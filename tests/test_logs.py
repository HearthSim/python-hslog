import pytest
from hearthstone.enums import FormatType, GameType

from hslog import LogParser, packets
from hslog.exceptions import MissingPlayerData
from hslog.export import EntityTreeExporter, FriendlyPlayerExporter
from hslog.packets import TagChange
from hslog.player import InconsistentPlayerIdError

from .conftest import logfile


@pytest.mark.regression_suite
def test_friendly_player_superfriends_brawl(parser: LogParser):
	with open(logfile("friendly_player_id_is_1.power.log")) as f:
		parser.read(f)

	assert len(parser.games) == 1
	packet_tree = parser.games[0]
	fpe = FriendlyPlayerExporter(packet_tree)
	friendly_player = fpe.export()
	assert friendly_player == 1


@pytest.mark.regression_suite
def test_20457(parser: LogParser):
	with open(logfile("20457_broken_names.power.log")) as f:
		parser.read(f)

	assert len(parser.games) == 1
	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	game = exporter.export()
	assert game.game.players[0].name == "Necroessenza"
	assert game.game.players[1].name == "Heigan l'Impuro"


@pytest.mark.regression_suite
def test_battlegrounds(parser: LogParser):
	with open(logfile("36393_battlegrounds.power.log")) as f:
		parser.read(f)

	assert len(parser.games) == 1
	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	game = exporter.export()
	assert game.game.setup_done
	assert game.game.players[0].name == "BehEh#1355"
	assert len([packet for packet in packet_tree if isinstance(packet, packets.Options)]) == 96


@pytest.mark.regression_suite
def test_change_def(parser: LogParser):
	with open(logfile("20457_def_change.power.log")) as f:
		parser.read(f)

	c = 0
	for packet in parser.games[0].recursive_iter(TagChange):
		if packet.has_change_def:
			c += 1

	assert c == 7


@pytest.mark.regression_suite
def test_debugprintgame(parser: LogParser):
	with open(logfile("23576_debugprintgame.power.log")) as f:
		parser.read(f)

	assert parser.game_meta == {
		"BuildNumber": 23576,
		"FormatType": FormatType.FT_WILD,
		"GameType": GameType.GT_RANKED,
		"ScenarioID": 2,
	}


@pytest.mark.regression_suite
def test_bad_ids(parser: LogParser):
	with pytest.raises(InconsistentPlayerIdError):
		with open(logfile("chaos/change_entity_null_id.power.log")) as f:
			parser.read(f)


@pytest.mark.regression_suite
def test_game_reset(parser: LogParser):
	with open(logfile("toki.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_puzzle_lab(parser: LogParser):
	with open(logfile("puzzlelab.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_puzzle_lab_player(parser: LogParser):
	with open(logfile("puzzle_player.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_unknown_human_player(parser: LogParser):
	with open(logfile("25770_unknown_human_player.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)

	with pytest.raises(MissingPlayerData):
		exporter.export()


@pytest.mark.regression_suite
def test_inferrable_player(parser: LogParser):
	with open(logfile("25770_inferrable_player.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_full_entity_defined_in_subspell(parser: LogParser):
	with open(logfile("34104_subspell.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_cached_tag_for_dormant_change(parser: LogParser):
	with open(logfile("49534_cached_tag_for_dormant_change.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_vo_spell(parser: LogParser):
	with open(logfile("49534_vo_spell.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_shuffle_deck(parser: LogParser):
	with open(logfile("54613_shuffle_deck.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_async_player_names(parser: LogParser):
	with open(logfile("88998_async_player_name.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)

	with pytest.raises(MissingPlayerData):
		exporter.export()


@pytest.mark.regression_suite
def test_name_aliasing(parser: LogParser):
	with open(logfile("88998_missing_player_hash.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_mercenaries_solo_bounty(parser: LogParser):
	with open(logfile("93227_mercenaries_solo_bounty.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True


@pytest.mark.regression_suite
def test_mercenaries_solo_pvp(parser: LogParser):
	with open(logfile("93227_mercenaries_solo_pvp.power.log")) as f:
		parser.read(f)

	packet_tree = parser.games[0]
	exporter = EntityTreeExporter(packet_tree, player_manager=parser.player_manager)
	exporter.export()
	assert True
