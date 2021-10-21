"""
Classes to provide lazy players that are treatable as an entity ID but
do not have to receive one immediately.
"""
from typing import Dict, List, Optional, Union

from hearthstone.enums import GameType

from .exceptions import MissingPlayerData
from .tokens import UNKNOWN_HUMAN_PLAYER
from .utils import is_mercenaries_game_type


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

	def __eq__(self, other):
		if not isinstance(other, PlayerReference):
			return False

		return (
			self.entity_id == other.entity_id and
			self.name == other.name and
			self.player_id == other.player_id
		)

	def __hash__(self):
		return hash((self.entity_id, self.name, self.player_id))

	def __repr__(self):
		return "%s(name=%r, entity_id=%r, player_id=%r)" % (
			self.__class__.__name__,
			self.name,
			self.entity_id,
			self.player_id
		)


def coerce_to_entity_id(entity_id_or_player: Union[int, PlayerReference]) -> int:
	if isinstance(entity_id_or_player, PlayerReference):
		if entity_id_or_player.entity_id is None:
			raise MissingPlayerData(
				"Entity ID not available for player %r" % entity_id_or_player.name
			)

		return entity_id_or_player.entity_id
	else:
		return entity_id_or_player


class InconsistentEntityIdError(Exception):

	def __init__(self, player: PlayerReference, entity_id: int):
		self.player = player
		self.entity_id = entity_id


class InconsistentPlayerIdError(Exception):

	def __init__(self, player: PlayerReference, player_id: int):
		self.player = player
		self.player_id = player_id


