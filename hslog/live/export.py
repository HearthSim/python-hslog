from hslog.export import EntityTreeExporter
from hslog.live.entities import LiveCard


class LiveEntityTreeExporter(EntityTreeExporter):
    card_class = LiveCard
    
    def __init__(self, packet_tree):
        super(LiveEntityTreeExporter, self).__init__(packet_tree)
        
    def handle_full_entity(self, packet):
        entity_id = packet.entity

        # Check if the entity already exists in the game first.
        # This prevents creating it twice.
        # This can legitimately happen in case of GAME_RESET
        if entity_id <= len(self.game.entities):
            # That first if check is an optimization to prevent always looping over all of
            # the game's entities every single FULL_ENTITY packet...
            # FIXME: Switching to a dict for game.entities would simplify this.
            existing_entity = self.game.find_entity_by_id(entity_id)
            if existing_entity is not None:
                existing_entity.card_id = packet.card_id
                existing_entity.tags = dict(packet.tags)
                return existing_entity

        entity = self.card_class(entity_id, packet.card_id, self.packet_tree)
        entity.tags = dict(packet.tags)
        self.game.register_entity(entity)
        return entity