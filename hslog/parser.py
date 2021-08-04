import logging
from datetime import datetime, timedelta

from aniso8601 import parse_time
from hearthstone.enums import (
	BlockType, ChoiceType, FormatType, GameTag, GameType,
	MetaDataType, Mulligan, OptionType, PlayReq, PowerType
)

from . import packets, tokens
from .exceptions import ParsingError, RegexParsingError
from .player import LazyPlayer, PlayerManager
from .utils import parse_enum, parse_tag


def parse_initial_tag(data):
	"""
	Parse \a data, a line formatted as tag=FOO value=BAR
	Returns the values as int.
	"""
	sre = tokens.TAG_VALUE_RE.match(data)
	if not sre:
		raise RegexParsingError(data)
	tag, value = sre.groups()
	return parse_tag(tag, value)


def clean_option_errors(error, error_param):
	"""
	As of 8.0.0.18336, all option packets are accompanied by an error and an
	errorParam argument.
	This function turns both into their respective types.
	"""

	if error == "NONE":
		error = None
	else:
		error = parse_enum(PlayReq, error)

	if not error_param:
		error_param = None
	else:
		error_param = int(error_param)

	return error, error_param


class PowerHandler:
	def __init__(self):
		super(PowerHandler, self).__init__()
		self.current_block = None
		self._metadata_node = None
		self._packets = None
		self._creating_game = False
		self.game_meta = {}
		self.unknown_human_player_count = 0

	def _check_for_mulligan_hack(self, ts, tag, value):
		# Old game logs didn't handle asynchronous mulligans properly.
		# If we're missing an ACTION_END packet after the mulligan SendChoices,
		# we just close it out manually.
		if tag == GameTag.MULLIGAN_STATE and value == Mulligan.DEALING:
			assert self.current_block
			if isinstance(self.current_block, packets.Block):
				logging.warning("[%s] Broken mulligan nesting. Working around...", ts)
				self.block_end(ts)

	def find_callback(self, method):
		if method == self.parse_method("DebugPrintPower"):
			return self.handle_data
		elif method == self.parse_method("DebugPrintGame"):
			return self.handle_game

	def handle_game(self, ts, data):
		if data.startswith("PlayerID="):
			sre = tokens.GAME_PLAYER_META.match(data)
			if not sre:
				raise RegexParsingError(data)
			player_id, player_name = sre.groups()
			player_id = int(player_id)

			if player_name == tokens.UNKNOWN_HUMAN_PLAYER:
				self.unknown_human_player_count += 1

			self._packets.manager.register_player_name_by_player_id(player_name, player_id)
		else:
			key, value = data.split("=")
			key = key.strip()
			value = value.strip()
			if key == "GameType":
				value = parse_enum(GameType, value)
			elif key == "FormatType":
				value = parse_enum(FormatType, value)
			else:
				value = int(value)

			self.game_meta[key] = value

	def handle_data(self, ts, data):
		opcode = data.split()[0]

		if opcode == "ERROR:":
			# Line error... skip
			return

		if opcode in PowerType.__members__:
			return self.handle_power(ts, opcode, data)

		if opcode == "GameEntity":
			self.flush()
			self._creating_game = True
			sre = tokens.GAME_ENTITY_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			self.register_game(ts, *sre.groups())
		elif opcode == "Player":
			self.flush()
			sre = tokens.PLAYER_ENTITY_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			self.register_player(ts, *sre.groups())
		elif opcode.startswith("tag="):
			tag, value = parse_initial_tag(data)
			self._entity_packet.tags.append((tag, value))
			if tag == GameTag.CONTROLLER:
				# We need to know entity controllers for player name registration
				self._packets.manager.register_controller(self._entity_packet.entity, value)
		elif opcode.startswith("Info["):
			if not self._metadata_node:
				logging.warning("[%s] Metadata Info outside of META_DATA: %r", ts, data)
				return
			sre = tokens.METADATA_INFO_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			entity = self.parse_entity_or_player(entity)
			self._metadata_node.info.append(entity)
		elif opcode == "Source":
			sre = tokens.SUB_SPELL_START_SOURCE_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			entity, = sre.groups()
			entity = self.parse_entity_or_player(entity)
			if not isinstance(self.current_block, packets.SubSpell):
				logging.warning("[%s] SubSpell Source outside of SUB_SPELL: %r", ts, data)
				return
			self.current_block.source = entity
		elif opcode.startswith("Targets["):
			sre = tokens.SUB_SPELL_START_TARGETS_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			entity = self.parse_entity_or_player(entity)
			if not isinstance(self.current_block, packets.SubSpell):
				logging.warning("[%s] SubSpell Target outside of SUB_SPELL: %r", ts, data)
				return
			self.current_block.targets.append(entity)
		else:
			raise NotImplementedError(data)

	def flush(self):
		super(PowerHandler, self).flush()
		if self._metadata_node:
			self._metadata_node = None

	def handle_power(self, ts, opcode, data):
		self.flush()

		if opcode == "CREATE_GAME":
			regex, callback = tokens.CREATE_GAME_RE, self.create_game
		elif opcode in ("ACTION_START", "BLOCK_START"):
			index = None
			effectid, effectindex = None, None
			suboption, trigger_keyword = None, None
			if " SubOption=" in data:
				if " TriggerKeyword=" in data:
					sre = tokens.BLOCK_START_20457_TRIGGER_KEYWORD_RE.match(data)
					if sre is None:
						raise RegexParsingError(data)
					type, entity, effectid, effectindex, target, suboption, trigger_keyword = sre.groups()
				else:
					sre = tokens.BLOCK_START_20457_RE.match(data)
					if sre is None:
						raise RegexParsingError(data)
					type, entity, effectid, effectindex, target, suboption = sre.groups()
			else:
				if opcode == "ACTION_START":
					sre = tokens.ACTION_START_RE.match(data)
				else:
					sre = tokens.BLOCK_START_12051_RE.match(data)

				if sre is None:
					sre = tokens.ACTION_START_OLD_RE.match(data)
					if not sre:
						raise RegexParsingError(data)
					entity, type, index, target = sre.groups()
				else:
					type, entity, effectid, effectindex, target = sre.groups()

			self.block_start(
				ts, entity, type, index, effectid, effectindex, target, suboption, trigger_keyword
			)
			return
		elif opcode in ("ACTION_END", "BLOCK_END"):
			regex, callback = tokens.BLOCK_END_RE, self.block_end
		elif opcode == "FULL_ENTITY":
			if data.startswith("FULL_ENTITY - Updating"):
				regex, callback = tokens.FULL_ENTITY_UPDATE_RE, self.full_entity_update
			else:
				regex, callback = tokens.FULL_ENTITY_CREATE_RE, self.full_entity
		elif opcode == "SHOW_ENTITY":
			regex, callback = tokens.SHOW_ENTITY_RE, self.show_entity
		elif opcode == "HIDE_ENTITY":
			regex, callback = tokens.HIDE_ENTITY_RE, self.hide_entity
		elif opcode == "CHANGE_ENTITY":
			regex, callback = tokens.CHANGE_ENTITY_RE, self.change_entity
		elif opcode == "TAG_CHANGE":
			regex, callback = tokens.TAG_CHANGE_RE, self.tag_change
		elif opcode == "META_DATA":
			regex, callback = tokens.META_DATA_RE, self.meta_data
		elif opcode == "RESET_GAME":
			regex, callback = tokens.RESET_GAME_RE, self.reset_game
		elif opcode == "SUB_SPELL_START":
			regex, callback = tokens.SUB_SPELL_START_RE, self.sub_spell_start
		elif opcode == "SUB_SPELL_END":
			regex, callback = tokens.SUB_SPELL_END_RE, self.sub_spell_end
		elif opcode == "CACHED_TAG_FOR_DORMANT_CHANGE":
			regex, callback = (
				tokens.CACHED_TAG_FOR_DORMANT_CHANGE_RE,
				self.cached_tag_for_dormant_change
			)
		elif opcode == "VO_SPELL":
			regex, callback = tokens.VO_SPELL_RE, self.vo_spell
		elif opcode == "SHUFFLE_DECK":
			regex, callback = tokens.SHUFFLE_DECK_RE, self.shuffle_deck
		else:
			raise NotImplementedError(data)

		sre = regex.match(data)
		if not sre:
			logging.warning("[%s] Could not correctly parse %r", ts, data)
			return
		return callback(ts, *sre.groups())

	def new_packet_tree(self, ts):
		self._packets = packets.PacketTree(ts)
		self._packets.spectator_mode = self.spectator_mode
		self._packets.manager = PlayerManager()
		self.current_block = self._packets
		self.games.append(self._packets)
		return self._packets

	# Messages
	def create_game(self, ts):
		self.new_packet_tree(ts)

	def block_start(
		self, ts, entity, type, index, effectid, effectindex, target, suboption, trigger_keyword
	):
		id = self.parse_entity_or_player(entity)
		type = parse_enum(BlockType, type)
		if index is not None:
			index = int(index)
		target = self.parse_entity_or_player(target)
		if suboption is not None:
			suboption = int(suboption)
		if trigger_keyword is not None:
			trigger_keyword = parse_enum(GameTag, trigger_keyword)

		block = packets.Block(
			ts, id, type, index, effectid, effectindex, target, suboption, trigger_keyword
		)
		block.parent = self.current_block
		self.register_packet(block)
		self.current_block = block
		return block

	def block_end(self, ts):
		if not self.current_block.parent:
			logging.warning("[%s] Orphaned BLOCK_END detected", ts)
			return self.current_block
		self.current_block.end()
		block = self.current_block
		self.current_block = self.current_block.parent
		return block

	def full_entity(self, ts, id, card_id):
		id = int(id)
		self._entity_packet = packets.FullEntity(ts, id, card_id)
		self.register_packet(self._entity_packet)

		if self._creating_game:
			# First packet after create game should always be a FULL_ENTITY
			self._creating_game = False

			# Check if we got an abnormal amount of players
			player_count = len(self._game_packet.players)
			if player_count < 2:
				msg = "Expected at least 2 players before the first entity, got %r"
				raise ParsingError(msg % (player_count))

		return self._entity_packet

	def full_entity_update(self, ts, entity, card_id):
		id = self.parse_entity_id(entity)
		return self.full_entity(ts, id, card_id)

	def show_entity(self, ts, entity, card_id):
		id = self.parse_entity_id(entity)
		self._entity_packet = packets.ShowEntity(ts, id, card_id)
		self.register_packet(self._entity_packet)
		return self._entity_packet

	def hide_entity(self, ts, entity, tag, value):
		id = self.parse_entity_id(entity)
		tag, value = parse_tag(tag, value)
		if tag != GameTag.ZONE:
			raise ParsingError("HIDE_ENTITY got non-zone tag (%r)" % (tag))
		packet = packets.HideEntity(ts, id, value)
		self.register_packet(packet)
		return packet

	def change_entity(self, ts, entity, card_id):
		id = self.parse_entity_or_player(entity)
		self._entity_packet = packets.ChangeEntity(ts, id, card_id)
		self.register_packet(self._entity_packet)
		return self._entity_packet

	def meta_data(self, ts, meta, data, info_count):
		meta = parse_enum(MetaDataType, meta)
		if meta == MetaDataType.JOUST:
			data = self.parse_entity_id(data)
		count = int(info_count)
		self._metadata_node = packets.MetaData(ts, meta, data, count)
		self.register_packet(self._metadata_node)
		return self._metadata_node

	def tag_change(self, ts, e, tag, value, def_change):
		id = self.parse_entity_or_player(e)
		tag, value = parse_tag(tag, value)
		self._check_for_mulligan_hack(ts, tag, value)

		if isinstance(id, LazyPlayer):
			id = self._packets.manager.register_player_name_on_tag_change(id, tag, value)

		has_change_def = def_change == tokens.DEF_CHANGE
		packet = packets.TagChange(ts, id, tag, value, has_change_def)
		self.register_packet(packet)
		return packet

	def reset_game(self, ts):
		packet = packets.ResetGame(ts)
		self.register_packet(packet)
		return packet

	def sub_spell_start(self, ts, spell_prefab_guid, source, target_count):
		id = int(source)
		target_count = int(target_count)

		sub_spell = packets.SubSpell(ts, spell_prefab_guid, id, target_count)
		sub_spell.parent = self.current_block
		self.register_packet(sub_spell)
		self.current_block = sub_spell
		return sub_spell

	def sub_spell_end(self, ts):
		if not self.current_block.parent:
			logging.warning("[%s] Orphaned SUB_SPELL_END detected", ts)
			return self.current_block
		self.current_block.end()
		sub_spell = self.current_block
		self.current_block = self.current_block.parent
		return sub_spell

	def cached_tag_for_dormant_change(self, ts, e, tag, value):
		id = self.parse_entity_id(e)
		tag, value = parse_tag(tag, value)

		packet = packets.CachedTagForDormantChange(ts, id, tag, value)
		self.register_packet(packet)
		return packet

	def vo_spell(self, ts, brguid, vospguid, blocking, delayms):
		packet = packets.VOSpell(ts, brguid, vospguid, blocking == "True", int(delayms))
		self.register_packet(packet)
		return packet

	def shuffle_deck(self, ts, player_id):
		packet = packets.ShuffleDeck(ts, int(player_id))
		self.register_packet(packet)
		return packet


