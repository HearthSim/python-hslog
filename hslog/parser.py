import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Union

from aniso8601 import parse_time
from hearthstone.enums import (
	BlockType, ChoiceType, FormatType, GameTag, GameType,
	MetaDataType, Mulligan, OptionType, PlayReq, PowerType
)

from . import packets, tokens
from .exceptions import ParsingError, RegexParsingError
from .packets import (
	Block, Choices, ChosenEntities, CreateGame,
	MetaData, Packet, PacketTree, SendChoices, SubSpell
)
from .player import PlayerManager, PlayerReference, coerce_to_entity_id
from .utils import parse_enum, parse_tag


class ParsingState:

	def __init__(self):
		self.current_block: Optional[Union[Packet, PacketTree]] = None
		self.game_meta = {}
		self.games = []
		self.manager = PlayerManager()
		self.mulligan_choices: Dict[int, Choices] = {}
		self.packet_tree: Optional[PacketTree] = None
		self.spectating_first_player = False
		self.spectating_second_player = False

		self.choice_packet: Optional[Choices] = None
		self.chosen_packet: Optional[ChosenEntities] = None
		self.chosen_packet_count: int = 0
		self.entity_packet: Optional[Packet] = None
		self.game_packet: Optional[CreateGame] = None
		self.metadata_node: Optional[MetaData] = None
		self.send_choice_packet: Optional[SendChoices] = None

	def block_end(self, ts):
		if not self.current_block.parent:
			logging.warning("[%s] Orphaned BLOCK_END detected", ts)
			return self.current_block

		if isinstance(self.current_block, Block):
			self.current_block.end()

		block = self.current_block
		self.current_block = self.current_block.parent
		return block

	def _register_player_name_mulligan(self, player: PlayerReference, packet: Choices):
		"""
		Attempt to register player names by looking at Mulligan choice packets.
		In Hearthstone 6.0+, registering a player name using tag changes is not
		available as early as before. That means games conceded at Mulligan no
		longer have player names.
		This technique uses the cards offered in Mulligan instead, registering
		the name of the packet's entity with the card's controller as PlayerID.
		"""
		if player.entity_id:
			# The player is already registered, ignore.
			return player
		if not player.name:
			# If we don't have the player name, we can't use this at all
			return player
		for choice in packet.choices:
			player_id = self.manager.get_controller_by_entity_id(choice)
			if player_id is None:
				raise ParsingError("Unknown entity ID in choice: %r" % choice)

			player = self.manager.create_or_update_player(
				name=player.name,
				player_id=player_id
			)

			packet.entity = player.entity_id

		return player

	def flush(self):
		if self.metadata_node:
			self.metadata_node = None

		if self.choice_packet:
			if self.choice_packet.type == ChoiceType.MULLIGAN:
				if isinstance(self.choice_packet.entity, PlayerReference):
					player = self._register_player_name_mulligan(
						self.choice_packet.entity,
						self.choice_packet
					)
					self.mulligan_choices[player.player_id] = self.choice_packet
			self.choice_packet = None

		self.chosen_packet = None

		if self.send_choice_packet:
			self.send_choice_packet = None

	def parse_entity_id(self, entity: str) -> int:
		if entity.isdigit():
			return int(entity)

		if entity == tokens.GAME_ENTITY:
			return int(self.game_packet.entity)

		sre = tokens.ENTITY_RE.match(entity)
		if sre:
			entity_id = sre.groups()[0]
			return int(entity_id)

	def parse_entity_or_player(self, entity) -> Union[None, int, PlayerReference]:
		if entity == "-1":
			return

		entity_id = self.parse_entity_id(entity)
		if entity_id is None:
			# Only case where an id is None is if it's a Player name
			return self.manager.create_or_update_player(name=entity)
		return entity_id

	def register_game(self, _ts: int, entity_id: int):
		# Use the timestamp from CREATE_GAME because it's earlier
		ts = self.packet_tree.ts
		self.game_packet = self.entity_packet = packets.CreateGame(ts, entity_id)
		self.register_packet(self.game_packet)
		return self.game_packet

	def register_packet(self, packet: Packet, node=None):
		if node is None:
			node = self.current_block.packets
		node.append(packet)
		self.packet_tree.packet_counter += 1
		packet.packet_id = self.packet_tree.packet_counter

	def register_player(self, ts, entity_id: int, player_id: int, hi: int, lo: int):
		hi = int(hi)
		lo = int(lo)
		lazy_player = self.manager.create_or_update_player(
			entity_id=entity_id,
			player_id=player_id,
			is_ai=lo == 0
		)
		self.entity_packet = packets.CreateGame.Player(ts, lazy_player, player_id, hi, lo)
		self.register_packet(self.entity_packet, node=self.game_packet.players)
		return lazy_player

	@property
	def spectator_mode(self):
		return self.spectating_first_player or self.spectating_second_player

	def set_spectating(self, first, second=None):
		self.spectating_first_player = first
		if second is not None:
			self.spectating_second_player = second


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


