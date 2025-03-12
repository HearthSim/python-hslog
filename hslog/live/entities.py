from hearthstone.entities import Card, Entity, Game, Player
from hearthstone.enums import GameTag

from hslog.live.utils import terminal_output


class LiveEntity(Entity):

	def __init__(self, entity_id):
		super(LiveEntity, self).__init__(entity_id)
		self._game = None

	@property
	def game(self):
		return self._game

	@game.setter
	def game(self, value):
		# this happens when game calls register_entity and entity sets self.game
		self._game = value
		if value is not None:
			terminal_output("ENTITY CREATED", self)
			# push data to an end-point
			pass

	def tag_change(self, tag, value):
		if tag == GameTag.CONTROLLER and not self._initial_controller:
			self._initial_controller = self.tags.get(GameTag.CONTROLLER, value)
		self.tags[tag] = value
		terminal_output("TAG UPDATED", self, tag, value)
		# push data to an end-point
		pass

	def update_callback(self, caller):
		terminal_output("ENTITY UPDATED", self)
		# push data to an end-point
		pass


class LiveCard(Card, LiveEntity):
	"""
		Card is called on export from game
		LiveCard replaces Card and inserts update_callback
		The point is to become able to route update events towards an API end-point
	"""

	def __init__(self, entity_id, card_id):
		super(LiveCard, self).__init__(entity_id, card_id)

	"""
		if card_id doesn"t change, there"s no need to pass it as the argument.
		we can use self.card_id instead as it is set by Card class
	"""
	def reveal(self, card_id, tags):
		self.revealed = True
		self.card_id = card_id
		if self.initial_card_id is None:
			self.initial_card_id = card_id
		self.tags.update(tags)

		# update notify
		self.update_callback(self)

	def hide(self):
		self.revealed = False

		# update notify
		self.update_callback(self)

	""" same comment as for reveal """
	def change(self, card_id, tags):
		if self.initial_card_id is None:
			self.initial_card_id = card_id
		self.card_id = card_id
		self.tags.update(tags)

		# update notify
		self.update_callback(self)


class LivePlayer(Player, LiveEntity):

	def __init__(self, packet_id, player_id, hi, lo, name=None):
		super(LivePlayer, self).__init__(packet_id, player_id, hi, lo, name)


class LiveGame(Game, LiveEntity):

	def __init__(self, entity_id):
		super(LiveGame, self).__init__(entity_id)
