from hearthstone.entities import Card, Game, Player, Entity
from hearthstone.enums import GameTag

'''
 * Card is called on export from game
 * LiveCard replaces Card and inserts update_callback
 * The point is to become able to route update events towards an API end-point
'''
class LiveEntity(Entity):
    
    def __init__(self, entity_id, parent, **kwargs):
        ''' Entity requires an ID, store everything else in kwargs '''
        self.parent = parent
        self.game_index = self.parent.parser.games.index(self.parent)
        super(LiveEntity, self).__init__(entity_id, **kwargs)
        
        # push data to an end-point
        print(f'GAME {self.game_index} --- ENTITY CREATED:', self)
    
    def tag_change(self, tag, value):
        if tag == GameTag.CONTROLLER and not self._initial_controller:
            self._initial_controller = self.tags.get(GameTag.CONTROLLER, value)
        self.tags[tag] = value
        
        # update notify
        self.update_callback()
    
    def update_callback(self):
        # push data to an end-point
        print(f'GAME {self.game_index} --- ENTITY UPDATED:', self)


class LiveCard(Card, LiveEntity):
   
    def __init__(self, entity_id, card_id, parent):
        super(LiveCard, self).__init__(
            entity_id=entity_id,
            card_id=card_id,
            parent=parent)

    ''' if card_id doesn't change, there's no need to pass it as the argument.
        we can use self.card_id instead as it is set by Card class '''
    def reveal(self, card_id, tags):
        self.revealed = True
        self.card_id = card_id
        if self.initial_card_id is None:
            self.initial_card_id = card_id
        self.tags.update(tags)
        
        # update notify
        self.update_callback()

    def hide(self):
        self.revealed = False
        
        # update notify
        self.update_callback()

    ''' same comment as for reveal '''
    def change(self, card_id, tags):
        if self.initial_card_id is None:
            self.initial_card_id = card_id
        self.card_id = card_id
        self.tags.update(tags)
        
        # update notify
        self.update_callback()
    