class OptionsHandler:
	def __init__(self):
		super(OptionsHandler, self).__init__()
		self._option_packet = None
		self._options_packet = None
		self._suboption_packet = None

	def find_callback(self, method):
		if method == self.parse_method("SendOption"):
			return self.handle_send_option
		elif method == self.parse_method("DebugPrintOptions"):
			return self.handle_options

	def _parse_option_packet(self, ts, data):
		if " errorParam=" in data:
			sre = tokens.OPTIONS_OPTION_ERROR_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			optype, id, type, entity, error, error_param = sre.groups()
			error, error_param = clean_option_errors(error, error_param)
		else:
			sre = tokens.OPTIONS_OPTION_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			optype, id, type, entity = sre.groups()
			error, error_param = None, None

		id = int(id)
		type = parse_enum(OptionType, type)
		if entity:
			entity = self.parse_entity_or_player(entity)
		self._option_packet = packets.Option(ts, entity, id, type, optype, error, error_param)
		if not self._options_packet:
			raise ParsingError("Option without a parent option group: %r" % (data))

		self.register_packet(self._option_packet, node=self._options_packet.options)
		self._suboption_packet = None

		return self._option_packet

	def _parse_suboption_packet(self, ts, data):
		if " errorParam=" in data:
			sre = tokens.OPTIONS_SUBOPTION_ERROR_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			optype, id, entity, error, error_param = sre.groups()
			error, error_param = clean_option_errors(error, error_param)
		else:
			sre = tokens.OPTIONS_SUBOPTION_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			optype, id, entity = sre.groups()
			error, error_param = None, None

		id = int(id)
		if entity:
			entity = self.parse_entity_or_player(entity)

		packet = packets.Option(ts, entity, id, None, optype, error, error_param)
		if optype == "subOption":
			self._suboption_packet = packet
			node = self._option_packet
		elif optype == "target":
			node = self._suboption_packet or self._option_packet

		if not node:
			raise ParsingError("SubOption / target without a matching option: %r" % (data))

		self.register_packet(packet, node=node.options)

		return packet

	def _check_for_options_hack(self, ts):
		# Battlegrounds games tend to omit the BLOCK_END just before options start. As
		# options will always be on the top level, we can safely close any remaining block
		# that is open at this time.
		if isinstance(self.current_block, packets.Block):
			logging.warning("[%s] Broken option nesting. Working around...", ts)
			self.block_end(ts)
			assert not isinstance(self.current_block, packets.Block)

	def handle_options(self, ts, data):
		self._check_for_options_hack(ts)
		if data.startswith("id="):
			sre = tokens.OPTIONS_ENTITY_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			id, = sre.groups()
			id = int(id)
			self._options_packet = packets.Options(ts, id)
			self.current_block.packets.append(self._options_packet)
		elif data.startswith("option "):
			return self._parse_option_packet(ts, data)
		elif data.startswith(("subOption ", "target ")):
			return self._parse_suboption_packet(ts, data)

	def handle_send_option(self, ts, data):
		if data.startswith("selectedOption="):
			sre = tokens.SEND_OPTION_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			option, suboption, target, position = sre.groups()
			packet = packets.SendOption(ts, int(option), int(suboption), int(target), int(position))
			self.register_packet(packet)
			return packet
		raise NotImplementedError("Unhandled send option: %r" % (data))


