from hearthstone.enums import GameTag

from hslog.player import PlayerManager


class LivePlayerManager(PlayerManager):

	def __init__(self):
		super(LivePlayerManager, self).__init__()

		self.actual_player_names = set()
		self.names_used = set()
		self.name_assignment_done = False

	def register_player_name_on_tag_change(self, player, tag, value):
		if tag not in [GameTag.ENTITY_ID, GameTag.LAST_CARD_PLAYED]:
			return None
		super(LivePlayerManager, self).register_player_name_on_tag_change(player, tag, value)

	def set_initial_player_name(self, player_id, player_name, current_game):
		players = current_game.liveExporter.game.players
		for p in players:
			if p.player_id == int(player_id):
				p.name = player_name

	def complete_player_names(self, player_name, current_game):
		# populate names if they haven"t been used already
		if player_name not in self.names_used:
			self.actual_player_names.add(player_name)

		# if there are two names available we have enough to assign
		if len(self.actual_player_names) == 2 and not self.name_assignment_done:
			unnamed = None
			for p in current_game.liveExporter.game.players:
				if p.name in self.actual_player_names:
					self.names_used.add(p.name)
					self.actual_player_names.remove(p.name)
				else:
					unnamed = p
			if len(self.actual_player_names):
				other_player_name = self.actual_player_names.pop()
				self.names_used.add(other_player_name)
				unnamed.name = other_player_name
				
			self.name_assignment_done = True
