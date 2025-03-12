from hearthstone.enums import TAG_TYPES, GameTag, GameType

from hslog.exceptions import NoSuchEnum


def parse_enum(enum, value):
	if value.isdecimal():
		value = int(value)
	elif hasattr(enum, value):
		value = getattr(enum, value)
	else:
		raise NoSuchEnum(enum, value)
	return value


def parse_tag(tag, value):
	tag = parse_enum(GameTag, tag)
	if tag in TAG_TYPES:
		value = parse_enum(TAG_TYPES[tag], value)
	elif value.isdecimal():
		value = int(value)
	else:
		raise NotImplementedError("Invalid string value %r = %r" % (tag, value))
	return tag, value


def is_mercenaries_game_type(game_type: GameType):
	return game_type in (
		GameType.GT_MERCENARIES_AI_VS_AI,
		GameType.GT_MERCENARIES_FRIENDLY,
		GameType.GT_MERCENARIES_PVE_COOP,
		GameType.GT_MERCENARIES_PVE,
		GameType.GT_MERCENARIES_PVP,
	)
