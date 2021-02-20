import time

from hslog.export import BaseExporter, CompositeExporter, FriendlyPlayerExporter
from hslog.packets import Block, SubSpell

from .conftest import logfile


class LoggingExporter(BaseExporter):

	def __init__(self, packet_tree):
		super().__init__(packet_tree)

		self.flush_calls = 0
		self.handle_block_calls = 0
		self.handle_cached_tag_for_dormant_change_calls = 0
		self.handle_chosen_entities_calls = 0
		self.handle_choices_calls = 0
		self.handle_change_entity_calls = 0
		self.handle_create_game_calls = 0
		self.handle_full_entity_calls = 0
		self.handle_hide_entity_calls = 0
		self.handle_metadata_calls = 0
		self.handle_option_calls = 0
		self.handle_options_calls = 0
		self.handle_player_calls = 0
		self.handle_reset_game_calls = 0
		self.handle_send_choices_calls = 0
		self.handle_send_option_calls = 0
		self.handle_show_entity_calls = 0
		self.handle_shuffle_deck_calls = 0
		self.handle_sub_spell_calls = 0
		self.handle_tag_change_calls = 0
		self.handle_vo_spell_calls = 0

	def flush(self):
		super().flush()

		self.flush_calls += 1

	def handle_block(self, packet):
		super().handle_block(packet)

		self.handle_block_calls += 1

	def handle_cached_tag_for_dormant_change(self, packet):
		self.handle_cached_tag_for_dormant_change_calls += 1

	def handle_chosen_entities(self, packet):
		self.handle_chosen_entities_calls += 1

	def handle_choices(self, packet):
		self.handle_choices_calls += 1

	def handle_change_entity(self, packet):
		self.handle_change_entity_calls += 1

	def handle_create_game(self, packet):
		self.handle_create_game_calls += 1

	def handle_full_entity(self, packet):
		self.handle_full_entity_calls += 1

	def handle_hide_entity(self, packet):
		self.handle_hide_entity_calls += 1

	def handle_metadata(self, packet):
		self.handle_metadata_calls += 1

	def handle_option(self, packet):
		self.handle_option_calls += 1

	def handle_options(self, packet):
		self.handle_options_calls += 1

	def handle_player(self, packet):
		self.handle_player_calls += 1

	def handle_reset_game(self, packet):
		self.handle_reset_game_calls += 1

	def handle_send_choices(self, packet):
		self.handle_send_choices_calls += 1

	def handle_send_option(self, packet):
		self.handle_send_option_calls += 1

	def handle_show_entity(self, packet):
		self.handle_show_entity_calls += 1

	def handle_shuffle_deck(self, packet):
		self.handle_shuffle_deck_calls += 1

	def handle_sub_spell(self, packet):
		super().handle_sub_spell(packet)

		self.handle_sub_spell_calls += 1

	def handle_tag_change(self, packet):
		self.handle_tag_change_calls += 1

	def handle_vo_spell(self, packet):
		self.handle_vo_spell_calls += 1


