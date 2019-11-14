from hslog.export import FriendlyPlayerExporter

from .conftest import logfile


class TestFriendlyPlayerExporter():
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
