from collections.abc import Iterable
from typing import IO, List, Optional, Tuple, Union

from hearthstone.enums import GameTag

from hslog import tokens
from hslog.exceptions import RegexParsingError
from hslog.utils import parse_tag


# List of TAG_CHANGE tags to discard

BLACKLISTED_TAGS = [
    "EXHAUSTED",
    "FACTION",
    "HIDE_COST",
    "HIDE_WATERMARK",
    "NUM_ATTACKS_THIS_TURN",
    "NUM_TURNS_IN_PLAY",
    "TECH_LEVEL",
]

# List of FULL_ENTITY tags to discard

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

# List of SHOW_ENTITY tags to discard (in addition to BLACKLISTED_FULL_ENTITY_TAGS above)

BLACKLISTED_SHOW_ENTITY_TAGS = [
    GameTag.ENCHANTMENT_INVISIBLE
]


class Buffer:
    """Represents a sequence of buffered log lines that might be emitted or skipped.

    Buffers can be nested, such that the collection of buffered lines includes both strings
    and other Buffer instances. Output skipping should be applied hierarchically such that
    `should_skip` flag set on a "parent" Buffer should cause lines in any nested Buffers to
    be skipped, regardless of the value of that flag for those instances.
    """

    def __init__(self, buffer_type: str, subtype: str, parent: Optional["Buffer"] = None):
        """Ctor.

        :param buffer_type: the type of log element being buffered, e.g. "BLOCK_START"
        :param subtype: the subtype of log element being buffered, e.g. "ATTACK"
        :param: the parent Buffer instance, if any
        """

        self.buffer_type = buffer_type
        self.subtype = subtype
        self.buffer: List[Union[Buffer, str]] = []
        self.parent: Optional[Buffer] = parent
        self.should_skip = False


