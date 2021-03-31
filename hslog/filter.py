from typing import Optional, List, Union, IO

from hearthstone.enums import GameTag

from hslog import tokens
from hslog.exceptions import RegexParsingError
from hslog.utils import parse_tag

BLACKLISTED_TAGS = [
    "EXHAUSTED",
    "FACTION",
    "HIDE_COST",
    "HIDE_WATERMARK",
    "NUM_ATTACKS_THIS_TURN",
    "NUM_TURNS_IN_PLAY",
    "TECH_LEVEL",
]

BLACKLISTED_FULL_ENTITY_TAGS = [
    GameTag.BACON_ACTION_CARD,
    GameTag.BATTLECRY,
    GameTag.CARDRACE,
    GameTag.COST,
    GameTag.EXHAUSTED,
    GameTag.FACTION,
    GameTag.GAME_MODE_BUTTON_SLOT,
    GameTag.HIDE_WATERMARK,
    GameTag.IS_BACON_POOL_MINION,
    GameTag.MODULAR,
    GameTag.MOVE_MINION_HOVER_TARGET_SLOT,
    GameTag.OVERKILL,
    GameTag.RARITY,
    GameTag.SPAWN_TIME_COUNT,
    GameTag.SUPPRESS_ALL_SUMMON_VO,
    GameTag.TAG_LAST_KNOWN_COST_IN_HAND,
    GameTag.TAG_SCRIPT_DATA_NUM_1,
    GameTag.TAG_SCRIPT_DATA_NUM_2,
    GameTag.TECH_LEVEL,
    GameTag.TRIGGER_VISUAL
]

BLACKLISTED_SHOW_ENTITY_TAGS = [
    GameTag.ENCHANTMENT_INVISIBLE
]


class Buffer:
    def __init__(self, buffer_type: str, subtype: str, parent: Optional["Buffer"] = None):
        self.buffer_type = buffer_type
        self.subtype = subtype
        self.buffer: List[Union[Buffer, str]] = []
        self.parent: Optional[Buffer] = parent
        self.should_skip = False


