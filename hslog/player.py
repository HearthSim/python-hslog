"""
Classes to provide lazy players that are treatable as an entity ID but
do not have to receive one immediately.
"""
from hearthstone.enums import GameTag

from .exceptions import MissingPlayerData, ParsingError
from .tokens import UNKNOWN_HUMAN_PLAYER


class LazyPlayer:
	def __init__(self, *args, **kwargs):
		self.id = None
		self.name = None

	def __repr__(self):
		return "%s(id=%r, name=%r)" % (self.__class__.__name__, self.id, self.name)

	def __int__(self):
		if not self.id:
			raise MissingPlayerData("Entity ID not available for player %r" % (self.name))
		return self.id


class PlayerManager:
	def __init__(self):
		self._players_by_id = {}
		self._players_by_name = {}
		self._players_by_player_id = {}
		self._entity_controller_map = {}
		self._registered_names = []
		self._unregistered_names = set()
		self.ai_player = None

	def get_player_by_id(self, id):
		assert id, "Expected an id for get_player_by_id (got %r)" % (id)
		if id not in self._players_by_id:
			lazy_player = LazyPlayer()
			lazy_player.id = id
			self._players_by_id[id] = lazy_player
		return self._players_by_id[id]

	def get_player_by_name(self, name):
		assert name, "Expected a name for get_player_by_name (got %r)" % (name)
		if name not in self._players_by_name:
			if len(self._registered_names) == 1 and name != UNKNOWN_HUMAN_PLAYER:
				# Maybe we can figure the name out right there and then
				other_player = self.get_player_by_name(self._registered_names[0])
				id = 3 if other_player == 2 else 2
				try:
					self.register_player_name(name, id)
				except KeyError:
					raise ParsingError("Unseen player name %r" % (name))
			elif len(self._registered_names) > 1 and self.ai_player:
				# If we are registering our 3rd (or more) name, and we are in an AI game...
				# then it's probably the innkeeper with a new name.
				self.register_player_name(name, int(self.ai_player))
			else:
				lazy_player = LazyPlayer()
				lazy_player.name = name
				self._players_by_name[name] = lazy_player
				self._unregistered_names.add(name)
		return self._players_by_name[name]

	def new_player(self, id, player_id, is_ai):
		lazy_player = self.get_player_by_id(id)
		self._players_by_player_id[player_id] = lazy_player
		if is_ai:
			self.ai_player = lazy_player
		return lazy_player

	def register_controller(self, entity, controller):
		self._entity_controller_map[entity] = controller

	def register_player_name_by_player_id(self, name, player_id):
		# We probably should raise an error if the name is not in _unregistered_names
		# In practice this breaks though if we have a game with identical player names
		if name in self._players_by_name and name in self._unregistered_names:
			self._unregistered_names.remove(name)

		lazy_player_by_player_id = self._players_by_player_id[player_id]
		lazy_player_by_player_id.name = name

		if name != UNKNOWN_HUMAN_PLAYER:
			self._registered_names.append(name)

		self._players_by_name[name] = lazy_player_by_player_id.id

		return lazy_player_by_player_id

	def register_player_name(self, name, id):
		"""
		Registers a link between \a name and \a id.
		Note that this does not support two different players with the same name.
		"""
		if name in self._players_by_name:
			self._players_by_name[name].id = id
			self._unregistered_names.remove(name)
		self._players_by_name[name] = id
		lazy_player_by_id = self._players_by_id[id]
		lazy_player_by_id.name = name
		self._registered_names.append(name)

		if len(self._unregistered_names) == 1:
			assert len(self._players_by_id) == 2
			id1, id2 = self._players_by_id.keys()
			other_id = id2 if id == id1 else id1
			other_name = list(self._unregistered_names)[0]
			self.register_player_name(other_name, other_id)

		return lazy_player_by_id

	def register_player_name_mulligan(self, packet):
		"""
		Attempt to register player names by looking at Mulligan choice packets.
		In Hearthstone 6.0+, registering a player name using tag changes is not
		available as early as before. That means games conceded at Mulligan no
		longer have player names.
		This technique uses the cards offered in Mulligan instead, registering
		the name of the packet's entity with the card's controller as PlayerID.
		"""
		lazy_player = packet.entity
		if isinstance(lazy_player, int) or lazy_player.id:
			# The player is already registered, ignore.
			return
		if not lazy_player.name:
			# If we don't have the player name, we can't use this at all
			return

		for choice in packet.choices:
			if choice not in self._entity_controller_map:
				raise ParsingError("Unknown entity ID in choice: %r" % (choice))
			player_id = self._entity_controller_map[choice]
			# We need ENTITY_ID for register_player_name()
			if player_id not in self._players_by_player_id:
				raise ParsingError("Unseen player id %r" % (player_id))
			entity_id = int(self._players_by_player_id[player_id])
			packet.entity = entity_id
			return self.register_player_name(lazy_player.name, entity_id)

	def register_player_name_on_tag_change(self, player, tag, value):
		"""
		Triggers on every TAG_CHANGE where the corresponding entity is a LazyPlayer.
		Will attempt to return a new value instead
		"""
		if tag == GameTag.ENTITY_ID:
			# This is the simplest check. When a player entity is declared,
			# its ENTITY_ID is not available immediately (in pre-6.0).
			# If we get a matching ENTITY_ID, then we can use that to match it.
			return self.register_player_name(player.name, value)
		elif tag == GameTag.LAST_CARD_PLAYED:
			# This is a fallback to register_player_name_mulligan in case the mulligan
			# phase is not available in this game (spectator mode, reconnects).
			if value not in self._entity_controller_map:
				raise ParsingError("Unknown entity ID on TAG_CHANGE: %r" % (value))
			player_id = self._entity_controller_map[value]
			entity_id = int(self._players_by_player_id[player_id])
			return self.register_player_name(player.name, entity_id)

		return player
