import time
from collections import deque
from threading import Thread

from hslog import packets, tokens
from hslog.live.packets import LivePacketTree
from hslog.parser import LogParser
from hslog.player import LazyPlayer, PlayerManager
from hslog.utils import parse_tag


class LiveLogParser(LogParser):

	def __init__(self, filepath):
		super(LiveLogParser, self).__init__()
		self.running = False
		self.filepath = filepath
		self.lines_deque = deque([])

	def new_packet_tree(self, ts):
		self._packets = LivePacketTree(ts, self)
		self._packets.spectator_mode = self.spectator_mode
		self._packets.manager = PlayerManager()
		self.current_block = self._packets
		self.games.append(self._packets)

		""" why is this return important? """
		return self._packets

	def tag_change(self, ts, e, tag, value, def_change):
		entity_id = self.parse_entity_or_player(e)
		tag, value = parse_tag(tag, value)
		self._check_for_mulligan_hack(ts, tag, value)

		""" skipping LazyPlayer here because it doesn"t have data """
		skip = False
		if isinstance(entity_id, LazyPlayer):
			entity_id = self._packets.manager.register_player_name_on_tag_change(
				entity_id, tag, value
			)
			skip = True
		has_change_def = def_change == tokens.DEF_CHANGE
		packet = packets.TagChange(ts, entity_id, tag, value, has_change_def)

		if not skip:
			self.register_packet(packet)
		return packet

	def register_packet(self, packet, node=None):
		""" make sure we"re registering packets to the current game"""
		if not self._packets or self._packets != self.games[-1]:
			self._packets = self.games[-1]

		if node is None:
			node = self.current_block.packets
		node.append(packet)

		""" line below triggers packet export which will
			run update_callback for entity being
			updated by the packet.

			self._packets == EntityTreeExporter
		"""
		self._packets.live_export(packet)

		self._packets._packet_counter += 1
		packet.packet_id = self._packets._packet_counter

	def file_worker(self):
		file = open(self.filepath, "r")
		while self.running:
			line = file.readline()
			if line:
				self.lines_deque.append(line)
			else:
				time.sleep(0.2)

	def parse_worker(self):
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
