from typing import Dict, Optional, cast

from hearthstone.entities import Card, Game, Player
from hearthstone.enums import BlockType, GameTag, Zone

from . import packets
from .exceptions import ExporterError, MissingPlayerData
from .player import PlayerManager, coerce_to_entity_id


class BaseExporter:
	def __init__(self, packet_tree):
		self.packet_tree = packet_tree
		self.dispatch = self.get_dispatch_dict()

	def get_dispatch_dict(self):
		return {
			packets.CreateGame: self.handle_create_game,
			packets.CreateGame.Player: self.handle_player,
			packets.Block: self.handle_block,
			packets.FullEntity: self.handle_full_entity,
			packets.HideEntity: self.handle_hide_entity,
			packets.ShowEntity: self.handle_show_entity,
			packets.ChangeEntity: self.handle_change_entity,
			packets.TagChange: self.handle_tag_change,
			packets.MetaData: self.handle_metadata,
			packets.Choices: self.handle_choices,
			packets.SendChoices: self.handle_send_choices,
			packets.ChosenEntities: self.handle_chosen_entities,
			packets.Options: self.handle_options,
			packets.Option: self.handle_option,
			packets.SendOption: self.handle_send_option,
			packets.ResetGame: self.handle_reset_game,
			packets.SubSpell: self.handle_sub_spell,
			packets.CachedTagForDormantChange: self.handle_cached_tag_for_dormant_change,
			packets.VOSpell: self.handle_vo_spell,
			packets.ShuffleDeck: self.handle_shuffle_deck
		}

	def export(self) -> "BaseExporter":
		for packet in self.packet_tree:
			self.export_packet(packet)
		self.flush()
		return self

	def export_packet(self, packet: packets.Packet):
		packet_type = packet.__class__
		handler = self.dispatch.get(packet_type, None)
		if not handler:
			raise NotImplementedError("Don't know how to export %r" % packet_type)
		handler(packet)

	def flush(self):
		"""Finalize the export and allow any intermediate state to be cleaned up."""
		pass

	def handle_create_game(self, packet: packets.CreateGame):
		pass

	def handle_player(self, packet: packets.CreateGame.Player):
		pass

	def handle_block(self, packet: packets.Block):
		for p in packet.packets:
			self.export_packet(p)

	def handle_full_entity(self, packet: packets.FullEntity):
		pass

	def handle_hide_entity(self, packet: packets.HideEntity):
		pass

	def handle_show_entity(self, packet: packets.ShowEntity):
		pass

	def handle_change_entity(self, packet: packets.ChangeEntity):
		pass

	def handle_tag_change(self, packet: packets.TagChange):
		pass

	def handle_metadata(self, packet: packets.MetaData):
		pass

	def handle_choices(self, packet: packets.Choices):
		pass

	def handle_send_choices(self, packet: packets.SendChoices):
		pass

	def handle_chosen_entities(self, packet: packets.ChosenEntities):
		pass

	def handle_options(self, packet: packets.Options):
		pass

	def handle_option(self, packet: packets.Option):
		pass

	def handle_send_option(self, packet: packets.SendOption):
		pass

	def handle_reset_game(self, packet: packets.ResetGame):
		pass

	def handle_sub_spell(self, packet: packets.SubSpell):
		for p in packet.packets:
			self.export_packet(p)

	def handle_cached_tag_for_dormant_change(
		self, packet: packets.CachedTagForDormantChange
	):
		pass

	def handle_vo_spell(self, packet: packets.VOSpell):
		pass

	def handle_shuffle_deck(self, packet: packets.ShuffleDeck):
		pass


