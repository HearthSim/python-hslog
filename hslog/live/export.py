from hearthstone.enums import GameTag

from hslog.export import EntityTreeExporter
from hslog.live.entities import LiveCard, LiveGame, LivePlayer


class LiveEntityTreeExporter(EntityTreeExporter):
	"""
		Inherits EntityTreeExporter to provide Live entities
	"""

	game_class = LiveGame
	player_class = LivePlayer
	card_class = LiveCard

	def __init__(self, packet_tree):
		super(LiveEntityTreeExporter, self).__init__(packet_tree)

	def handle_player(self, packet):
		entity_id = int(packet.entity)

		if hasattr(self.packet_tree, "manager"):
			# If we have a PlayerManager, first we mutate the CreateGame.Player packet.
			# This will have to change if we"re ever able to immediately get the names.
			player = self.packet_tree.manager.get_player_by_id(entity_id)
			packet.name = player.name
		entity = self.player_class(entity_id, packet.player_id, packet.hi, packet.lo, packet.name)
		entity.tags = dict(packet.tags)
		self.game.register_entity(entity)
		entity.initial_hero_entity_id = entity.tags.get(GameTag.HERO_ENTITY, 0)
		return entity