class PlayerManager:
	def __init__(self):
		self._entity_controller_map: Dict[int, int] = {}
		self._game_type = None
		self._name_aliases: Dict[str, str] = {}
		self._players_by_name: Dict[str, PlayerReference] = {}
		self._players_by_entity_id: Dict[int, PlayerReference] = {}
		self._players_by_player_id: Dict[int, PlayerReference] = {}
		self._player_resolution_order: List[int] = []

		self.ai_player: Optional[PlayerReference] = None
		self.first_player: Optional[PlayerReference] = None

	def _maybe_alias_name(self, name):
		if "#" in name:
			alias = name[:name.index("#")]
			if alias in self._name_aliases:
				assert self._name_aliases[alias] == name
			else:
				self._name_aliases[alias] = name

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
				self._game_type != GameType.GT_BATTLEGROUNDS and
				not is_mercenaries_game_type(self._game_type)
			):
				# Maybe we can figure the name out right there and then.

				# NOTE: This is a neat trick, but it doesn't really work (and leads to
				# errors) when there are lots of players such that we can't predict the
				# entity ids. Hence the check for Battlegrounds above.

				other_player = next(iter(self._players_by_name.values()))
				entity_id = 3 if other_player.entity_id == 2 else 2
				if entity_id in self._players_by_entity_id:
					player = self._players_by_entity_id[entity_id]
					player.name = name

					self._players_by_name[name] = player
					self._maybe_alias_name(name)

					return player
				else:
					return self.create_or_update_player(
						name=name,
						entity_id=entity_id
					)
			elif len(self._players_by_name) > 1 and self.ai_player:
				# If we are registering our 3rd (or more) name, and we are in an AI game...
				# then it's probably the innkeeper with a new name.

				return self.create_or_update_player(
					name=name,
					entity_id=self.ai_player.entity_id
				)
			else:
				return None

	def create_or_update_player(
		self,
		name: Optional[str] = None,
		entity_id: Optional[int] = None,
		player_id: Optional[int] = None,
		is_ai: bool = False
	) -> PlayerReference:
		assert name or entity_id or player_id

		player: Optional[PlayerReference] = None

		if name and name != UNKNOWN_HUMAN_PLAYER:
			if name in self._players_by_name:
				player = self._players_by_name[name]
			elif name in self._name_aliases:
				player = self._players_by_name[self._name_aliases[name]]
			else:
				player = None

		if player is None:
			if entity_id and entity_id in self._players_by_entity_id:
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
			elif player.name != name and player.name != self._name_aliases.get(name):
				if player == self.ai_player:

					# Need to check whether this is just the Innkeeper's name changing,
					# which happens for all sorts of valid reasons

					player.name = name
				elif name == UNKNOWN_HUMAN_PLAYER:

					# If we're pretty sure we know which player's being referred to and it
					# looks like the log is trying to set the player name to "UNKOWN HUMAN
					# PLAYER" it could be a little bit of asynchrony that we can ignore.
					# Just treat this like the log used the right name.

					name = player.name
				else:
					raise AssertionError()

			if (
				name != UNKNOWN_HUMAN_PLAYER and
				name not in self._players_by_name and
				name not in self._name_aliases
			):
				if not player.entity_id and not entity_id:

					# We don't have an entity_id but we do have a name; let's see if we
					# can guess the entity id...

					self._guess_player_entity_id(name)
					if name in self._players_by_name:
						player = self._players_by_name[name]

				self._players_by_name[name] = player
				self._maybe_alias_name(name)
			elif player.name != name and player.name != self._name_aliases.get(name):
				raise AssertionError()

		if entity_id:
			if player.entity_id is None:
				player.entity_id = entity_id
			elif player.entity_id != entity_id:
				raise InconsistentEntityIdError(player, entity_id)

			if player.entity_id in self._players_by_entity_id:
				self._safe_merge_player_references(
					self._players_by_entity_id[player.entity_id],
					player,
				)
			else:
				self._players_by_entity_id[entity_id] = player

		if player_id:
			if player.player_id is None:
				player.player_id = player_id
			elif player.player_id != player_id and not is_mercenaries_game_type(self._game_type):
				raise InconsistentPlayerIdError(player, player_id)

			if player.player_id in self._players_by_player_id:
				self._safe_merge_player_references(
					self._players_by_player_id[player.player_id],
					player,
				)
			else:
				self._players_by_player_id[player_id] = player

		if (
			player.name is not None and
			player.name != UNKNOWN_HUMAN_PLAYER and
			player.entity_id and
			player.player_id and
			player.player_id not in self._player_resolution_order
		):
			self._player_resolution_order.append(player.player_id)
		elif (
			player.name == UNKNOWN_HUMAN_PLAYER and
			player.entity_id is None and
			player.player_id is None and
			self._game_type != GameType.GT_BATTLEGROUNDS and
			len(self._player_resolution_order) < len(self._players_by_player_id)
		):
			unresolved_keys = [
				k for k in self._players_by_player_id.keys()
				if k not in self._player_resolution_order
			]

			if len(unresolved_keys) == 1:
				player = self._players_by_player_id[unresolved_keys[0]]

		return player

	@staticmethod
	def _safe_merge_player_references(left: PlayerReference, right: PlayerReference):
		if left.entity_id is None:
			if right.entity_id is not None:
				left.entity_id = right.entity_id
		elif right.entity_id is None:
			right.entity_id = left.entity_id
		else:
			assert left.entity_id == right.entity_id

		if left.player_id is None:
			if right.player_id is not None:
				left.player_id = right.player_id
		elif right.player_id is None:
			right.player_id = left.player_id
		else:
			assert left.player_id == right.player_id

		if left.name is None or left.name == UNKNOWN_HUMAN_PLAYER:
			if right.name is not None:
				left.name = right.name
		elif right.player_id is None or right.name == UNKNOWN_HUMAN_PLAYER:
			if left.name is not None:
				right.name = left.name

	def notify_first_player(self, entity_id: int):
		if entity_id in self._players_by_entity_id:
			first_player = self._players_by_entity_id[entity_id]
		else:
			first_player = PlayerReference(entity_id=entity_id)
			self._players_by_entity_id[entity_id] = first_player

		self.first_player = first_player

	def register_controller(self, entity_id: int, player_id: int):
		self._entity_controller_map[entity_id] = player_id

	def get_controller_by_entity_id(self, entity_id: int) -> Optional[int]:
		return self._entity_controller_map.get(entity_id)