class CompositeExporter(BaseExporter):
	"""Exporter implementation that broadcasts packets to configured child exporters

	Use this class to compose multiple exporters in order to do a single pass over a
	configured packet tree. Note:

	- Packet trees passed to constructors of child exporters will be ignored; only the
	packets in the packet tree passed to this class's constructor will be visited.
	- Unlike BaseExporter, the `handle_block` and `handle_sub_spell` methods on this class
	do not recursively invoke the `handle_packet` on child packets; child exporters used in
	an instance of CompositeExporter *should* continue to recursively invoke `handle_packet`
	however (or delegate to their superclass implementation).
	"""

	def __init__(self, packet_tree, exporters):
		super().__init__(packet_tree)
		self.exporters = exporters

	def flush(self):
		for exporter in self.exporters:
			exporter.flush()

	def handle_create_game(self, packet):
		for exporter in self.exporters:
			exporter.handle_create_game(packet)

	def handle_player(self, packet):
		for exporter in self.exporters:
			exporter.handle_player(packet)

	def handle_block(self, packet):
		for exporter in self.exporters:
			exporter.handle_block(packet)

	def handle_full_entity(self, packet):
		for exporter in self.exporters:
			exporter.handle_full_entity(packet)

	def handle_hide_entity(self, packet):
		for exporter in self.exporters:
			exporter.handle_hide_entity(packet)

	def handle_show_entity(self, packet):
		for exporter in self.exporters:
			exporter.handle_show_entity(packet)

	def handle_change_entity(self, packet):
		for exporter in self.exporters:
			exporter.handle_change_entity(packet)

	def handle_tag_change(self, packet):
		for exporter in self.exporters:
			exporter.handle_tag_change(packet)

	def handle_metadata(self, packet):
		for exporter in self.exporters:
			exporter.handle_metadata(packet)

	def handle_choices(self, packet):
		for exporter in self.exporters:
			exporter.handle_choices(packet)

	def handle_send_choices(self, packet):
		for exporter in self.exporters:
			exporter.handle_send_choices(packet)

	def handle_chosen_entities(self, packet):
		for exporter in self.exporters:
			exporter.handle_chosen_entities(packet)

	def handle_options(self, packet):
		for exporter in self.exporters:
			exporter.handle_options(packet)

	def handle_option(self, packet):
		for exporter in self.exporters:
			exporter.handle_option(packet)

	def handle_send_option(self, packet):
		for exporter in self.exporters:
			exporter.handle_send_option(packet)

	def handle_reset_game(self, packet):
		for exporter in self.exporters:
			exporter.handle_reset_game(packet)

	def handle_sub_spell(self, packet):
		for exporter in self.exporters:
			exporter.handle_sub_spell(packet)

	def handle_cached_tag_for_dormant_change(self, packet):
		for exporter in self.exporters:
			exporter.handle_cached_tag_for_dormant_change(packet)

	def handle_vo_spell(self, packet):
		for exporter in self.exporters:
			exporter.handle_vo_spell(packet)

	def handle_shuffle_deck(self, packet):
		for exporter in self.exporters:
			exporter.handle_shuffle_deck(packet)


