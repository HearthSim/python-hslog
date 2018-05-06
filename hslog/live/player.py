from hearthstone.enums import GameTag

from hslog.exceptions import ParsingError
from hslog.player import PlayerManager


class LivePlayerManager(PlayerManager):

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
        elif tag == GameTag.MULLIGAN_STATE:
            return None
        return player