class ChoicesHandler:
	def __init__(self):
		super(ChoicesHandler, self).__init__()
		self._choice_packet = None
		self._chosen_packet = None
		self._send_choice_packet = None

	def find_callback(self, method):
		if method == self.parse_method("DebugPrintEntityChoices"):
			return self.handle_entity_choices
		elif method == self.parse_method("DebugPrintChoices"):
			return self.handle_entity_choices_old
		elif method == self.parse_method("SendChoices"):
			return self.handle_send_choices
		elif method == self.parse_method("DebugPrintEntitiesChosen"):
			return self.handle_entities_chosen

	def flush(self):
		if self._choice_packet:
			if self._choice_packet.type == ChoiceType.MULLIGAN:
				self._packets.manager.register_player_name_mulligan(self._choice_packet)
			self._choice_packet = None
		if self._chosen_packet:
			self._chosen_packet = None
		if self._send_choice_packet:
			self._send_choice_packet = None

	def handle_entity_choices_old(self, ts, data):
		if data.startswith("id="):
			sre = tokens.CHOICES_CHOICE_OLD_1_RE.match(data)
			if sre:
				self.register_choices_old_1(ts, *sre.groups())
			else:
				sre = tokens.CHOICES_CHOICE_OLD_2_RE.match(data)
				if not sre:
					raise RegexParsingError(data)
				self.register_choices_old_2(ts, *sre.groups())
		else:
			return self.handle_entity_choices(ts, data)

	def handle_entity_choices(self, ts, data):
		if data.startswith("id="):
			sre = tokens.CHOICES_CHOICE_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			return self.register_choices(ts, *sre.groups())
		elif data.startswith("Source="):
			sre = tokens.CHOICES_SOURCE_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			entity, = sre.groups()
			id = self.parse_entity_or_player(entity)
			if not self._choice_packet:
				raise ParsingError("Source Choice Entity outside of choie packet: %r" % (data))
			self._choice_packet.source = id
			return id
		elif data.startswith("Entities["):
			sre = tokens.CHOICES_ENTITIES_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			id = self.parse_entity_or_player(entity)
			if not id:
				raise ParsingError("Missing choice entity %r (%r)" % (id, entity))
			if not self._choice_packet:
				raise ParsingError("Choice Entity outside of choice packet: %r" % (data))
			self._choice_packet.choices.append(id)
			return id
		raise NotImplementedError("Unhandled entity choice: %r" % (data))

	def _register_choices(self, ts, id, player, tasklist, type, min, max):
		id = int(id)
		type = parse_enum(ChoiceType, type)
		min, max = int(min), int(max)
		self._choice_packet = packets.Choices(ts, player, id, tasklist, type, min, max)
		self.register_packet(self._choice_packet)
		return self._choice_packet

	def register_choices_old_1(self, ts, id, type):
		player = None
		# XXX: We don't have a player here for old games.
		# Is it safe to assume CURRENT_PLAYER?
		tasklist = None
		min, max = 0, 0
		return self._register_choices(ts, id, player, tasklist, type, min, max)

	def register_choices_old_2(self, ts, id, player_id, type, min, max):
		player_id = int(player_id)
		player = self._packets.manager._players_by_player_id[player_id]
		tasklist = None
		return self._register_choices(ts, id, player, tasklist, type, min, max)

	def register_choices(self, ts, id, player, tasklist, type, min, max):
		player = self.parse_entity_or_player(player)
		if tasklist is not None:
			# Sometimes tasklist is empty
			tasklist = int(tasklist)
		return self._register_choices(ts, id, player, tasklist, type, min, max)

	def handle_send_choices(self, ts, data):
		if data.startswith("id="):
			sre = tokens.SEND_CHOICES_CHOICE_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			id, type = sre.groups()
			id = int(id)
			type = parse_enum(ChoiceType, type)
			self._send_choice_packet = packets.SendChoices(ts, id, type)
			self.register_packet(self._send_choice_packet)
			return self._send_choice_packet
		elif data.startswith("m_chosenEntities"):
			sre = tokens.SEND_CHOICES_ENTITIES_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			id = self.parse_entity_or_player(entity)
			if not id:
				raise ParsingError("Missing chosen entity %r (%r)" % (id, entity))
			if not self._send_choice_packet:
				raise ParsingError("Chosen Entity outside of choice packet: %r" % (data))
			self._send_choice_packet.choices.append(id)
			return id
		raise NotImplementedError("Unhandled send choice: %r" % (data))

	def handle_entities_chosen(self, ts, data):
		if data.startswith("id="):
			sre = tokens.ENTITIES_CHOSEN_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			id, player, count = sre.groups()
			id = int(id)
			player = self.parse_entity_or_player(player)
			if isinstance(player, LazyPlayer):
				player.id = id
				self._packets.manager.register_player_name_by_player_id(
					player.name,
					player.id
				)
			self._chosen_packet_count = int(count)
			self._chosen_packet = packets.ChosenEntities(ts, player, id)
			self.register_packet(self._chosen_packet)
			return self._chosen_packet
		elif data.startswith("Entities["):
			sre = tokens.ENTITIES_CHOSEN_ENTITIES_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			id = self.parse_entity_or_player(entity)
			if not id:
				raise ParsingError("Missing entity chosen %r (%r)" % (id, entity))
			if not self._chosen_packet:
				raise ParsingError("Entity Chosen outside of choice packet: %r" % (data))
			self._chosen_packet.choices.append(id)
			if len(self._chosen_packet.choices) > self._chosen_packet_count:
				raise ParsingError("Too many choices (expected %r)" % (self._chosen_packet_count))
			return id
		raise NotImplementedError("Unhandled entities chosen: %r" % (data))


