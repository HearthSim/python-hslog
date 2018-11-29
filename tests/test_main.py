from datetime import datetime, time, timedelta
from io import StringIO

import pytest
from aniso8601 import parse_datetime
from hearthstone.enums import (
	CardType, ChoiceType, GameTag, OptionType,
	PlayReq, PlayState, PowerType, State, Step, Zone
)

from hslog import LogParser
from hslog.exceptions import ParsingError
from hslog.export import FriendlyPlayerExporter
from hslog.parser import parse_entity_id, parse_initial_tag

from .data import (
	CONTROLLER_CHANGE, EMPTY_GAME, FULL_ENTITY, INITIAL_GAME,
	INVALID_GAME, OPTIONS_WITH_ERRORS, UNROUNDABLE_TIMESTAMP
)


def test_create_empty_game():
	parser = LogParser()
	parser.read(StringIO(EMPTY_GAME))
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
	assert int(packet.players[0].entity) == game.players[0].id
	assert packet.players[0].player_id == game.players[0].player_id
	assert int(packet.players[1].entity) == game.players[1].id
	assert packet.players[1].player_id == game.players[1].player_id

	# All tags should be empty (we didn't pass any)
	assert not game.tags
	assert not game.players[0].tags
	assert not game.players[1].tags

	# Check some basic logic
	assert game.get_player(1) is game.players[0]
	assert game.get_player(2) is game.players[1]


def test_tag_value_parsing():
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


def test_game_initialization():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
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

	# Test that there should be no friendly player
	fpe = FriendlyPlayerExporter(packet_tree)
	friendly_player = fpe.export()
	assert not friendly_player


def test_timestamp_parsing():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
	parser.flush()

	assert parser.games[0].packets[0].ts == time(2, 59, 14, 608862)

	# Test with an initial datetime
	parser2 = LogParser()
	parser2._current_date = datetime(2015, 1, 1)
	parser2.read(StringIO(INITIAL_GAME))
	parser2.flush()

	assert parser2.games[0].packets[0].ts == datetime(2015, 1, 1, 2, 59, 14, 608862)

	# Same test, with timezone
	parser2 = LogParser()
	parser2._current_date = parse_datetime("2015-01-01T02:58:00+0200")
	parser2.read(StringIO(INITIAL_GAME))
	parser2.flush()

	ts = parser2.games[0].packets[0].ts
	assert ts.year == 2015
	assert ts.hour == 2
	assert ts.second == 14
	assert ts.tzinfo
	assert ts.utcoffset() == timedelta(hours=2)


def test_unroundable_timestamp():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
	parser.read(StringIO(UNROUNDABLE_TIMESTAMP))
	parser.flush()

	# Timestamp has to be truncated
	assert parser.games[0].packets[1].ts == time(14, 43, 59, 999999)


def test_info_outside_of_metadata():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
	parser.flush()

	info = u"D 02:59:14.6500380 GameState.DebugPrintPower() -             Info[0] = 99"
	parser.read(StringIO(info))
	parser.flush()


def test_empty_entity_in_options():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
	parser.flush()

	data = "target 0 entity="
	with pytest.raises(ParsingError):
		# This can happen, but the game is corrupt
		parser.handle_options(None, data)


def test_warn_level():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
	parser.flush()

	line = u"W 09:09:23.1428700 GameState.ReportStuck() - Stuck for 10s 89ms. {...}"
	parser.read(StringIO(line))
	parser.flush()


def test_empty_tasklist():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
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


def test_tag_change_unknown_entity_format():
	# Format changed in 15590
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
	parser.flush()

	entity_format = (
		"[name=UNKNOWN ENTITY [cardType=INVALID] id=24 zone=DECK zonePos=0 cardId= player=1]"
	)
	id = parse_entity_id(entity_format)
	assert id == 24

	data = "TAG_CHANGE Entity=%s tag=ZONE value=HAND" % (entity_format)
	packet = parser.handle_power(None, "TAG_CHANGE", data)
	assert packet.power_type == PowerType.TAG_CHANGE
	assert packet.entity == id
	assert packet.tag == GameTag.ZONE
	assert packet.value == Zone.HAND


def test_initial_deck_initial_controller():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
	parser.read(StringIO(FULL_ENTITY))
	parser.flush()
	packet_tree = parser.games[0]
	game = packet_tree.export().game

	assert len(list(game.players[0].initial_deck)) == 1
	assert len(list(game.players[1].initial_deck)) == 0

	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))
	parser.read(StringIO(FULL_ENTITY))
	parser.read(StringIO(CONTROLLER_CHANGE))
	parser.flush()
	packet_tree = parser.games[0]
	game = packet_tree.export().game

	assert len(list(game.players[0].initial_deck)) == 1
	assert len(list(game.players[1].initial_deck)) == 0


def test_invalid_game_one_player():
	parser = LogParser()
	with pytest.raises(ParsingError):
		parser.read(StringIO(INVALID_GAME))


def test_options_packet_with_errors():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))

	parser.read(StringIO(OPTIONS_WITH_ERRORS))
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


def test_options_no_option_packet():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))

	with pytest.raises(ParsingError):
		parser.handle_options(None, "option 0 type=END_TURN mainEntity=")


def test_suboptions_no_option_packet():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))

	with pytest.raises(ParsingError):
		parser.handle_options(None, "subOption 0 entity=1")


def test_error_unhandled_powtype():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))

	# This shouldn't raise an exception
	parser.read(StringIO(
		"D 02:13:03.1360001 GameState.DebugPrintPower() - "
		"ERROR: unhandled PowType RESET_GAME"
	))
	parser.flush()


def test_target_no_entity():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))

	parser.read(StringIO(
		"D 01:02:58.3254653 GameState.DebugPrintOptions() - id=2\n" # noqa
		"D 01:02:58.3254653 GameState.DebugPrintOptions() -   option 0 type=END_TURN mainEntity= error=INVALID errorParam=\n" # noqa
		"D 01:02:58.3254653 GameState.DebugPrintOptions() -   option 1 type=POWER mainEntity= error=NONE errorParam=\n" # noqa
		"D 01:02:58.3254653 GameState.DebugPrintOptions() -     target 0 entity= error=NONE errorParam=\n" # noqa
		"D 01:02:58.3254653 GameState.DebugPrintOptions() -     target 1 entity= error=NONE errorParam=\n" # noqa
	))
	parser.flush()

	packet_tree = parser.games[0]

	options_packet = packet_tree.packets[-1]
	option = options_packet.options[1]
	target = option.options[0]
	assert target.entity is None
	assert target.error is None
	assert target.error_param is None


def test_reset_game():
	parser = LogParser()
	parser.read(StringIO(INITIAL_GAME))

	# This shouldn't raise an exception
	parser.read(StringIO(
		"D 15:39:19.3190860 GameState.DebugPrintPower() - BLOCK_START BlockType=GAME_RESET Entity=[entityName=Temporal Loop id=17 zone=PLAY zonePos=0 cardId=GILA_900p player=1] EffectCardId= EffectIndex=-1 Target=0 SubOption=-1\n" # noqa
		"D 15:39:19.3190860 GameState.DebugPrintPower() -     RESET_GAME\n"
	))
	parser.flush()