class TestCompositeExporter:

	def test_flush(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.flush()

		assert exporter1.flush_calls == 1
		assert exporter2.flush_calls == 1

	def test_handle_block(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_block(Block(time.time(), 0, 0, 0, 0, 0, 0, 0, 0))

		assert exporter1.handle_block_calls == 1
		assert exporter2.handle_block_calls == 1

	def test_handle_cached_tag_for_dormant_change(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_cached_tag_for_dormant_change(None)

		assert exporter1.handle_cached_tag_for_dormant_change_calls == 1
		assert exporter2.handle_cached_tag_for_dormant_change_calls == 1

	def test_handle_chosen_entities(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_chosen_entities(None)

		assert exporter1.handle_chosen_entities_calls == 1
		assert exporter2.handle_chosen_entities_calls == 1

	def test_handle_choices(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_choices(None)

		assert exporter1.handle_choices_calls == 1
		assert exporter2.handle_choices_calls == 1

	def test_handle_change_entity(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_change_entity(None)

		assert exporter1.handle_change_entity_calls == 1
		assert exporter2.handle_change_entity_calls == 1

	def test_handle_create_game(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_create_game(None)

		assert exporter1.handle_create_game_calls == 1
		assert exporter2.handle_create_game_calls == 1

	def test_handle_full_entity(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_full_entity(None)

		assert exporter1.handle_full_entity_calls == 1
		assert exporter2.handle_full_entity_calls == 1

	def test_handle_hide_entity(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_hide_entity(None)

		assert exporter1.handle_hide_entity_calls == 1
		assert exporter2.handle_hide_entity_calls == 1

	def test_handle_metadata(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_metadata(None)

		assert exporter1.handle_metadata_calls == 1
		assert exporter2.handle_metadata_calls == 1

	def test_handle_option(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_option(None)

		assert exporter1.handle_option_calls == 1
		assert exporter2.handle_option_calls == 1

	def test_handle_options(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_options(None)

		assert exporter1.handle_options_calls == 1
		assert exporter2.handle_options_calls == 1

	def test_handle_player(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_player(None)

		assert exporter1.handle_player_calls == 1
		assert exporter2.handle_player_calls == 1

	def test_handle_reset_game(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_reset_game(None)

		assert exporter1.handle_reset_game_calls == 1
		assert exporter2.handle_reset_game_calls == 1

	def test_handle_send_choices(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_send_choices(None)

		assert exporter1.handle_send_choices_calls == 1
		assert exporter2.handle_send_choices_calls == 1

	def test_handle_send_option(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_send_option(None)

		assert exporter1.handle_send_option_calls == 1
		assert exporter2.handle_send_option_calls == 1

	def test_handle_show_entity(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_show_entity(None)

		assert exporter1.handle_show_entity_calls == 1
		assert exporter2.handle_show_entity_calls == 1

	def test_handle_shuffle_deck(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_shuffle_deck(None)

		assert exporter1.handle_shuffle_deck_calls == 1
		assert exporter2.handle_shuffle_deck_calls == 1

	def test_handle_sub_spell(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_sub_spell(SubSpell(time.time(), None, 0, 0))

		assert exporter1.handle_sub_spell_calls == 1
		assert exporter2.handle_sub_spell_calls == 1

	def test_handle_tag_change(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_tag_change(None)

		assert exporter1.handle_tag_change_calls == 1
		assert exporter2.handle_tag_change_calls == 1

	def test_handle_vo_spell(self):
		exporter1 = LoggingExporter(None)
		exporter2 = LoggingExporter(None)

		composite_exporter = CompositeExporter(None, [exporter1, exporter2])
		composite_exporter.handle_vo_spell(None)

		assert exporter1.handle_vo_spell_calls == 1
		assert exporter2.handle_vo_spell_calls == 1


class TestFriendlyPlayerExporter:
	def test_inferrable(self, parser):
		with open(logfile("friendly_player_id_is_1.power.log")) as f:
			parser.read(f)

		assert len(parser.games) == 1
		packet_tree = parser.games[0]
		fpe = FriendlyPlayerExporter(packet_tree)
		friendly_player = fpe.export()
		assert friendly_player == 1

	def test_ai_game(self, parser):
		with open(logfile("puzzlelab.power.log")) as f:
			parser.read(f)

		assert len(parser.games) == 1
		packet_tree = parser.games[0]
		fpe = FriendlyPlayerExporter(packet_tree)
		friendly_player = fpe.export()
		assert friendly_player == 1

	def test_battlegrounds(self, parser):
		with open(logfile("36393_battlegrounds.power.log")) as f:
			parser.read(f)

		assert len(parser.games) == 1
		packet_tree = parser.games[0]
		fpe = FriendlyPlayerExporter(packet_tree)
		friendly_player = fpe.export()
		assert friendly_player == 3
