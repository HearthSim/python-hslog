from hearthstone.enums import PowerType


class PacketTree:
	def __init__(self, ts):
		self.ts = ts
		self.packets = []
		self.parent = None
		self.packet_counter = 0

	def __iter__(self):
		for packet in self.packets:
			yield packet

	@property
	def start_time(self):
		for packet in self.packets:
			if packet.ts:
				return packet.ts

	@property
	def end_time(self):
		for packet in self.packets[::-1]:
			if packet.ts:
				return packet.ts

	def export(self, cls=None):
		if cls is None:
			from .export import EntityTreeExporter as cls
		exporter = cls(self)
		return exporter.export()

	def recursive_iter(self, cls=None):
		"""
		Iterate recursively over the PacketTree.
		Optional argument `cls` yields only packets of that instance.
		"""
		if cls is None:
			cls = Packet

		def _iter_recursive(packets, cls):
			for packet in packets:
				if isinstance(packet, cls):
					yield packet
				if isinstance(packet, Block):
					for p in _iter_recursive(packet.packets, cls):
						yield p

		for packet in _iter_recursive(self.packets, cls):
			yield packet


class Packet:
	power_type = 0

	def __repr__(self):
		return "<%s>" % self.__class__.__name__


class Block(Packet):
	power_type = PowerType.BLOCK_START

	def __init__(
		self, ts, entity, type, index, effectid, effectindex, target, suboption, trigger_keyword
	):
		self.ts = ts
		self.entity = entity
		self.type = type
		self.index = index
		self.effectid = effectid
		self.effectindex = effectindex
		self.target = target
		self.suboption = suboption
		self.trigger_keyword = trigger_keyword
		self.ended = False
		self.packets = []

	def __iter__(self):
		for packet in self.packets:
			yield packet

	def __repr__(self):
		return "%s(entity=%r, type=%r, index=%r, target=%r)" % (
			self.__class__.__name__, self.entity, self.type, self.index, self.target
		)

	def end(self):
		self.ended = True

	def _export(self, game):
		for packet in self.packets:
			packet._export(game)


class MetaData(Packet):
	power_type = PowerType.META_DATA

	def __init__(self, ts, meta, data, count):
		self.ts = ts
		self.meta = meta
		self.data = data
		self.count = count
		self.info = []

	def __repr__(self):
		return "%s(meta=%r, data=%r)" % (self.__class__.__name__, self.meta, self.data)


class CreateGame(Packet):
	power_type = PowerType.CREATE_GAME

	class Player(Packet):
		def __init__(self, ts, entity, player_id, hi, lo):
			self.ts = ts
			self.entity = entity
			self.player_id = player_id
			self.hi = hi
			self.lo = lo
			self.tags = []
			self.name = None

	def __init__(self, ts, entity):
		self.ts = ts
		self.entity = entity
		self.tags = []
		self.players = []


class HideEntity(Packet):
	power_type = PowerType.HIDE_ENTITY

	def __init__(self, ts, entity, zone):
		self.ts = ts
		self.entity = entity
		self.zone = zone


class FullEntity(Packet):
	power_type = PowerType.FULL_ENTITY

	def __init__(self, ts, entity, card_id):
		self.ts = ts
		self.entity = entity
		self.card_id = card_id
		self.tags = []


class ShowEntity(Packet):
	power_type = PowerType.SHOW_ENTITY

	def __init__(self, ts, entity, card_id):
		self.ts = ts
		self.entity = entity
		self.card_id = card_id
		self.tags = []

	def __repr__(self):
		return "%s(entity=%r, card_id=%r)" % (
			self.__class__.__name__, self.entity, self.card_id
		)


class ChangeEntity(Packet):
	power_type = PowerType.CHANGE_ENTITY

	def __init__(self, ts, entity, card_id):
		self.ts = ts
		self.entity = entity
		self.card_id = card_id
		self.tags = []


class TagChange(Packet):
	power_type = PowerType.TAG_CHANGE

	def __init__(self, ts, entity, tag, value, has_change_def=False):
		self.ts = ts
		self.entity = entity
		self.tag = tag
		self.value = value
		self.has_change_def = has_change_def


class Choices(Packet):
	def __init__(self, ts, entity, id, tasklist, type, min, max):
		self.ts = ts
		self.entity = entity
		self.id = id
		self.tasklist = tasklist
		self.type = type
		self.min = min
		self.max = max
		self.source = None
		self.choices = []

	@property
	def player(self):
		return self.entity


class SendChoices(Packet):
	def __init__(self, ts, id, type):
		self.ts = ts
		self.entity = None
		self.id = id
		self.type = type
		self.choices = []


class ChosenEntities(Packet):
	def __init__(self, ts, entity, id):
		self.ts = ts
		self.entity = entity
		self.id = id
		self.choices = []


class Options(Packet):
	def __init__(self, ts, id):
		self.ts = ts
		self.entity = None
		self.id = id
		self.options = []


class Option(Packet):
	def __init__(self, ts, entity, id, type, optype, error, error_param):
		self.ts = ts
		self.entity = entity
		self.id = id
		self.type = type
		self.optype = optype
		self.error = error
		self.error_param = error_param
		self.options = []


class SendOption(Packet):
	def __init__(self, ts, option, suboption, target, position):
		self.ts = ts
		self.entity = None
		self.option = option
		self.suboption = suboption
		self.target = target
		self.position = position


class ResetGame(Packet):
	def __init__(self, ts):
		self.ts = ts


class SubSpell(Packet):
	power_type = PowerType.SUB_SPELL_START

	def __init__(self, ts, spell_prefab_guid, source, target_count):
		self.ts = ts
		self.spell_prefab_guid = spell_prefab_guid
		self.source = source
		self.target_count = target_count
		self.ended = False
		self.targets = []
		self.packets = []

	def __repr__(self):
		return "%s(spell_prefab_guid=%r, source=%r)" % (
			self.__class__.__name__, self.spell_prefab_guid, self.source
		)

	def end(self):
		self.ended = True


class CachedTagForDormantChange(Packet):
	power_type = PowerType.CACHED_TAG_FOR_DORMANT_CHANGE

	def __init__(self, ts, entity, tag, value):
		self.ts = ts
		self.entity = entity
		self.tag = tag
		self.value = value


class VOSpell(Packet):
	power_type = PowerType.VO_SPELL

	def __init__(self, ts, brguid, vospguid, blocking, delayms):
		self.ts = ts
		self.brguid = brguid
		self.vospguid = vospguid
		self.blocking = blocking
		self.delayms = delayms


class ShuffleDeck(Packet):
	power_type = PowerType.SHUFFLE_DECK

	def __init__(self, ts, player_id):
		self.ts = ts
		self.player_id = player_id