class BattlegroundsLogFilter(Iterable):
    """Iterable implementation that discards Battlegrounds log lines not needed for Tier7.

    Wrap this filter around the file-like object for a Battlegrounds log before passing it
    to the regular Hearthstone LogParser.

    The following log-skipping strategies are employed:

    - ATTACK blocks for minions that do not include interesting TRIGGER subblocks
        (such as those for DEATHRATTLEs) are discarded; ATTACK blocks for heroes will cause
        the next 4 blocks to be preserved, consistent with the logic for refreshing the
        `battlegrounds_combat_snapshot` materialized view
    - DEATHS blocks with no subblocks are discarded
    - All options messages (from DebugPrintOptions) are discarded
    - Blacklisted and unknown tags for FULL_ENTITY and SHOW_ENTITY messages are discarded
    - TAG_CHANGES containing blacklisted and unknown tags are discarded
    - All TAG_CHANGES that are part of a TRIGGER block that include a BOARD_VISUAL_STATE=2
        tag change are discarded
    - All TAG_CHANGES that precede a BOARD_VISUAL_STATE=1 tag change in a TRIGGER block are
        discarded
    """

    def __init__(self, fp: IO, show_suppressed_lines: bool = False):
        """Ctor.

        :param fp: the file-like object to be filtered
        :param show_suppressed_lines: whether to hide or show suppressed lines; when shown,
            suppressed lines are prefixed with "X: "
        """

        self._fp = fp
        self._preserve_block_counter = 0
        self._show_suppressed_lines = show_suppressed_lines

        self._current_buffer = None
        self._flushed_lines = []

        self.num_lines_read = 0
        self.num_lines_emitted = 0

    # Returns True if there's a current buffer which is buffering a FULL_ENTITY or
    # SHOW_ENTITY sequence of messages, False otherwise.

    def _buffering_entity(self) -> bool:
        return (
            self._current_buffer is not None and
            self._current_buffer.buffer_type in ["FULL_ENTITY", "SHOW_ENTITY"]
        )

    # Adds a line to the current buffer if it exists or to the outbound sequence of
    # "flushed" lines otherwise.

    def _emit_line(self, line):
        if self._current_buffer:
            self._current_buffer.buffer.append(line)
        else:
            self._flushed_lines.append(line)

    # Closes the current buffer sets the new current buffer to its parent. If the current
    # buffer had no parent, all non-skipped lines are recursively flushed to the flushed
    # lines list to be subsequently returned.

    def _end_buffer(self):
        if self._current_buffer:
            if self._current_buffer.parent is not None:
                self._current_buffer = self._current_buffer.parent
            else:
                buffer = self._current_buffer
                self._current_buffer = None
                self._flush_buffered_packets(buffer, should_skip=buffer.should_skip)

    # Recursively flushes buffered lines to the flushd lines list. If "should_skip" is True,
    # all lines in the current buffer and any nested buffers are suppressed, regardless of
    # their local "should_skip" flag.

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

    # Given the speciifed "opcode" (e.g., "BLOCK_START") and the following remainder of the
    # line, parse and return a Tuple of the block type (e.g., "ATTACK") and the card id of
    # the related entity.

    def _get_block_type_and_card_id(self, opcode, data) -> Tuple[str, str]:
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

    # Return the card id (if present) for the specified "entity string."

    @staticmethod
    def _get_card_id(entity: str) -> Optional[str]:
        card_id_index = entity.find("cardId=")
        if card_id_index < 0:
            return None

        card_id_index += 7
        following_space_index = entity.find(" ", card_id_index)
        return entity[card_id_index:following_space_index] \
            if following_space_index > card_id_index \
            else entity[card_id_index:]

    # Return a tuple of tag name and tag value from the specified log line.

    @staticmethod
    def _get_tag_change_tag_and_value(data) -> Tuple[str, str]:
        sre = tokens.TAG_CHANGE_RE.match(data)
        _e, tag, value, _def_change = sre.groups()
        return tag, value

    # Buffer or emit lines related to the specified BLOCK_END message.

    def _handle_block_end(self, line: str):

        # If we're buffering tag messages for a FULL_ENTITY / SHOW_ENTITY, flush them.

        if self._buffering_entity():
            self._end_buffer()

        self._emit_line(line)

        if self._current_buffer:
            self._end_buffer()

    # Buffer or emit lines related to the specified BLOCK_START message.

    def _handle_block_start(self, msg: str, line: str):

        # If we're buffering tag messages for a FULL_ENTITY / SHOW_ENTITY, flush them.

        if self._buffering_entity():
            self._end_buffer()

        block_type, card_id = self._get_block_type_and_card_id("BLOCK_START", msg)

        if self._current_buffer:

            # If we're already buffering an ATTACK block, check and see if this new block
            # is a TRIGGER related to something we care about, like a deathrattle. If so,
            # we should keep the outer block "alive."

            if self._current_buffer.subtype == "ATTACK":
                if block_type == "TRIGGER" and card_id != "TB_BaconShop_8P_PlayerE":
                    self._current_buffer.should_skip = False

            # If we're already buffering a DEATHS block, then any nested block (like this
            # one) should serve to preserve it.

            elif self._current_buffer.subtype == "DEATHS":
                self._current_buffer.should_skip = False

        if block_type == "ATTACK":

            # If the hero is attacking, preserve this block as well as the next 4 blocks -
            # there's a calculation in the materialized view update logic for
            # `battlegrounds_combat_snapshot` that expects a roughly 4-block gap between
            # a hero attacking and a hero death notification.

            if self._is_hero(card_id):
                self._preserve_block_counter = 4
            else:

                # Minion attacks aren't interesting unless they trigger something
                # interesting (see above)

                self._start_new_buffer("BLOCK", block_type)
                self._current_buffer.should_skip = True

        # Deaths aren't interesting unless they contain a nested block (see above)

        elif block_type == "DEATHS":
            self._start_new_buffer("BLOCK", block_type)
            self._current_buffer.should_skip = True

        # A TRIGGER block from the "8 player enchantment" might indicate a board state
        # reset that contains skippable stuff - see TAG_CHANGE logic below.

        elif block_type == "TRIGGER":
            if card_id == "TB_BaconShop_8P_PlayerE":
                self._start_new_buffer("BLOCK", block_type)

        if self._preserve_block_counter > 0:
            self._preserve_block_counter -= 1
            if self._current_buffer:
                self._current_buffer.should_skip = False

        self._emit_line(line)

    # Buffer or emit lines related to the specified FULL_ENTITY or SHOW_ENTITY message.

    def _handle_entity(self, opcode: str, line: str):

        # If we're buffering tag messages for a previous FULL_ENTITY / SHOW_ENTITY, flush
        # them.

        if self._buffering_entity():
            self._end_buffer()

        self._start_new_buffer(opcode, "")
        self._emit_line(line)

    # Buffer or emit lines related to the "initial atgs" attached to a previous FULL_ENTITY
    # or SHOW_ENTITY message.

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

                # Filter out all tags that we blacklist for FULL_ENTITY as well

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

    # Buffer or emit lines related to the specified TAG_CHANGE message.

    def _handle_tag_change(self, msg: str, line: str):

        # If we're buffering tag messages for a FULL_ENTITY / SHOW_ENTITY, flush them.

        if self._buffering_entity():
            self._end_buffer()

        tag, value = self._get_tag_change_tag_and_value(msg)

        # BOARD_VISUAL_STATE changes indicate that Battlegrounds is manipulating the shop.
        # If we're setting it to "1" we want to discard all previous TAG_CHANGEs that were
        # part of the same enclosing TRIGGER block. If we're setting it to "2" we want to
        # discard those TAG_CHANGEs as well as all subsequent TAG_CHANGEs.

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

    # Buffer or emit lines related to the specified option message.

    def _handle_options(self, level: str, ts: str, msg: str, line: str):
        if msg.startswith("id="):

            # This is the log filtering version of the "options hack" that the parser uses
            # to terminate dangling blocks for BGS games. Since we're suppressing options
            # lines, the parser won't know that it needs to use the hack, so instead we'll
            # need to emit a synthetic "BLOCK_END."

            block_end = f"{level} {ts} GameState.DebugPrintPower() - BLOCK_END\n"
            self._emit_line(block_end)
            self._end_buffer()

        if self._show_suppressed_lines:
            suppressed_line = "X: " + line
            self._flushed_lines.append(suppressed_line)

    # Predicate for detecting whether a specified card id is a BGS hero; this is a naive
    # implementation that may not work consistently!

    @staticmethod
    def _is_hero(card_id: str) -> bool:
        return card_id and "HERO" in card_id

    # Parse and return a tuple of tag and value for the specified log message corresponding
    # to the initial tags for a FULL_ENTITY or SHOW_ENTITY message.

    @staticmethod
    def _parse_initial_tag(data: str) -> Tuple[GameTag, str]:
        sre = tokens.TAG_VALUE_RE.match(data)
        if not sre:
            raise RegexParsingError(data)
        tag, value = sre.groups()
        return parse_tag(tag, value)

    # Start a new buffer with the specified buffer type and subtype and set it to be the new
    # "current buffer." Parent pointer and buffer nesting are updated as part of this.

    def _start_new_buffer(self, buffer_type: str, subtype: str):
        new_buffer = Buffer(buffer_type, subtype, parent=self._current_buffer)

        if self._current_buffer:
            self._current_buffer.buffer.append(new_buffer)

        self._current_buffer = new_buffer

    def __iter__(self):
        return self

    def __next__(self):
        while True:

            # First, return any lines that have been flushed to the flushed line list.

            if self._flushed_lines:
                self.num_lines_emitted += 1
                return self._flushed_lines.pop(0)

            line = self._fp.readline()
            if line == "":
                raise StopIteration()

            self.num_lines_read += 1

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
