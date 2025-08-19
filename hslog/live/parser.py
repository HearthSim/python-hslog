import time
from collections import deque
from threading import Thread

from hslog import packets, tokens
from hslog.exceptions import RegexParsingError
from hslog.live.packets import LivePacketTree
from hslog.live.player import LivePlayerManager
from hslog.parser import LogParser
from hslog.player import LazyPlayer
from hslog.utils import parse_tag


class LiveLogParser(LogParser):
	"""
		LiveLogParser provides live log translation into useful data.

		Lines are read and pushed into a deque by a separate thread.
		Deque is emptied by parse_worker which replaces the read()
		function of LogParser and it"s also in a separate thread.

		This approach is non-blocking and allows for live parsing
		of incoming lines.
	"""

	def __init__(self, filepath):
		super(LiveLogParser, self).__init__()
		self.running = False
		self.filepath = filepath
		self.lines_deque = deque([])

	def new_packet_tree(self, ts):
		"""
			LivePacketTree is introduced here because it instantiates LiveEntityTreeExporter
			and keeps track of the parser parent. It also contains a function that
			utilizes the liveExporter instance across all the games.

			self.parser = parser
			self.liveExporter = LiveEntityTreeExporter(self)
		"""
		self._packets = LivePacketTree(ts, self)
		self._packets.spectator_mode = self.spectator_mode
		self._packets.manager = LivePlayerManager()
		self.current_block = self._packets
		self.games.append(self._packets)

	def handle_entities_chosen(self, ts, data):
		super(LiveLogParser, self).handle_entities_chosen(ts, data)
		if data.startswith("id="):
			sre = tokens.ENTITIES_CHOSEN_RE.match(data)
			if not sre:
				raise RegexParsingError(data)
			player_name = sre.groups()[1]

			# pick up opponent name from GameState.DebugPrintEntitiesChosen()
			m = self._packets.manager
			m.complete_player_names(player_name, self._packets)

	def handle_game(self, ts, data):
		if data.startswith("PlayerID="):
			sre = tokens.GAME_PLAYER_META.match(data)
			if not sre:
				raise RegexParsingError(data)
			player_id, player_name = sre.groups()

			# set initial name based on GameState.DebugPrintGame()
			m = self._packets.manager
			m.set_initial_player_name(player_id, player_name, self._packets)

			player_id = int(player_id)
		else:
			super(LiveLogParser, self).handle_game(ts, data)

	def tag_change(self, ts, e, tag, value, def_change):
		entity_id = self.parse_entity_or_player(e)
		tag, value = parse_tag(tag, value)
		self._check_for_mulligan_hack(ts, tag, value)

		if isinstance(entity_id, LazyPlayer):
			entity_id = self._packets.manager.register_player_name_on_tag_change(
				entity_id, tag, value)

		has_change_def = def_change == tokens.DEF_CHANGE
		packet = packets.TagChange(ts, entity_id, tag, value, has_change_def)
		if entity_id:
			self.register_packet(packet)
		return packet

	def register_packet(self, packet, node=None):
		"""
			LogParser.register_packet override

			This uses the live_export functionality introduces by LivePacketTree
			It also keeps track of which LivePacketTree is being used when there
			are multiple in parser.games

			A better naming for a PacketTree/LivePacketTree would be HearthstoneGame?
			Then parser.games would contain HearthstoneGame instances and would
			be more obvious what the purpose is.
		"""

		# make sure we"re registering packets to the current game
		if not self._packets or self._packets != self.games[-1]:
			self._packets = self.games[-1]

		if node is None:
			node = self.current_block.packets
		node.append(packet)
		self._packets._packet_counter += 1
		packet.packet_id = self._packets._packet_counter
		self._packets.live_export(packet)

	def file_worker(self):
		"""
			File reader thread. (Naive implementation)
			Reads the log file continuously and appends to deque.
		"""

		file = open(self.filepath, "r")
		while self.running:
			line = file.readline()
			if line:
				self.lines_deque.append(line)
			else:
				time.sleep(0.2)

	def parse_worker(self):
		"""
			If deque contains lines, this initiates parsing.
		"""
		while self.running:
			if len(self.lines_deque):
				line = self.lines_deque.popleft()
				self.read_line(line)
			else:
				time.sleep(0.2)

	def start_file_worker(self):
		file_thread = Thread(target=self.file_worker)
		file_thread.setDaemon(True)
		file_thread.start()

	def start_parse_worker(self):
		parse_thread = Thread(target=self.parse_worker)
		parse_thread.setDaemon(True)
		parse_thread.start()

	def start(self):
		self.running = True
		self.start_file_worker()
		self.start_parse_worker()

	def stop(self):
		self.running = False