class BattlegroundsLogFilter:

    def __init__(self, fp: IO, show_suppressed_lines: bool = False):
        self._fp = fp
        self._preserve_block_counter = 0
        self._show_suppressed_lines = show_suppressed_lines

        self._current_buffer = None
        self._flushed_lines = []

    def _buffering_entity(self):
        return (
            self._current_buffer is not None and
            self._current_buffer.buffer_type in ["FULL_ENTITY", "SHOW_ENTITY"]
        )

    def _emit_line(self, line):
        if self._current_buffer:
            self._current_buffer.buffer.append(line)
        else:
            self._flushed_lines.append(line)

    def _end_buffer(self):
        if self._current_buffer:
            if self._current_buffer.parent is not None:
                self._current_buffer = self._current_buffer.parent
            else:
                buffer = self._current_buffer
                self._current_buffer = None
                self._flush_buffered_packets(buffer, should_skip=buffer.should_skip)

    def _flush_buffered_packets(self, buffer: Buffer, should_skip: bool = False):
        for buffered_item in buffer.buffer:
            if isinstance(buffered_item, Buffer):
                eff_should_skip = should_skip or buffered_item.should_skip
                self._flush_buffered_packets(buffered_item, should_skip=eff_should_skip)
            else:
                if should_skip:
                    if self._show_suppressed_lines:
                        self._flushed_lines.append("X: " + buffered_item)
                else:
                    self._flushed_lines.append(buffered_item)

    def _get_block_type_and_card_id(self, opcode, data):
        _index = None
        _effectid, _effectindex = None, None
        _suboption, _trigger_keyword = None, None
        if " SubOption=" in data:
            if " TriggerKeyword=" in data:
                sre = tokens.BLOCK_START_20457_TRIGGER_KEYWORD_RE.match(data)
                if sre is None:
                    raise RegexParsingError(data)
                block_type, entity, _effectid, _effectindex, target, _suboption, \
                    _trigger_keyword = sre.groups()
            else:
                sre = tokens.BLOCK_START_20457_RE.match(data)
                if sre is None:
                    raise RegexParsingError(data)
                block_type, entity, _effectid, _effectindex, target, \
                    _suboption = sre.groups()
        else:
            if opcode == "ACTION_START":
                sre = tokens.ACTION_START_RE.match(data)
            else:
                sre = tokens.BLOCK_START_12051_RE.match(data)

            if sre is None:
                sre = tokens.ACTION_START_OLD_RE.match(data)
                if not sre:
                    raise RegexParsingError(data)
                entity, block_type, _index, target = sre.groups()
            else:
                block_type, entity, _effectid, _effectindex, target = sre.groups()

        return block_type, self._get_card_id(entity)

    @staticmethod
    def _get_card_id(entity: str):
        card_id_index = entity.find("cardId=")
        if card_id_index < 0:
            return None

        card_id_index += 7
        following_space_index = entity.find(" ", card_id_index)
        return entity[card_id_index:following_space_index] \
            if following_space_index > card_id_index \
            else entity[card_id_index:]

    @staticmethod
    def _get_tag_change_tag_and_value(data):
        sre = tokens.TAG_CHANGE_RE.match(data)
        _e, tag, value, _def_change = sre.groups()
        return tag, value

    def _handle_block_end(self, line: str):
        if self._buffering_entity():
            self._end_buffer()

        self._emit_line(line)

        if self._current_buffer:
            self._end_buffer()

    def _handle_block_start(self, msg: str, line: str):
        if self._buffering_entity():
            self._end_buffer()

        block_type, card_id = self._get_block_type_and_card_id("BLOCK_START", msg)

        if self._current_buffer:
            if self._current_buffer.subtype == "ATTACK":
                if block_type == "TRIGGER" and card_id != "TB_BaconShop_8P_PlayerE":
                    self._current_buffer.should_skip = False
            elif self._current_buffer.subtype == "DEATHS":
                self._current_buffer.should_skip = False

        if block_type == "ATTACK":
            if self._is_hero(card_id):
                self._preserve_block_counter = 4
            else:
                self._start_new_buffer("BLOCK", block_type)
                self._current_buffer.should_skip = True
        elif block_type == "DEATHS":
            self._start_new_buffer("BLOCK", block_type)
            self._current_buffer.should_skip = True
        elif block_type == "TRIGGER":
            if card_id == "TB_BaconShop_8P_PlayerE":
                self._start_new_buffer("BLOCK", block_type)

        if self._preserve_block_counter > 0:
            self._preserve_block_counter -= 1
            if self._current_buffer:
                self._current_buffer.should_skip = False

        self._emit_line(line)

    def _handle_entity(self, opcode: str, line: str):
        if self._buffering_entity():
            self._end_buffer()

        self._start_new_buffer(opcode, "")
        self._emit_line(line)

    def _handle_entity_tag(self, msg: str, line: str):
        tag, value = self._parse_initial_tag(msg)

        if self._buffering_entity():
            if self._current_buffer.buffer_type == "FULL_ENTITY":
                if tag in BLACKLISTED_FULL_ENTITY_TAGS:
                    self._start_new_buffer("__ENTITY_TAG", "")
                    self._current_buffer.should_skip = True
                    self._emit_line(line)
                    self._end_buffer()
                else:
                    self._emit_line(line)
            elif self._current_buffer.buffer_type == "SHOW_ENTITY":
                if (
                        tag in BLACKLISTED_FULL_ENTITY_TAGS or
                        tag in BLACKLISTED_SHOW_ENTITY_TAGS
                ):
                    self._start_new_buffer("__ENTITY_TAG", "")
                    self._current_buffer.should_skip = True
                    self._emit_line(line)
                    self._end_buffer()
                else:
                    self._emit_line(line)
            else:
                self._emit_line(line)
        else:
            self._emit_line(line)

    def _handle_tag_change(self, msg: str, line: str):
        if self._buffering_entity():
            self._end_buffer()

        tag, value = self._get_tag_change_tag_and_value(msg)

        if (
                self._current_buffer and
                self._current_buffer.subtype == "TRIGGER" and
                tag == "BOARD_VISUAL_STATE"
        ):
            self._current_buffer.buffer.append(line)

            if value == "1" or value == "2":
                for i in range(len(self._current_buffer.buffer)):
                    buffered_item = self._current_buffer.buffer[i]
                    if (
                            isinstance(buffered_item, str) and
                            "TAG_CHANGE" in buffered_item
                    ):
                        buf = Buffer("TAG_CHANGE", "", parent=self._current_buffer)
                        buf.buffer.append(buffered_item)
                        buf.should_skip = True
                        self._current_buffer.buffer[i] = buf

                if value == "2":
                    setattr(self._current_buffer, "skip_tag_changes", True)

                return

        if (
                tag.isdigit() or
                tag in BLACKLISTED_TAGS or
                (
                        self._current_buffer is not None and
                        hasattr(self._current_buffer, "skip_tag_changes")
                )
        ):
            self._start_new_buffer("TAG_CHANGE", "")
            self._current_buffer.should_skip = True
            self._emit_line(line)
            self._end_buffer()
        else:
            self._emit_line(line)

    def _handle_options(self, level: str, ts: str, msg: str, line: str):
        if msg.startswith("id="):
            block_end = f"{level} {ts} GameState.DebugPrintPower() - BLOCK_END\n"
            self._emit_line(block_end)
            self._end_buffer()

        if self._show_suppressed_lines:
            suppressed_line = "X: " + line
            if self._flushed_lines:
                self._flushed_lines.append(suppressed_line)
            else:
                return suppressed_line

    @staticmethod
    def _is_hero(card_id):
        return card_id and "HERO" in card_id

    @staticmethod
    def _parse_initial_tag(data):
        sre = tokens.TAG_VALUE_RE.match(data)
        if not sre:
            raise RegexParsingError(data)
        tag, value = sre.groups()
        return parse_tag(tag, value)

    def _start_new_buffer(self, buffer_type: str, subtype: str):
        new_buffer = Buffer(buffer_type, subtype, parent=self._current_buffer)

        if self._current_buffer:
            self._current_buffer.buffer.append(new_buffer)

        self._current_buffer = new_buffer

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self._flushed_lines:
                return self._flushed_lines.pop(0)

            line = self._fp.readline()
            if line == "":
                raise StopIteration()

            sre = tokens.TIMESTAMP_RE.match(line)
            if not sre:
                raise RegexParsingError(line)

            level, ts, line_rest = sre.groups()
            if line_rest.startswith(tokens.SPECTATOR_MODE_TOKEN):
                self._emit_line(line)
                continue

            sre = tokens.POWERLOG_LINE_RE.match(line_rest)
            if not sre:
                self._emit_line(line)
                continue

            method, msg = sre.groups()
            msg = msg.strip()

            if method == "GameState.DebugPrintPower":
                opcode = msg.split()[0]

                if opcode == "BLOCK_START":
                    self._handle_block_start(msg, line)
                elif opcode == "BLOCK_END":
                    self._handle_block_end(line)
                elif opcode in ["FULL_ENTITY", "SHOW_ENTITY"]:
                    self._handle_entity(opcode, line)
                elif opcode.startswith("tag="):
                    self._handle_entity_tag(msg, line)
                elif opcode == "TAG_CHANGE":
                    self._handle_tag_change(msg, line)
                else:
                    self._emit_line(line)

            elif method == "GameState.DebugPrintOptions":
                self._handle_options(level, ts, msg, line)
            else:
                self._emit_line(line)
