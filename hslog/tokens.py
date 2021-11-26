import re


# Entity format
GAME_ENTITY = "GameEntity"
UNKNOWN_HUMAN_PLAYER = "UNKNOWN HUMAN PLAYER"
_E = r"(%s|%s|\[.+\]|\d+|.+)" % (GAME_ENTITY, UNKNOWN_HUMAN_PLAYER)
ENTITY_RE = re.compile(r"\[.*\s*id=(\d+)\s*.*\]")

# Line format
TIMESTAMP_POWERLOG_FORMAT = r"%H:%M:%S.%f"
TIMESTAMP_RE = re.compile(r"^([DWE]) ([\d:.]+) (.+)$")
POWERLOG_LINE_RE = re.compile(r"([^(]+)\(\) - (.+)$")

# Game / Player
GAME_ENTITY_RE = re.compile(r"GameEntity EntityID=(\d+)")
PLAYER_ENTITY_RE = re.compile(r"Player EntityID=(\d+) PlayerID=(\d+) GameAccountId=\[hi=(\d+) lo=(\d+)\]$")

# Messages
CREATE_GAME_RE = re.compile(r"^CREATE_GAME$")
ACTION_START_OLD_RE = re.compile(r"ACTION_START Entity=%s (?:SubType|BlockType)=(\w+) Index=(-1|\d+) Target=%s$" % (_E, _E))
ACTION_START_RE = re.compile(r"ACTION_START SubType=(\w+) Entity=%s EffectCardId=(.*) EffectIndex=(-1|\d+) Target=%s$" % (_E, _E))
BLOCK_START_12051_RE = re.compile(r"BLOCK_START BlockType=(\w+) Entity=%s EffectCardId=(.*) EffectIndex=(-1|\d+) Target=%s$" % (_E, _E))
BLOCK_START_20457_RE = re.compile(r"BLOCK_START BlockType=(\w+) Entity=%s EffectCardId=(.*) EffectIndex=(-1|\d+) Target=%s SubOption=(-1|\d+)$" % (_E, _E))
BLOCK_START_20457_TRIGGER_KEYWORD_RE = re.compile(r"BLOCK_START BlockType=(\w+) Entity=%s EffectCardId=(.*) EffectIndex=(-1|\d+) Target=%s SubOption=(-1|\d+) TriggerKeyword=(\w+)$" % (_E, _E))
BLOCK_END_RE = re.compile(r"^(?:ACTION|BLOCK)_END$")
FULL_ENTITY_CREATE_RE = re.compile(r"FULL_ENTITY - Creating ID=(\d+) CardID=(\w+)?$")
FULL_ENTITY_UPDATE_RE = re.compile(r"FULL_ENTITY - Updating %s CardID=(\w+)?$" % _E)
SHOW_ENTITY_RE = re.compile(r"SHOW_ENTITY - Updating Entity=%s CardID=(\w+)$" % _E)
HIDE_ENTITY_RE = re.compile(r"HIDE_ENTITY - Entity=%s tag=(\w+) value=(\w+)$" % _E)
CHANGE_ENTITY_RE = re.compile(r"CHANGE_ENTITY - Updating Entity=%s CardID=(\w+)$" % _E)
DEF_CHANGE = "DEF CHANGE"
TAG_CHANGE_RE = re.compile(r"TAG_CHANGE Entity=%s tag=(\w+) value=(\w+) ?(%s)?" % (_E, DEF_CHANGE))
META_DATA_RE = re.compile(r"META_DATA - Meta=(\w+) Data=%s InfoCount=(\d+)" % _E)
RESET_GAME_RE = re.compile(r"RESET_GAME$")
SUB_SPELL_START_RE = re.compile(r"SUB_SPELL_START - SpellPrefabGUID=([\w:.()]+) Source=(\d+) TargetCount=(\d+)$")
SUB_SPELL_END_RE = re.compile(r"SUB_SPELL_END$")
CACHED_TAG_FOR_DORMANT_CHANGE_RE = re.compile(r"CACHED_TAG_FOR_DORMANT_CHANGE Entity=%s tag=(\w+) value=(\w+)" % _E)
VO_SPELL_RE = re.compile(r"VO_SPELL - BrassRingGuid=(.*) - VoSpellPrefabGUID=(\w*)? - Blocking=(True|False) - AdditionalDelayInMs=(\d+)$")
SHUFFLE_DECK_RE = re.compile(r"SHUFFLE_DECK PlayerID=(\d+)$")

# Message details
TAG_VALUE_RE = re.compile(r"tag=(\w+) value=(\w+)")
METADATA_INFO_RE = re.compile(r"Info\[(\d+)\] = %s" % _E)
SUB_SPELL_START_SOURCE_RE = re.compile(r"Source = %s" % _E)
SUB_SPELL_START_TARGETS_RE = re.compile(r"Targets\[(\d+)\] = %s" % _E)

# Game
GAME_PLAYER_META = re.compile(r"PlayerID=(\d+), PlayerName=(.*)")

# Choices
CHOICES_CHOICE_OLD_1_RE = re.compile(r"id=(\d+) ChoiceType=(\w+)$")
CHOICES_CHOICE_OLD_2_RE = re.compile(r"id=(\d+) PlayerId=(\d+) ChoiceType=(\w+) CountMin=(\d+) CountMax=(\d+)$")
CHOICES_CHOICE_RE = re.compile(r"id=(\d+) Player=%s TaskList=(\d+)? ChoiceType=(\w+) CountMin=(\d+) CountMax=(\d+)$" % _E)
CHOICES_SOURCE_RE = re.compile(r"Source=%s$" % _E)
CHOICES_ENTITIES_RE = re.compile(r"Entities\[(\d+)\]=(\[.+\])$")
SEND_CHOICES_CHOICE_RE = re.compile(r"id=(\d+) ChoiceType=(.+)$")
SEND_CHOICES_ENTITIES_RE = re.compile(r"m_chosenEntities\[(\d+)\]=(\[.+\])$")
ENTITIES_CHOSEN_RE = re.compile(r"id=(\d+) Player=%s EntitiesCount=(\d+)$" % _E)
ENTITIES_CHOSEN_ENTITIES_RE = re.compile(r"Entities\[(\d+)\]=%s$" % _E)

# Options
OPTIONS_ENTITY_RE = re.compile(r"id=(\d+)$")
OPTIONS_OPTION_RE = re.compile(r"(option) (\d+) type=(\w+) mainEntity=%s?$" % _E)
OPTIONS_OPTION_ERROR_RE = re.compile(r"(option) (\d+) type=(\w+) mainEntity=%s? error=(\w+) errorParam=(\d+)?$" % _E)
OPTIONS_SUBOPTION_RE = re.compile(r"(subOption|target) (\d+) entity=%s?$" % _E)
OPTIONS_SUBOPTION_ERROR_RE = re.compile(r"(subOption|target) (\d+) entity=%s? error=(\w+) errorParam=(\d+)?$" % _E)
SEND_OPTION_RE = re.compile(r"selectedOption=(\d+) selectedSubOption=(-1|\d+) selectedTarget=(\d+) selectedPosition=(\d+)")

# Spectator mode
SPECTATOR_MODE_TOKEN = "=================="
SPECTATOR_MODE_BEGIN_GAME = "Start Spectator Game"
SPECTATOR_MODE_BEGIN_FIRST = "Begin Spectating 1st player"
SPECTATOR_MODE_BEGIN_SECOND = "Begin Spectating 2nd player"
SPECTATOR_MODE_END_MODE = "End Spectator Mode"
SPECTATOR_MODE_END_GAME = "End Spectator Game"
