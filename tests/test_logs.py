import pytest
from hearthstone.enums import FormatType, GameType

from hslog import packets
from hslog.export import EntityTreeExporter, ExporterError, FriendlyPlayerExporter
from hslog.packets import TagChange

from .conftest import logfile


@pytest.mark.regression_suite
def test_friendly_player_superfriends_brawl(parser):
	with open(logfile("friendly_player_id_is_1.power.log")) as f:
		parser.read(f)

	assert len(parser.games) == 1
	packet_tree = parser.games[0]
	fpe = FriendlyPlayerExporter(packet_tree)
	friendly_player = fpe.export()
	assert friendly_player == 1


@pytest.mark.regression_suite
def test_20457(parser):
	with open(logfile("20457_broken_names.power.log")) as f:
		parser.read(f)

	assert len(parser.games) == 1
	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	game = exporter.export()
	assert game.game.players[0].name == "Necroessenza"
	assert game.game.players[1].name == "Heigan l'Impuro"


@pytest.mark.regression_suite
def test_battlegrounds(parser):
	with open(logfile("36393_battlegrounds.power.log")) as f:
		parser.read(f)

	assert len(parser.games) == 1
	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	game = exporter.export()
	assert game.game.setup_done
	assert game.game.players[0].name == "BehEh#1355"
	assert len([packet for packet in packet_tree if isinstance(packet, packets.Options)]) == 96


@pytest.mark.regression_suite
def test_change_def(parser):
	with open(logfile("20457_def_change.power.log")) as f:
		parser.read(f)

	c = 0
	for packet in parser.games[0].recursive_iter(TagChange):
		if packet.has_change_def:
			c += 1

	assert c == 7


@pytest.mark.regression_suite
def test_debugprintgame(parser):
	with open(logfile("23576_debugprintgame.power.log")) as f:
		parser.read(f)

	assert parser.game_meta == {
		"BuildNumber": 23576,
		"FormatType": FormatType.FT_WILD,
		"GameType": GameType.GT_RANKED,
		"ScenarioID": 2,
	}


@pytest.mark.regression_suite
def test_bad_ids(parser):
	with open(logfile("chaos/change_entity_null_id.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	with pytest.raises(ExporterError):
		exporter.export()


@pytest.mark.regression_suite
def test_game_reset(parser):
	with open(logfile("toki.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_puzzle_lab(parser):
	with open(logfile("puzzlelab.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_puzzle_lab_player(parser):
	with open(logfile("puzzle_player.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_unknown_human_player(parser):
	with open(logfile("25770_unknown_human_player.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_inferrable_player(parser):
	with open(logfile("25770_inferrable_player.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_full_entity_defined_in_subspell(parser):
	with open(logfile("34104_subspell.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree)
	exporter.export()
	assert True