class EntityTreeExporter(BaseExporter):
	game_class = Game
	player_class = Player
	card_class = Card

	class EntityNotFound(Exception):
		pass

	def __init__(self, packet_tree, player_manager: Optional[PlayerManager] = None):
		super().__init__(packet_tree)

		self.game: Optional[Game] = None

		self.player_manager = player_manager

	def find_entity(self, entity_id: int, opcode) -> Card:
		try:
			entity = self.game.find_entity_by_id(entity_id)
		except MissingPlayerData:
			raise self.EntityNotFound(
				f"Error getting entity {entity_id} for {opcode}"
			)
		if not entity:
			raise self.EntityNotFound(
				f"Attempting {opcode} on entity {entity_id} (not found)"
			)
		return cast(Card, entity)

	def handle_block(self, packet):
		if packet.type == BlockType.GAME_RESET:
			self.game.reset()
		super().handle_block(packet)

	def handle_create_game(self, packet):
		self.game = self.game_class(packet.entity)
		self.game.create(packet.tags)
		for player in packet.players:
			self.export_packet(player)
		return self.game

	def handle_player(self, packet):
		entity_id = coerce_to_entity_id(packet.entity)

		# If we have a PlayerManager, first we mutate the CreateGame.Player packet.
		# This will have to change if we're ever able to immediately get the names.

		if self.player_manager:
			player = self.player_manager.get_player_by_entity_id(int(entity_id))
			packet.name = player.name

		entity = self.player_class(
			entity_id,
			packet.player_id,
			packet.hi,
			packet.lo,
			packet.name
		)
		entity.tags = dict(packet.tags)
		self.game.register_entity(entity)
		entity.initial_hero_entity_id = entity.tags.get(GameTag.HERO_ENTITY, 0)
		return entity

	def handle_full_entity(self, packet):
		entity_id = packet.entity

		# Check if the entity already exists in the game first.
		# This prevents creating it twice.
		# This can legitimately happen in case of GAME_RESET
		existing_entity = self.game.find_entity_by_id(entity_id)
		if existing_entity is not None:
			existing_entity.card_id = packet.card_id
			existing_entity.tags = dict(packet.tags)
			return existing_entity

		entity = self.card_class(int(entity_id), packet.card_id)
		entity.tags = dict(packet.tags)
		self.game.register_entity(entity)
		return entity

	def handle_hide_entity(self, packet):
		entity = self.find_entity(packet.entity, "HIDE_ENTITY")
		entity.hide()
		return entity

	def handle_show_entity(self, packet):
		entity = self.find_entity(packet.entity, "SHOW_ENTITY")
		entity.reveal(packet.card_id, dict(packet.tags))
		return entity

	def handle_change_entity(self, packet):
		entity = self.find_entity(packet.entity, "CHANGE_ENTITY")
		if not entity.card_id:
			# This can only happen if the entity's initial reveal was missed.
			# Not raising this can cause entities to have a card id, but no initial_card_id.
			# If you want that behaviour, subclass EntityTreeExporter and override this.
			raise ExporterError(
				f"CHANGE_ENTITY {packet.entity} to {packet.card_id} with no previous known CardID."
			)
		entity.change(packet.card_id, dict(packet.tags))
		return entity

	def handle_tag_change(self, packet):
		entity_id = coerce_to_entity_id(packet.entity)
		entity = self.find_entity(int(entity_id), "TAG_CHANGE")
		entity.tag_change(packet.tag, packet.value)

		return entity


class FriendlyPlayerExporter(BaseExporter):
	"""
	An exporter that will attempt to guess the friendly player in the game by
	looking for initial unrevealed cards.
	May produce incorrect results in spectator mode if both hands are revealed.
	"""
	def __init__(self, packet_tree):
		super().__init__(packet_tree)
		self._controller_map: Dict[int, int] = {}
		self.friendly_player = None
		self._ai_player = None
		self._non_ai_players = []

	def export(self):
		for packet in self.packet_tree:
			self.export_packet(packet)
			if self.friendly_player is not None:
				# Stop export once we have it
				break
		return self.friendly_player

	def handle_create_game(self, packet):
		for player in packet.players:
			self.export_packet(player)
		if self._ai_player is not None and len(self._non_ai_players) == 1:
			self.friendly_player = self._non_ai_players[0]

	def handle_player(self, packet):
		if packet.lo == 0:
			self._ai_player = packet.player_id
		else:
			self._non_ai_players.append(packet.player_id)

	def handle_tag_change(self, packet):
		if packet.tag == GameTag.CONTROLLER:
			self._controller_map[int(packet.entity)] = packet.value

	def handle_full_entity(self, packet):
		tags = dict(packet.tags)
		if GameTag.CONTROLLER in tags:
			self._controller_map[int(packet.entity)] = tags[GameTag.CONTROLLER]

	def handle_show_entity(self, packet):
		tags = dict(packet.tags)
		if GameTag.CONTROLLER in tags:
			self._controller_map[int(packet.entity)] = tags[GameTag.CONTROLLER]

		if tags.get(GameTag.ZONE) != Zone.HAND:
			# Ignore cards already in play (such as enchantments, common in TB)
			return

		# The first SHOW_ENTITY packet will always be the friendly player's.
		self.friendly_player = self._controller_map[packet.entity]