class SpectatorModeHandler:
	def __init__(self):
		super(SpectatorModeHandler, self).__init__()
		self.spectating_first_player = False
		self.spectating_second_player = False

	@property
	def spectator_mode(self):
		return self.spectating_first_player or self.spectating_second_player

	def set_spectating(self, first, second=None):
		self.spectating_first_player = first
		if second is not None:
			self.spectating_second_player = second

	def process_spectator_mode(self, line):
		if line == tokens.SPECTATOR_MODE_BEGIN_GAME:
			self.set_spectating(True)
		elif line == tokens.SPECTATOR_MODE_BEGIN_FIRST:
			self.set_spectating(True, False)
		elif line == tokens.SPECTATOR_MODE_BEGIN_SECOND:
			self.set_spectating(True, True)
		elif line == tokens.SPECTATOR_MODE_END_MODE:
			self.set_spectating(False, False)
		elif line == tokens.SPECTATOR_MODE_END_GAME:
			self.set_spectating(False, False)
		else:
			raise NotImplementedError("Unhandled spectator mode: %r" % (line))


class LogParser(
	PowerHandler, ChoicesHandler, OptionsHandler, SpectatorModeHandler
):
	def __init__(self):
		super(LogParser, self).__init__()
		self.games = []
		self.line_regex = tokens.POWERLOG_LINE_RE
		self._game_state_processor = "GameState"
		self._current_date = None
		self._synced_timestamp = False
		self._last_ts = None

	def parse_timestamp(self, ts, method):
		if self._last_ts is not None and self._last_ts[0] == ts:
			return self._last_ts[1]

		ret = parse_time(ts)

		if not self._synced_timestamp:
			# The first timestamp we parse requires syncing the time
			# (in case _current_date is greater than the start date)
			if self._current_date is not None:
				self._current_date = self._current_date.replace(
					hour=ret.hour,
					minute=ret.minute,
					second=ret.second,
					microsecond=ret.microsecond,
				)
			# Only do it once per parse tree
			self._synced_timestamp = True

		# Logs don't have dates :(
		if self._current_date is None:
			self._last_ts = (ts, ret)
			# No starting date is available. Return just the time.
			return ret

		ret = datetime.combine(self._current_date, ret)
		ret = ret.replace(tzinfo=self._current_date.tzinfo)
		if ret < self._current_date:
			# If the new date falls before the last saved date, that
			# means we rolled over and need to increment the day by 1.
			ret += timedelta(days=1)
		self._current_date = ret
		self._last_ts = (ts, ret)
		return ret

	def read(self, fp):
		for line in fp:
			self.read_line(line)

	def read_line(self, line):
		sre = tokens.TIMESTAMP_RE.match(line)
		if not sre:
			raise RegexParsingError(line)
		level, ts, line = sre.groups()
		if line.startswith(tokens.SPECTATOR_MODE_TOKEN):
			line = line.replace(tokens.SPECTATOR_MODE_TOKEN, "").strip()
			return self.process_spectator_mode(line)

		sre = self.line_regex.match(line)
		if not sre:
			return
		method, msg = sre.groups()
		msg = msg.strip()
		if not self.current_block and "CREATE_GAME" not in msg:
			# Ignore messages before the first CREATE_GAME packet
			return

		for handler in PowerHandler, ChoicesHandler, OptionsHandler:
			callback = handler.find_callback(self, method)
			if callback:
				ts = self.parse_timestamp(ts, method)
				return callback(ts, msg)

	def register_packet(self, packet, node=None):
		if node is None:
			node = self.current_block.packets
		node.append(packet)
		self._packets._packet_counter += 1
		packet.packet_id = self._packets._packet_counter

	def parse_entity_id(self, entity):
		if entity.isdigit():
			return int(entity)

		if entity == tokens.GAME_ENTITY:
			return int(self._game_packet.entity)

		sre = tokens.ENTITY_RE.match(entity)
		if sre:
			id = sre.groups()[0]
			return int(id)

	def parse_entity_or_player(self, entity):
		if entity == "-1":
			return

		id = self.parse_entity_id(entity)
		if id is None:
			# Only case where an id is None is if it's a Player name
			id = self._packets.manager.get_player_by_name(entity)
		return id

	def parse_method(self, m):
		return "%s.%s" % (self._game_state_processor, m)

	def register_game(self, ts, id):
		id = int(id)
		# Use the timestamp from CREATE_GAME because it's earlier
		ts = self._packets.ts
		self._game_packet = self._entity_packet = packets.CreateGame(ts, id)
		self.register_packet(self._game_packet)
		return self._game_packet

	def register_player(self, ts, id, player_id, hi, lo):
		id = int(id)
		player_id = int(player_id)
		hi = int(hi)
		lo = int(lo)
		lazy_player = self._packets.manager.new_player(id, player_id, is_ai=lo == 0)
		self._entity_packet = packets.CreateGame.Player(ts, lazy_player, player_id, hi, lo)
		self.register_packet(self._entity_packet, node=self._game_packet.players)
		return lazy_player
