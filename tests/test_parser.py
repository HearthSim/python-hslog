from datetime import datetime, time, timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from aniso8601 import parse_datetime, parse_time
from hearthstone.enums import (
	CardType, ChoiceType, GameTag, OptionType,
	PlayReq, PlayState, PowerType, State, Step, Zone
)

from hslog import LogParser, packets
from hslog.exceptions import CorruptLogError, ParsingError
from hslog.parser import parse_initial_tag

from . import data


class TestLogParser:
	def test_create_empty_game(self):
		parser = LogParser()
		parser.read(StringIO(data.EMPTY_GAME))
		parser.flush()

		# Test resulting game/entities
		assert len(parser.games) == 1

		packet_tree = parser.games[0]
		game = packet_tree.export().game
		assert len(game._entities) == 3
		assert len(game.players) == 2
		assert game._entities[1] is game
		assert game._entities[1].id == 1
		assert game._entities[2] is game.players[0]
		assert game._entities[3] is game.players[1]
		assert game.initial_state == State.INVALID
		assert game.initial_step == Step.INVALID

		# Test player objects
		assert game.players[0].id == 2
		assert game.players[0].player_id == 1
		assert game.players[0].account_hi == 1
		assert game.players[0].account_lo == 0
		assert game.players[0].is_ai
		assert not game.players[0].name

		assert game.players[1].id == 3
		assert game.players[1].player_id == 2
		assert game.players[1].account_hi == 3
		assert game.players[1].account_lo == 2
		assert not game.players[1].is_ai
		assert not game.players[1].name

		# Test packet structure
		assert len(packet_tree.packets) == 1
		packet = packet_tree.packets[0]
		assert packet.power_type == PowerType.CREATE_GAME
		assert packet.entity == game.id == 1

		# Player packet objects are not the same as players
		assert packet.players[0].entity.entity_id == game.players[0].id
		assert packet.players[0].player_id == game.players[0].player_id
		assert packet.players[1].entity.entity_id == game.players[1].id
		assert packet.players[1].player_id == game.players[1].player_id

		# All tags should be empty (we didn't pass any)
		assert not game.tags
		assert not game.players[0].tags
		assert not game.players[1].tags

		# Check some basic logic
		assert game.get_player(1) is game.players[0]
		assert game.get_player(2) is game.players[1]

	def test_tag_value_parsing(self):
		tag, value = parse_initial_tag("tag=ZONE value=PLAY")
		assert tag == GameTag.ZONE
		assert value == Zone.PLAY

		tag, value = parse_initial_tag("tag=CARDTYPE value=PLAYER")
		assert tag == GameTag.CARDTYPE
		assert value == CardType.PLAYER

		tag, value = parse_initial_tag("tag=1 value=2")
		assert tag == 1
		assert value == 2

		tag, value = parse_initial_tag("tag=9999998 value=123")
		assert tag == 9999998
		assert value == 123

	def test_game_initialization(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.flush()

		assert len(parser.games) == 1
		packet_tree = parser.games[0]
		game = packet_tree.export().game
		assert len(game._entities) == 3
		assert len(game.players) == 2

		assert game.tags == {
			GameTag.TURN: 1,
			GameTag.ZONE: Zone.PLAY,
			GameTag.ENTITY_ID: 1,
			GameTag.NEXT_STEP: Step.BEGIN_MULLIGAN,
			GameTag.CARDTYPE: CardType.GAME,
			GameTag.STATE: State.RUNNING,
		}
		assert game.initial_state == State.RUNNING
		assert game.initial_step == Step.INVALID

		assert game.players[0].tags == {
			GameTag.PLAYSTATE: PlayState.PLAYING,
			GameTag.PLAYER_ID: 1,
			GameTag.TEAM_ID: 1,
			GameTag.ZONE: Zone.PLAY,
			GameTag.CONTROLLER: 1,
			GameTag.ENTITY_ID: 2,
			GameTag.CARDTYPE: CardType.PLAYER,
		}

		assert game.players[1].tags == {
			GameTag.PLAYSTATE: PlayState.PLAYING,
			GameTag.CURRENT_PLAYER: 1,
			GameTag.FIRST_PLAYER: 1,
			GameTag.PLAYER_ID: 2,
			GameTag.TEAM_ID: 2,
			GameTag.ZONE: Zone.PLAY,
			GameTag.CONTROLLER: 2,
			GameTag.ENTITY_ID: 3,
			GameTag.CARDTYPE: CardType.PLAYER,
		}

	def test_timestamp_parsing(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.flush()

		assert parser.games[0].packets[0].ts == time(2, 59, 14, 608862)

		# Test with an initial datetime
		parser2 = LogParser()
		parser2._current_date = datetime(2015, 1, 1)
		parser2.read(StringIO(data.INITIAL_GAME))
		parser2.flush()

		assert parser2.games[0].packets[0].ts == datetime(2015, 1, 1, 2, 59, 14, 608862)

		# Same test, with timezone
		parser2 = LogParser()
		parser2._current_date = parse_datetime("2015-01-01T02:58:00+0200")
		parser2.read(StringIO(data.INITIAL_GAME))
		parser2.flush()

		ts = parser2.games[0].packets[0].ts
		assert ts.year == 2015
		assert ts.hour == 2
		assert ts.second == 14
		assert ts.tzinfo
		assert ts.utcoffset() == timedelta(hours=2)

	def test_repeated_timestamps(self):
		parser = LogParser()
		parser._current_date = parse_datetime("2015-01-01T02:58:00+0200")

		parser.read(StringIO(data.INITIAL_GAME))

		with patch("hslog.parser.parse_time", wraps=parse_time) as spy:
			parser.read(StringIO(data.REPEATED_TIMESTAMP))
		spy.assert_called_once()  # The same repeated timestamp should only be parsed once

		ts1 = parser.games[0].packets[-1].ts
		ts2 = parser.games[0].packets[-2].ts
		assert ts1 == ts2

	def test_unroundable_timestamp(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.read(StringIO(data.UNROUNDABLE_TIMESTAMP))
		parser.flush()

		# Timestamp has to be truncated
		assert parser.games[0].packets[1].ts == time(14, 43, 59, 999999)

	def test_info_outside_of_metadata(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.flush()

		info = u"D 02:59:14.6500380 GameState.DebugPrintPower() -             Info[0] = 99"
		parser.read(StringIO(info))
		parser.flush()

	def test_empty_entity_in_options(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.flush()

		line = "target 0 entity="
		with pytest.raises(ParsingError):
			# This can happen, but the game is corrupt
			parser.handle_options(None, line)

	def test_warn_level(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.flush()

		line = u"W 09:09:23.1428700 GameState.ReportStuck() - Stuck for 10s 89ms. {...}"
		parser.read(StringIO(line))
		parser.flush()

	def test_error_level(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.flush()

		line = u"E 02:08:13.8318679 SubSpellController {...}"
		parser.read(StringIO(line))
		parser.flush()

	def test_empty_tasklist(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.flush()

		ts = datetime.now()
		msg = "id=4 Player=The Innkeeper TaskList=1 ChoiceType=GENERAL CountMin=1 CountMax=1"
		choices = parser.handle_entity_choices(ts, msg)
		assert choices
		assert choices.id == 4
		assert choices.player.name == "The Innkeeper"
		assert choices.tasklist == 1
		assert choices.type == ChoiceType.GENERAL
		assert choices.min == 1
		assert choices.max == 1

		# Test empty tasklist
		msg = "id=4 Player=The Innkeeper TaskList= ChoiceType=GENERAL CountMin=1 CountMax=1"
		choices = parser.handle_entity_choices(ts, msg)
		assert choices.tasklist is None

	def test_tag_change_unknown_entity_format(self):
		# Format changed in 15590
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.flush()

		entity_format = (
			"[name=UNKNOWN ENTITY [cardType=INVALID] id=24 zone=DECK zonePos=0 cardId= player=1]"
		)
		id = parser.parse_entity_id(entity_format)
		assert id == 24

		line = "TAG_CHANGE Entity=%s tag=ZONE value=HAND" % (entity_format)
		packet = parser.handle_power(None, "TAG_CHANGE", line)
		assert packet.power_type == PowerType.TAG_CHANGE
		assert packet.entity == id
		assert packet.tag == GameTag.ZONE
		assert packet.value == Zone.HAND

	def test_initial_deck_initial_controller(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.read(StringIO(data.FULL_ENTITY))
		parser.flush()
		packet_tree = parser.games[0]
		game = packet_tree.export().game

		assert len(list(game.players[0].initial_deck)) == 1
		assert len(list(game.players[1].initial_deck)) == 0

		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.read(StringIO(data.FULL_ENTITY))
		parser.read(StringIO(data.CONTROLLER_CHANGE))
		parser.flush()
		packet_tree = parser.games[0]
		game = packet_tree.export().game

		assert len(list(game.players[0].initial_deck)) == 1
		assert len(list(game.players[1].initial_deck)) == 0

	def test_invalid_game_one_player(self):
		parser = LogParser()
		with pytest.raises(ParsingError):
			parser.read(StringIO(data.INVALID_GAME))

	def test_options_packet_with_errors(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		parser.read(StringIO(data.OPTIONS_WITH_ERRORS))
		parser.flush()
		packet_tree = parser.games[0]

		options_packet = packet_tree.packets[-1]

		op0 = options_packet.options[0]
		assert op0.id == 0
		assert op0.type == OptionType.END_TURN
		assert op0.entity is None
		assert op0.error == PlayReq.INVALID
		assert op0.error_param is None

		op1 = options_packet.options[1]
		assert op1.id == 1
		assert op1.type == OptionType.POWER
		assert op1.entity == 33
		assert op1.error is None
		assert op1.error_param is None

		assert len(op1.options) == 12
		target = op1.options[11]
		assert target.id == 11
		assert target.entity == 37
		assert target.error == PlayReq.REQ_TARGET_MAX_ATTACK
		assert target.error_param == 3

	def test_options_no_option_packet(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		with pytest.raises(ParsingError):
			parser.handle_options(None, "option 0 type=END_TURN mainEntity=")

	def test_suboptions_no_option_packet(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		with pytest.raises(ParsingError):
			parser.handle_options(None, "subOption 0 entity=1")

	def test_error_unhandled_powtype(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		# This shouldn't raise an exception
		parser.read(StringIO(
			"D 02:13:03.1360001 GameState.DebugPrintPower() - "
			"ERROR: unhandled PowType RESET_GAME"
		))
		parser.flush()

	def test_target_no_entity(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		parser.read(StringIO(
			"D 01:02:58.3254653 GameState.DebugPrintOptions() - id=2\n"  # noqa
			"D 01:02:58.3254653 GameState.DebugPrintOptions() -   option 0 type=END_TURN mainEntity= error=INVALID errorParam=\n"  # noqa
			"D 01:02:58.3254653 GameState.DebugPrintOptions() -   option 1 type=POWER mainEntity= error=NONE errorParam=\n"  # noqa
			"D 01:02:58.3254653 GameState.DebugPrintOptions() -     target 0 entity= error=NONE errorParam=\n"  # noqa
			"D 01:02:58.3254653 GameState.DebugPrintOptions() -     target 1 entity= error=NONE errorParam=\n"  # noqa
		))
		parser.flush()

		packet_tree = parser.games[0]

		options_packet = packet_tree.packets[-1]
		option = options_packet.options[1]
		target = option.options[0]
		assert target.entity is None
		assert target.error is None
		assert target.error_param is None

	def test_reset_game(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		# This shouldn't raise an exception
		parser.read(StringIO(
			"D 15:39:19.3190860 GameState.DebugPrintPower() - BLOCK_START BlockType=GAME_RESET Entity=[entityName=Temporal Loop id=17 zone=PLAY zonePos=0 cardId=GILA_900p player=1] EffectCardId= EffectIndex=-1 Target=0 SubOption=-1\n"  # noqa
			"D 15:39:19.3190860 GameState.DebugPrintPower() -     RESET_GAME\n"
		))
		parser.flush()

	def test_sub_spell(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		parser.read(StringIO(data.SUB_SPELL_BLOCK))
		parser.flush()

		packet_tree = parser.games[0]
		play_block = packet_tree.packets[-1]
		power_block = play_block.packets[0]
		assert len(power_block.packets) == 1
		sub_spell_packet = power_block.packets[0]

		assert sub_spell_packet.spell_prefab_guid == (
			"CannonBarrage_Missile_FX:e26b4681614e0964aa8ef7afebc560d1"
		)
		assert sub_spell_packet.source == 59
		assert sub_spell_packet.target_count == 1
		assert sub_spell_packet.targets == [41]

	def test_sub_spell_battlegrounds(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		parser.read(StringIO(data.BGS_SUB_SPELL_BLOCK))
		parser.flush()

		packet_tree = parser.games[0]
		play_block = packet_tree.packets[-1]
		power_block = play_block.packets[0]
		assert len(power_block.packets) == 1
		sub_spell_packet = power_block.packets[0]

		assert sub_spell_packet.spell_prefab_guid == (
			"Bacon_FreezeMinions_AE_Super.prefab:49de73d8b72602f47994a795a78f050d"
		)
		assert sub_spell_packet.source == 0
		assert sub_spell_packet.target_count == 0
		assert sub_spell_packet.targets == []

	def test_sub_spell_mercenaries(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		parser.read(StringIO(data.MERCENARIES_SUB_SPELL_BLOCK))
		parser.flush()

		packet_tree = parser.games[0]
		power_block = packet_tree.packets[-1]
		assert len(power_block.packets) == 1
		sub_spell_packet = power_block.packets[0]

		assert sub_spell_packet.spell_prefab_guid == (
			"ReuseFX_Missile_Object)Bomb_Dynamite_Super:63de8756b8c2c704ba59d9a31ed4e820"
		)
		assert sub_spell_packet.source == 34
		assert sub_spell_packet.target_count == 1
		assert sub_spell_packet.targets == [37]

	def test_options_missing_block_end(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		parser.read(StringIO(
			"D 09:01:05.7959635 GameState.DebugPrintPower() - BLOCK_START BlockType=ATTACK Entity=[entityName=Rat Pack id=2974 zone=PLAY zonePos=2 cardId=CFM_316 player=3] EffectCardId= EffectIndex=1 Target=0 SubOption=-1 \n"  # noqa
			"D 09:01:05.7959635 GameState.DebugPrintPower() -     BLOCK_START BlockType=TRIGGER Entity=[entityName=3ofKindCheckPlayerEnchant id=3319 zone=PLAY zonePos=0 cardId=TB_BaconShop_3ofKindChecke player=3] EffectCardId= EffectIndex=-1 Target=0 SubOption=-1 TriggerKeyword=0\n"  # noqa
			"D 09:01:05.7959635 GameState.DebugPrintPower() -     BLOCK_END\n"  # noqa
			"D 09:01:05.7959635 GameState.DebugPrintPower() -     TAG_CHANGE Entity=BehEh#1355 tag=NUM_OPTIONS_PLAYED_THIS_TURN value=15 \n"  # noqa
			"D 09:01:05.8620235 GameState.DebugPrintOptions() - id=76\n"  # noqa
			"D 09:01:05.8620235 GameState.DebugPrintOptions() -   option 0 type=END_TURN mainEntity= error=INVALID errorParam=\n"  # noqa
		))
		parser.flush()

		packet_tree = parser.games[0]

		block_without_end = packet_tree.packets[1]
		assert isinstance(block_without_end, packets.Block)
		assert block_without_end.ended

		options_packet = packet_tree.packets[-1]
		assert isinstance(options_packet, packets.Options)

	def test_cached_tag_for_dormant_change(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.read(StringIO(data.CACHED_TAG_FOR_DORMANT_CHANGE))
		parser.flush()

		packet_tree = parser.games[0]

		cached_tag_packet = packet_tree.packets[1]

		assert cached_tag_packet.entity == 417
		assert cached_tag_packet.tag == GameTag.DEATHRATTLE
		assert cached_tag_packet.value == 1

	def test_cached_tag_for_dormant_change_entity_id_only(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.read(StringIO(data.CACHED_TAG_FOR_DORMANT_CHANGE_SHORT_ENTITY))
		parser.flush()

		packet_tree = parser.games[0]

		cached_tag_packet = packet_tree.packets[1]

		assert cached_tag_packet.entity == 593
		assert cached_tag_packet.tag == GameTag.DEATHRATTLE
		assert cached_tag_packet.value == 1

	def test_vo_spell_only(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.read(StringIO(data.VO_SPELL))
		parser.flush()

		packet_tree = parser.games[0]

		vo_spell_packet = packet_tree.packets[1]

		assert vo_spell_packet.brguid == (
			"VO_BTA_BOSS_07h2_Female_NightElf_Mission_Fight_07_PlayerStart_01.prefab:616c9e5" +
			"7bb7fce54684e26be50462d17"
		)
		assert vo_spell_packet.vospguid == ""
		assert vo_spell_packet.blocking is True
		assert vo_spell_packet.delayms == 1000

	def test_shuffle_deck_only(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))
		parser.read(StringIO(data.SHUFFLE_DECK))
		parser.flush()

		packet_tree = parser.games[0]

		shuffle_deck_packet = packet_tree.packets[1]

		assert shuffle_deck_packet.player_id == 2

	def test_nul_byte(self):
		parser = LogParser()
		parser.read(StringIO(data.INITIAL_GAME))

		with pytest.raises(
			CorruptLogError,
			match=r"Log contains contains a NUL \(0x00\) byte"
		):
			parser.read(StringIO(data.CORRUPT_SHOW_ENTITY))