class HandlerBase:
	def __init__(self):
		self._game_state_processor = "GameState"

	def parse_method(self, m):
		return "%s.%s" % (self._game_state_processor, m)

	def find_callback(self, method: str) -> Callable[[ParsingState, int, Any], Any]:
		raise NotImplementedError()


class PowerHandler(HandlerBase):
	def __init__(self):
		super().__init__()

		self._creating_game = False

	@staticmethod
	def _check_for_mulligan_hack(ps: ParsingState, ts, tag, value):

		# Old game logs didn't handle asynchronous mulligans properly.
		# If we're missing an ACTION_END packet after the mulligan SendChoices,
		# we just close it out manually.

		if tag == GameTag.MULLIGAN_STATE and value == Mulligan.DEALING:
			assert ps.current_block
			if isinstance(ps.current_block, packets.Block):
				logging.warning("[%s] Broken mulligan nesting. Working around...", ts)
				ps.block_end(ts)

	def find_callback(self, method):
		if method == self.parse_method("DebugPrintPower"):
			return self.handle_data
		elif method == self.parse_method("DebugPrintGame"):
			return self.handle_game

	@staticmethod
	def handle_game(ps: ParsingState, _ts, data):
		if data.startswith("PlayerID="):
			sre = tokens.GAME_PLAYER_META.match(data)

			if not sre:
				raise RegexParsingError(data)

			player_id, player_name = sre.groups()
			ps.manager.create_or_update_player(name=player_name, player_id=int(player_id))
		else:
			key, value = data.split("=")
			key = key.strip()
			value = value.strip()
			if key == "GameType":
				value = parse_enum(GameType, value)
				ps.manager._game_type = value
			elif key == "FormatType":
				value = parse_enum(FormatType, value)
			else:
				value = int(value)

			ps.game_meta[key] = value

	def handle_data(self, ps: ParsingState, ts, data):
		opcode = data.split()[0]

		if opcode == "ERROR:":
			# Line error... skip
			return

		if opcode in PowerType.__members__:
			return self.handle_power(ps, ts, opcode, data)

		if opcode == "GameEntity":
			ps.flush()
			self._creating_game = True
			sre = tokens.GAME_ENTITY_RE.match(data)
			if not sre:
				raise RegexParsingError(data)

			entity_id_str, = sre.groups()
			ps.register_game(ts, int(entity_id_str))
		elif opcode == "Player":
			ps.flush()
			sre = tokens.PLAYER_ENTITY_RE.match(data)
			if not sre:
				raise RegexParsingError(data)

			entity_id_str, player_id_str, hi_str, lo_str = sre.groups()

			ps.register_player(
				ts,
				int(entity_id_str),
				int(player_id_str),
				int(hi_str),
				int(lo_str)
			)
		elif opcode.startswith("tag="):
			tag, value = parse_initial_tag(data)

			assert hasattr(ps.entity_packet, "tags")
			ps.entity_packet.tags.append((tag, value))  # noqa

			if tag == GameTag.CONTROLLER:

				# We need to know entity controllers for player name registration

				assert hasattr(ps.entity_packet, "entity")
				entity_id = coerce_to_entity_id(ps.entity_packet.entity)  # noqa
				ps.manager.register_controller(int(entity_id), int(value))

		elif opcode.startswith("Info["):
			if not ps.metadata_node:
				logging.warning("[%s] Metadata Info outside of META_DATA: %r", ts, data)
				return
			sre = tokens.METADATA_INFO_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			entity = ps.parse_entity_or_player(entity)
			ps.metadata_node.info.append(entity)
		elif opcode == "Source":
			sre = tokens.SUB_SPELL_START_SOURCE_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			entity, = sre.groups()
			entity = ps.parse_entity_or_player(entity)
			if not isinstance(ps.current_block, packets.SubSpell):
				logging.warning("[%s] SubSpell Source outside of SUB_SPELL: %r", ts, data)
				return
			ps.current_block.source = entity
		elif opcode.startswith("Targets["):
			sre = tokens.SUB_SPELL_START_TARGETS_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			entity = ps.parse_entity_or_player(entity)
			if not isinstance(ps.current_block, packets.SubSpell):
				logging.warning("[%s] SubSpell Target outside of SUB_SPELL: %r", ts, data)
				return
			ps.current_block.targets.append(entity)
		else:
			raise NotImplementedError(data)

	def handle_power(self, ps: ParsingState, ts, opcode, data):
		ps.flush()

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
					(
						block_type,
						entity,
						effectid,
						effectindex,
						target,
						suboption,
						trigger_keyword
					) = sre.groups()
				else:
					sre = tokens.BLOCK_START_20457_RE.match(data)
					if sre is None:
						raise RegexParsingError(data)
					(
						block_type,
						entity,
						effectid,
						effectindex,
						target,
						suboption
					) = sre.groups()
			else:
				if opcode == "ACTION_START":
					sre = tokens.ACTION_START_RE.match(data)
				else:
					sre = tokens.BLOCK_START_12051_RE.match(data)

				if sre is None:
					sre = tokens.ACTION_START_OLD_RE.match(data)
					if not sre:
						raise RegexParsingError(data)
					entity, block_type, index, target = sre.groups()
				else:
					block_type, entity, effectid, effectindex, target = sre.groups()

			self.block_start(
				ps, ts, entity, block_type, index, effectid, effectindex, target, suboption,
				trigger_keyword
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
		return callback(ps, ts, *sre.groups())

	# Messages

	@staticmethod
	def create_game(ps: ParsingState, ts):
		pt = packets.PacketTree(ts)
		pt.spectator_mode = ps.spectator_mode

		ps.games.append(pt)
		ps.current_block = pt
		ps.packet_tree = pt

	@staticmethod
	def block_end(ps, ts):
		ps.block_end(ts)

	@staticmethod
	def block_start(
		ps: ParsingState, ts, entity, block_type, index, effectid, effectindex, target,
		suboption, trigger_keyword
	):
		entity_id = ps.parse_entity_or_player(entity)
		block_type = parse_enum(BlockType, block_type)

		if index is not None:
			index = int(index)

		target = ps.parse_entity_or_player(target)

		if suboption is not None:
			suboption = int(suboption)
		if trigger_keyword is not None:
			trigger_keyword = parse_enum(GameTag, trigger_keyword)

		block = packets.Block(
			ts, entity_id, block_type, index, effectid, effectindex, target, suboption,
			trigger_keyword
		)
		block.parent = ps.current_block
		ps.register_packet(block)
		ps.current_block = block
		return block

	def _full_entity(self, ps: ParsingState, ts, entity_id: int, card_id: str):
		ps.entity_packet = packets.FullEntity(ts, entity_id, card_id)
		ps.register_packet(ps.entity_packet)

		if self._creating_game:
			# First packet after create game should always be a FULL_ENTITY
			self._creating_game = False

			# Check if we got an abnormal amount of players
			player_count = len(ps.game_packet.players)
			if player_count < 2:
				msg = "Expected at least 2 players before the first entity, got %r"
				raise ParsingError(msg % player_count)

		return ps.entity_packet

	def full_entity(self, ps: ParsingState, ts, entity_id: str, card_id: str):
		return self._full_entity(ps, ts, int(entity_id), card_id)

	def full_entity_update(self, ps: ParsingState, ts, entity_id: str, card_id: str):
		return self._full_entity(ps, ts, ps.parse_entity_id(entity_id), card_id)

	@staticmethod
	def show_entity(ps: ParsingState, ts, entity, card_id):
		entity_id = ps.parse_entity_id(entity)
		ps.entity_packet = packets.ShowEntity(ts, entity_id, card_id)
		ps.register_packet(ps.entity_packet)
		return ps.entity_packet

	@staticmethod
	def hide_entity(ps: ParsingState, ts, entity, tag, value):
		entity_id = ps.parse_entity_id(entity)
		tag, value = parse_tag(tag, value)

		if tag != GameTag.ZONE:
			raise ParsingError("HIDE_ENTITY got non-zone tag (%r)" % tag)

		packet = packets.HideEntity(ts, entity_id, value)
		ps.register_packet(packet)
		return packet

	@staticmethod
	def change_entity(ps: ParsingState, ts, entity, card_id):
		entity_id = ps.parse_entity_or_player(entity)
		ps.entity_packet = packets.ChangeEntity(ts, entity_id, card_id)
		ps.register_packet(ps.entity_packet)
		return ps.entity_packet

	@staticmethod
	def meta_data(ps: ParsingState, ts, meta, data, info_count):
		meta = parse_enum(MetaDataType, meta)

		if meta == MetaDataType.JOUST:
			data = ps.parse_entity_id(data)

		count = int(info_count)
		ps.metadata_node = MetaData(ts, meta, data, count)
		ps.register_packet(ps.metadata_node)
		return ps.metadata_node

	@staticmethod
	def _register_player_on_tag_change(
		ps: ParsingState,
		player: PlayerReference,
		tag: str,
		value: str
	):
		# Triggers on every TAG_CHANGE where the corresponding entity is a LazyPlayer.
		# Will attempt to return a new value instead

		if tag == GameTag.ENTITY_ID:

			# This is the simplest check. When a player entity is declared,
			# its ENTITY_ID is not available immediately (in pre-6.0).
			# If we get a matching ENTITY_ID, then we can use that to match it.

			return ps.manager.create_or_update_player(
				name=player.name,
				entity_id=int(value)
			)
		elif tag == GameTag.LAST_CARD_PLAYED:

			# This is a fallback to register_player_name_mulligan in case the mulligan
			# phase is not available in this game (spectator mode, reconnects).

			player_id = ps.manager.get_controller_by_entity_id(int(value))

			if player_id is None:
				raise ParsingError("Unknown entity ID on TAG_CHANGE: %r" % value)

			return ps.manager.create_or_update_player(name=player.name, player_id=player_id)
		else:
			return player

	def tag_change(self, ps: ParsingState, ts, e, tag, value, def_change):
		entity = ps.parse_entity_or_player(e)
		tag, value = parse_tag(tag, value)
		self._check_for_mulligan_hack(ps, ts, tag, value)

		if tag == GameTag.CONTROLLER:
			entity_id = coerce_to_entity_id(entity)
			ps.manager.register_controller(int(entity_id), int(value))

		elif tag == GameTag.FIRST_PLAYER:
			entity_id = coerce_to_entity_id(entity)
			ps.manager.notify_first_player(int(entity_id))

		if isinstance(entity, PlayerReference):
			entity_id = self._register_player_on_tag_change(ps, entity, tag, value)
		else:
			entity_id = entity

		has_change_def = def_change == tokens.DEF_CHANGE
		packet = packets.TagChange(ts, entity_id, tag, value, has_change_def)
		ps.register_packet(packet)
		return packet

	@staticmethod
	def reset_game(ps: ParsingState, ts):
		packet = packets.ResetGame(ts)
		ps.register_packet(packet)
		return packet

	@staticmethod
	def sub_spell_start(ps: ParsingState, ts, spell_prefab_guid, source, target_count):
		source = int(source)
		target_count = int(target_count)

		sub_spell = packets.SubSpell(ts, spell_prefab_guid, source, target_count)
		sub_spell.parent = ps.current_block
		ps.register_packet(sub_spell)
		ps.current_block = sub_spell
		return sub_spell

	@staticmethod
	def sub_spell_end(ps: ParsingState, ts):
		if not ps.current_block.parent:
			logging.warning("[%s] Orphaned SUB_SPELL_END detected", ts)
			return ps.current_block

		if isinstance(ps.current_block, SubSpell):
			ps.current_block.end()

		sub_spell = ps.current_block
		ps.current_block = ps.current_block.parent
		return sub_spell

	@staticmethod
	def cached_tag_for_dormant_change(ps: ParsingState, ts, e, tag, value):
		entity_id = ps.parse_entity_id(e)
		tag, value = parse_tag(tag, value)

		packet = packets.CachedTagForDormantChange(ts, entity_id, tag, value)
		ps.register_packet(packet)
		return packet

	@staticmethod
	def vo_spell(ps: ParsingState, ts, brguid, vospguid, blocking, delayms):
		packet = packets.VOSpell(ts, brguid, vospguid, blocking == "True", int(delayms))
		ps.register_packet(packet)
		return packet

	@staticmethod
	def shuffle_deck(ps: ParsingState, ts, player_id):
		packet = packets.ShuffleDeck(ts, int(player_id))
		ps.register_packet(packet)
		return packet


class OptionsHandler(HandlerBase):
	def __init__(self):
		super().__init__()

		self._option_packet = None
		self._options_packet = None
		self._suboption_packet = None

	def find_callback(self, method):
		if method == self.parse_method("SendOption"):
			return self.handle_send_option
		elif method == self.parse_method("DebugPrintOptions"):
			return self.handle_options

	def _parse_option_packet(self, ps: ParsingState, ts, data):
		if " errorParam=" in data:
			sre = tokens.OPTIONS_OPTION_ERROR_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			optype, entity_id, option_type, entity, error, error_param = sre.groups()
			error, error_param = clean_option_errors(error, error_param)
		else:
			sre = tokens.OPTIONS_OPTION_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			optype, entity_id, option_type, entity = sre.groups()
			error, error_param = None, None

		entity_id = int(entity_id)
		option_type = parse_enum(OptionType, option_type)
		if entity:
			entity = ps.parse_entity_or_player(entity)
		self._option_packet = packets.Option(
			ts,
			entity,
			entity_id,
			option_type,
			optype,
			error,
			error_param
		)
		if not self._options_packet:
			raise ParsingError("Option without a parent option group: %r" % data)

		ps.register_packet(self._option_packet, node=self._options_packet.options)
		self._suboption_packet = None

		return self._option_packet

	def _parse_suboption_packet(self, ps: ParsingState, ts, data):
		if " errorParam=" in data:
			sre = tokens.OPTIONS_SUBOPTION_ERROR_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			optype, entity_id, entity, error, error_param = sre.groups()
			error, error_param = clean_option_errors(error, error_param)
		else:
			sre = tokens.OPTIONS_SUBOPTION_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			optype, entity_id, entity = sre.groups()
			error, error_param = None, None

		entity_id = int(entity_id)
		if entity:
			entity = ps.parse_entity_or_player(entity)

		node = None
		packet = packets.Option(ts, entity, entity_id, None, optype, error, error_param)

		if optype == "subOption":
			self._suboption_packet = packet
			node = self._option_packet
		elif optype == "target":
			node = self._suboption_packet or self._option_packet

		if not node:
			raise ParsingError("SubOption / target without a matching option: %r" % data)

		ps.register_packet(packet, node=node.options)

		return packet

	@staticmethod
	def _check_for_options_hack(ps: ParsingState, ts):

		# Battlegrounds games tend to omit the BLOCK_END just before options start. As
		# options will always be on the top level, we can safely close any remaining block
		# that is open at this time.

		if isinstance(ps.current_block, packets.Block):
			logging.warning("[%s] Broken option nesting. Working around...", ts)
			ps.block_end(ts)
			assert not isinstance(ps.current_block, packets.Block)

	def handle_options(self, ps: ParsingState, ts, data):
		self._check_for_options_hack(ps, ts)
		if data.startswith("id="):
			sre = tokens.OPTIONS_ENTITY_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			entity_id, = sre.groups()
			entity_id = int(entity_id)
			self._options_packet = packets.Options(ts, entity_id)
			ps.current_block.packets.append(self._options_packet)
		elif data.startswith("option "):
			return self._parse_option_packet(ps, ts, data)
		elif data.startswith(("subOption ", "target ")):
			return self._parse_suboption_packet(ps, ts, data)

	def handle_send_option(self, ps: ParsingState, ts, data):
		if data.startswith("selectedOption="):
			sre = tokens.SEND_OPTION_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			option, suboption, target, position = sre.groups()
			packet = packets.SendOption(
				ts,
				int(option),
				int(suboption),
				int(target),
				int(position)
			)
			ps.register_packet(packet)
			return packet
		raise NotImplementedError("Unhandled send option: %r" % data)


class ChoicesHandler(HandlerBase):
	def __init__(self):
		super().__init__()

	def find_callback(self, method):
		if method == self.parse_method("DebugPrintEntityChoices"):
			return self.handle_entity_choices
		elif method == self.parse_method("DebugPrintChoices"):
			return self.handle_entity_choices_old
		elif method == self.parse_method("SendChoices"):
			return self.handle_send_choices
		elif method == self.parse_method("DebugPrintEntitiesChosen"):
			return self.handle_entities_chosen

	def handle_entity_choices_old(self, ps: ParsingState, ts, data):
		if data.startswith("id="):
			sre = tokens.CHOICES_CHOICE_OLD_1_RE.match(data)
			if sre:
				self.register_choices_old_1(ps, ts, *sre.groups())
			else:
				sre = tokens.CHOICES_CHOICE_OLD_2_RE.match(data)
				if not sre:
					raise RegexParsingError(data)
				self.register_choices_old_2(ps, ts, *sre.groups())
		else:
			return self.handle_entity_choices(ps, ts, data)

	def handle_entity_choices(self, ps: ParsingState, ts, data):
		if data.startswith("id="):
			sre = tokens.CHOICES_CHOICE_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			return self.register_choices(ps, ts, *sre.groups())
		elif data.startswith("Source="):
			sre = tokens.CHOICES_SOURCE_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			entity, = sre.groups()
			entity_id = ps.parse_entity_or_player(entity)
			if not ps.choice_packet:
				raise ParsingError("Source Choice Entity outside of choie packet: %r" % data)
			ps.choice_packet.source = entity_id
			return entity_id
		elif data.startswith("Entities["):
			sre = tokens.CHOICES_ENTITIES_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			entity_id = ps.parse_entity_or_player(entity)
			if not entity_id:
				raise ParsingError("Missing choice entity %r (%r)" % (entity_id, entity))
			if not ps.choice_packet:
				raise ParsingError("Choice Entity outside of choice packet: %r" % data)
			ps.choice_packet.choices.append(entity_id)
			return entity_id
		raise NotImplementedError("Unhandled entity choice: %r" % data)

	@staticmethod
	def _register_choices(
		ps: ParsingState,
		ts,
		choice_id,
		player,
		tasklist,
		choice_type,
		min_choice,
		max_choice
	):
		choice_type = parse_enum(ChoiceType, choice_type)
		min_choice, max_choice = int(min_choice), int(max_choice)
		ps.choice_packet = packets.Choices(
			ts,
			player,
			choice_id,
			tasklist,
			choice_type,
			min_choice,
			max_choice
		)
		ps.register_packet(ps.choice_packet)
		return ps.choice_packet

	def register_choices_old_1(self, ps: ParsingState, ts, choice_id, choice_type):
		player = None

		# XXX: We don't have a player here for old games.
		# Is it safe to assume CURRENT_PLAYER?

		tasklist = None
		min_choice, max_choice = 0, 0

		return self._register_choices(
			ps,
			ts,
			int(choice_id),
			player,
			tasklist,
			choice_type,
			min_choice,
			max_choice
		)

	def register_choices_old_2(
		self,
		ps: ParsingState,
		ts,
		choice_id,
		player_id,
		choice_type,
		min_choice,
		max_choice
	):
		return self._register_choices(
			ps,
			ts,
			int(choice_id),
			ps.manager.get_player_by_player_id(int(player_id)),
			None,
			choice_type,
			min_choice,
			max_choice
		)

	def register_choices(
		self,
		ps: ParsingState,
		ts,
		choice_id,
		player,
		tasklist,
		choice_type,
		min_choice,
		max_choice
	):
		player = ps.parse_entity_or_player(player)

		if tasklist is not None:
			# Sometimes tasklist is empty

			tasklist = int(tasklist)

		return self._register_choices(
			ps,
			ts,
			int(choice_id),
			player,
			tasklist,
			choice_type,
			min_choice,
			max_choice
		)

	def handle_send_choices(self, ps: ParsingState, ts, data):
		if data.startswith("id="):
			sre = tokens.SEND_CHOICES_CHOICE_RE.match(data)

			if not sre:
				raise RegexParsingError(data)

			choice_id, choice_type = sre.groups()
			ps.send_choice_packet = packets.SendChoices(
				ts,
				int(choice_id),
				parse_enum(ChoiceType, choice_type)
			)
			ps.register_packet(ps.send_choice_packet)
			return ps.send_choice_packet
		elif data.startswith("m_chosenEntities"):
			sre = tokens.SEND_CHOICES_ENTITIES_RE.match(data)

			if not sre:
				raise RegexParsingError(data)

			idx, entity = sre.groups()
			ep = ps.parse_entity_or_player(entity)

			if not ep:
				raise ParsingError("Missing chosen entity %r (%r)" % (ep, entity))
			if not ps.send_choice_packet:
				raise ParsingError("Chosen Entity outside of choice packet: %r" % data)

			ps.send_choice_packet.choices.append(ep)
			return ep
		raise NotImplementedError("Unhandled send choice: %r" % data)

	def handle_entities_chosen(self, ps: ParsingState, ts, data):
		if data.startswith("id="):
			sre = tokens.ENTITIES_CHOSEN_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			choice_id, player, count = sre.groups()
			player = ps.parse_entity_or_player(player)

			ps.chosen_packet_count = int(count)
			ps.chosen_packet = packets.ChosenEntities(ts, player, int(choice_id))
			ps.register_packet(ps.chosen_packet)

			for player_id, mulligan_choice in ps.mulligan_choices.items():
				if mulligan_choice.id == ps.chosen_packet.id:
					ps.manager.create_or_update_player(
						name=player.name,
						player_id=player_id
					)
					break

			return ps.chosen_packet
		elif data.startswith("Entities["):
			sre = tokens.ENTITIES_CHOSEN_ENTITIES_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			idx, entity = sre.groups()
			entity_id = ps.parse_entity_or_player(entity)

			if not entity_id:
				raise ParsingError("Missing entity chosen %r (%r)" % (entity_id, entity))
			if not ps.chosen_packet:
				raise ParsingError("Entity Chosen outside of choice packet: %r" % data)

			ps.chosen_packet.choices.append(entity_id)

			if len(ps.chosen_packet.choices) > ps.chosen_packet_count:
				raise ParsingError(
					"Too many choices (expected %r)" % ps.chosen_packet_count
				)
			return entity_id
		raise NotImplementedError("Unhandled entities chosen: %r" % data)


class SpectatorModeHandler:

	def process_spectator_mode(self, ps: ParsingState, line):
		if line == tokens.SPECTATOR_MODE_BEGIN_GAME:
			ps.set_spectating(True)
		elif line == tokens.SPECTATOR_MODE_BEGIN_FIRST:
			ps.set_spectating(True, False)
		elif line == tokens.SPECTATOR_MODE_BEGIN_SECOND:
			ps.set_spectating(True, True)
		elif line == tokens.SPECTATOR_MODE_END_MODE:
			ps.set_spectating(False, False)
		elif line == tokens.SPECTATOR_MODE_END_GAME:
			ps.set_spectating(False, False)
		else:
			raise NotImplementedError("Unhandled spectator mode: %r" % line)


class LogParser:
	def __init__(self):
		self.line_regex = tokens.POWERLOG_LINE_RE
		self._current_date = None
		self._synced_timestamp = False
		self._last_ts = None

		self._parsing_state = ParsingState()

		self._power_handler = PowerHandler()
		self._choices_handler = ChoicesHandler()
		self._options_handler = OptionsHandler()
		self._spectator_mode_handler = SpectatorModeHandler()

	def flush(self):
		self._parsing_state.flush()

	@property
	def game_meta(self):
		return self._parsing_state.game_meta

	@property
	def games(self):
		return self._parsing_state.games

	def handle_entity_choices(self, ts, data):
		return self._choices_handler.handle_entity_choices(self._parsing_state, ts, data)

	def handle_options(self, ts, data):
		return self._options_handler.handle_options(self._parsing_state, ts, data)

	def handle_power(self, ts, opcode, data):
		return self._power_handler.handle_power(self._parsing_state, ts, opcode, data)

	def parse_entity_id(self, entity):
		return self._parsing_state.parse_entity_id(entity)

	def parse_timestamp(self, ts, _method):
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

	@property
	def player_manager(self):
		return self._parsing_state.manager

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
			return self._spectator_mode_handler.process_spectator_mode(
				self._parsing_state,
				line
			)

		sre = self.line_regex.match(line)

		if not sre:
			return

		method, msg = sre.groups()
		msg = msg.strip()

		if not self._parsing_state.current_block and "CREATE_GAME" not in msg:

			# Ignore messages before the first CREATE_GAME packet

			return

		for handler in self._power_handler, self._choices_handler, self._options_handler:
			callback = handler.find_callback(method)
			if callback:
				ts = self.parse_timestamp(ts, method)
				return callback(self._parsing_state, ts, msg)
