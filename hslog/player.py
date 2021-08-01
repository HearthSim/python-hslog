"""
Classes to provide lazy players that are treatable as an entity ID but
do not have to receive one immediately.
"""
from typing import Optional, Dict

from hearthstone.enums import GameType

from .tokens import UNKNOWN_HUMAN_PLAYER


class PlayerReference:
	def __init__(
		self,
		entity_id: Optional[int] = None,
		name: Optional[str] = None,
		player_id: Optional[int] = None
	):
		self.entity_id = entity_id
		self.name = name
		self.player_id = player_id

	def __repr__(self):
		return "%s(name=%r, entity_id=%r, player_id=%r)" % (
			self.__class__.__name__,
			self.name,
			self.entity_id,
			self.player_id
		)


class PlayerManager:
	def __init__(self):
		self._players_by_name: Dict[str, PlayerReference] = {}
		self._players_by_entity_id: Dict[int, PlayerReference] = {}
		self._players_by_player_id: Dict[int, PlayerReference] = {}
		self._entity_controller_map = {}
		self._registered_names = []
		self._unregistered_names = set()
		self.ai_player = None
		self._game_type = None

	def get_player_by_entity_id(self, entity_id: int) -> Optional[PlayerReference]:
		return self._players_by_entity_id.get(entity_id)

	def get_player_by_player_id(self, player_id: int) -> Optional[PlayerReference]:
		return self._players_by_player_id.get(player_id)

	def _guess_player_entity_id(self, name: str) -> Optional[PlayerReference]:
		assert name, "Expected a name for get_player_by_name (got %r)" % name
		if name not in self._players_by_name:
			if (
				len(self._players_by_name) == 1 and
				name != UNKNOWN_HUMAN_PLAYER and
				self._game_type != GameType.GT_BATTLEGROUNDS
			):
				# Maybe we can figure the name out right there and then.

				# NOTE: This is a neat trick, but it doesn't really work (and leads to
				# errors) when there are lots of players such that we can't predict the
				# entity ids. Hence the check for Battlegrounds above.

				other_player = next(iter(self._players_by_name.values()))
				entity_id = 3 if other_player.entity_id == 2 else 2
				if entity_id not in self._players_by_entity_id:
					return self.create_or_update_player(
						name=name,
						entity_id=entity_id
					)
				else:
					return None
			elif len(self._registered_names) > 1 and self.ai_player:
				# If we are registering our 3rd (or more) name, and we are in an AI game...
				# then it's probably the innkeeper with a new name.

				return self.create_or_update_player(
					name=name,
					entity_id=self.ai_player.entity_id
				)
			else:
				return self.create_or_update_player(name=name)

	def create_or_update_player(
		self,
		name: Optional[str] = None,
		entity_id: Optional[int] = None,
		player_id: Optional[int] = None,
		is_ai: bool = False
	):
		assert name or entity_id or player_id

		if name and name != UNKNOWN_HUMAN_PLAYER and name in self._players_by_name:
			player = self._players_by_name[name]
		elif entity_id and entity_id in self._players_by_entity_id:
			player = self._players_by_entity_id[entity_id]
		elif player_id and player_id in self._players_by_player_id:
			player = self._players_by_player_id[player_id]
		else:
			player = PlayerReference(
				name=name,
				entity_id=entity_id,
				player_id=player_id,
			)

		if is_ai:
			self.ai_player = player

		if name:
			if player.name is None or player.name == UNKNOWN_HUMAN_PLAYER:
				player.name = name
				if name != UNKNOWN_HUMAN_PLAYER:
					if not player.entity_id and not entity_id:

						# We don't have an entity_id but we do have a name; let's see if we
						# can guess the entity id...

						self._guess_player_entity_id(name)

					assert name not in self._players_by_name
					self._players_by_name[name] = player

			elif player.name != name:
				raise AssertionError()

		if entity_id:
			if player.entity_id is None:
				assert entity_id not in self._players_by_entity_id
				self._players_by_entity_id[entity_id] = player
			elif player.entity_id != entity_id:
				raise AssertionError()

		if player_id:
			if player.player_id is None:
				assert player_id not in self._players_by_player_id
				self._players_by_player_id[player_id] = player
			elif player.player_id != player_id:
				raise AssertionError()

	def register_controller(self, entity, controller):
		self._entity_controller_map[entity] = controller

	def get_controller_by_entity_id(self, entity_id: int) -> Optional[int]:
		return self._entity_controller_map.get(entity_id)
