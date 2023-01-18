from io import StringIO

from hslog.filter import BattlegroundsLogFilter


class TestBattlegroundsLogFilter:

    def test_suppression(self):
        unknown_tag = "D 00:13:20.7502897 GameState.DebugPrintPower() -     " \
            "TAG_CHANGE Entity=22 tag=10 value=60"

        lf1 = BattlegroundsLogFilter(StringIO(unknown_tag))

        assert list(lf1) == []
        assert lf1.num_lines_read == 1
        assert lf1.num_lines_emitted == 0

        lf2 = BattlegroundsLogFilter(StringIO(unknown_tag), show_suppressed_lines=True)

        assert list(lf2) == ["X: " + unknown_tag]
        assert lf2.num_lines_read == 1
        assert lf2.num_lines_emitted == 1

    def test_attacks_minion(self):
        attack1 = StringIO(
            "D 00:14:49.3366557 GameState.DebugPrintPower() -     "
            "BLOCK_START BlockType=ATTACK Entity=[entityName=Dachowiec id=345 zone=PLAY "
            "zonePos=1 cardId=CFM_315 player=16] "
            "EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=0 "
            "Target=0 SubOption=-1\n"

            "D 00:14:49.3366557 GameState.DebugPrintPower() -         BLOCK_START "
            "BlockType=TRIGGER Entity=[entityName=BaconShop8PlayerEnchant id=71 zone=PLAY "
            "zonePos=0 cardId=TB_BaconShop_8P_PlayerE player=8] "
            "EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=10 "
            "Target=0 SubOption=-1 TriggerKeyword=TAG_NOT_SET\n"

            "D 00:14:49.3366557 GameState.DebugPrintPower() -             TAG_CHANGE "
            "Entity=Starluki#2943 tag=1481 value=2 \n"

            "D 00:14:49.3366557 GameState.DebugPrintPower() -         BLOCK_END\n"
            "D 00:14:49.3366557 GameState.DebugPrintPower() -     BLOCK_END\n"
        )

        assert list(BattlegroundsLogFilter(attack1)) == []

        attack2 = "D 00:14:20.3501059 GameState.DebugPrintPower() - BLOCK_START " \
            "BlockType=ATTACK Entity=[entityName=Morska wyga id=245 zone=PLAY zonePos=1 " \
            "cardId=BGS_061 player=16] " \
            "EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=1 " \
            "Target=0 SubOption=-1\n" \
            \
            "D 00:14:20.3501059 GameState.DebugPrintPower() -     BLOCK_START " \
            "BlockType=TRIGGER Entity=[entityName=3ofKindCheckPlayerEnchant id=72 " \
            "zone=PLAY zonePos=0 cardId=TB_BaconShop_3ofKindChecke player=8] " \
            "EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=0 " \
            "Target=0 SubOption=-1 TriggerKeyword=TAG_NOT_SET\n" \
            \
            "D 00:14:20.3501059 GameState.DebugPrintPower() -     BLOCK_END\n" \
            "D 00:14:20.3501059 GameState.DebugPrintPower() - BLOCK_END\n"

        assert list(BattlegroundsLogFilter(StringIO(attack2))) == [
            line + "\n" for line in attack2.split("\n") if line
        ]

    def test_attacks_hero(self):
        attack = "D 00:41:17.0376047 GameState.DebugPrintPower() -     BLOCK_START " \
            "BlockType=ATTACK Entity=[entityName=Ragnaros Władca Ognia id=7973 zone=PLAY " \
            "zonePos=0 cardId=TB_BaconShop_HERO_11 player=16] " \
            "EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=0 " \
            "Target=0 SubOption=-1\n" \
            \
            "D 00:41:17.0376047 GameState.DebugPrintPower() -         TAG_CHANGE " \
            "Entity=GameEntity tag=PROPOSED_ATTACKER value=7973\n" \
            \
            "D 00:41:17.0376047 GameState.DebugPrintPower() -         TAG_CHANGE " \
            "Entity=GameEntity tag=PROPOSED_DEFENDER value=97\n" \
            \
            "D 00:41:17.0376047 GameState.DebugPrintPower() -     BLOCK_END\n"

        assert list(BattlegroundsLogFilter(StringIO(attack))) == [
            line + "\n" for line in attack.split("\n") if line
        ]

    def test_options(self):
        options = StringIO(
            "D 00:14:02.2116755 GameState.DebugPrintOptions() - id=1\n"

            "D 00:14:02.2116755 GameState.DebugPrintOptions() -   option 0 type=END_TURN "
            "mainEntity= error=INVALID errorParam=\n"

            "D 00:14:02.2116755 GameState.DebugPrintOptions() -   option 1 type=POWER "
            "mainEntity=[entityName=Odśwież id=239 zone=PLAY zonePos=0 "
            "cardId=TB_BaconShop_8p_Reroll_Button player=8] error=NONE errorParam=\n"

            "D 00:14:02.2116755 GameState.DebugPrintOptions() -   option 2 type=POWER "
            "mainEntity=[entityName=Zamrożenie id=240 zone=PLAY zonePos=0 "
            "cardId=TB_BaconShopLockAll_Button player=8] error=NONE errorParam=\n"
        )

        lf = BattlegroundsLogFilter(options)

        assert list(lf) == ["D 00:14:02.2116755 GameState.DebugPrintPower() - BLOCK_END\n"]
        assert lf.num_lines_emitted == 1
        assert lf.num_lines_read == 4

    def test_tag_change(self):
        unknown_tag = StringIO(
            "D 00:13:20.7502897 GameState.DebugPrintPower() -     "
            "TAG_CHANGE Entity=22 tag=10 value=60"
        )

        assert list(BattlegroundsLogFilter(unknown_tag)) == []

        blacklisted_tag = StringIO(
            "D 00:14:49.3366557 GameState.DebugPrintPower() -         "
            "TAG_CHANGE Entity=[entityName=Dachowiec id=345 zone=PLAY zonePos=1 "
            "cardId=CFM_315 player=16] tag=EXHAUSTED value=1"
        )

        assert list(BattlegroundsLogFilter(blacklisted_tag)) == []

        valid_tag = "D 00:13:20.7502897 GameState.DebugPrintPower() - TAG_CHANGE " \
            "Entity=GameEntity tag=STEP value=BEGIN_MULLIGAN"

        assert list(BattlegroundsLogFilter(StringIO(valid_tag))) == [valid_tag]

    def test_preserve_deaths_139963(self):
        hero_death = (
            "D 13:38:27.4606595 GameState.DebugPrintPower() -         "
            "BLOCK_START BlockType=DEATHS Entity=GameEntity "
            "EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=0 "
            "Target=0 SubOption=-1 \n"

            "D 13:38:27.4606595 GameState.DebugPrintPower() -             "
            "TAG_CHANGE Entity=[entityName=Rakanishu id=9591 zone=PLAY zonePos=0 "
            "cardId=TB_BaconShop_HERO_75 player=13] tag=PLAYER_TECH_LEVEL value=0 \n"

            "D 13:38:27.4606595 GameState.DebugPrintPower() -         BLOCK_END\n"
        )

        assert list(BattlegroundsLogFilter(StringIO(hero_death))) == [
            line + "\n" for line in hero_death.split("\n") if line
        ]

        minion_death = StringIO(
            "D 13:20:35.0997287 GameState.DebugPrintPower() -     "
            "BLOCK_START BlockType=DEATHS Entity=GameEntity "
            "EffectCardId=System.Collections.Generic.List`1[System.String] "
            "EffectIndex=0 Target=0 SubOption=-1 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         "
            "TAG_CHANGE Entity=MuNGGG#2882 tag=NUM_MINIONS_PLAYER_KILLED_THIS_TURN "
            "value=1 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         "
            "TAG_CHANGE Entity=GameEntity tag=NUM_MINIONS_KILLED_THIS_TURN value=1 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         "
            "TAG_CHANGE Entity=[entityName=Icky Imp id=455 zone=PLAY zonePos=1 "
            "cardId=BG21_029 player=5] tag=1068 value=4 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         "
            "TAG_CHANGE Entity=[entityName=Icky Imp id=455 zone=PLAY zonePos=1 "
            "cardId=BG21_029 player=5] tag=1068 value=0 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         "
            "TAG_CHANGE Entity=[entityName=Icky Imp id=455 zone=PLAY zonePos=1 "
            "cardId=BG21_029 player=5] tag=EXHAUSTED value=0 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         "
            "TAG_CHANGE Entity=[entityName=Icky Imp id=455 zone=PLAY zonePos=1 "
            "cardId=BG21_029 player=5] tag=ZONE_POSITION value=0 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         "
            "TAG_CHANGE Entity=[entityName=Icky Imp id=455 zone=PLAY zonePos=1 "
            "cardId=BG21_029 player=5] tag=ZONE value=GRAVEYARD \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         TAG_CHANGE "
            "Entity=MuNGGG#2882 tag=NUM_FRIENDLY_MINIONS_THAT_DIED_THIS_TURN value=1 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         TAG_CHANGE "
            "Entity=MuNGGG#2882 tag=NUM_FRIENDLY_MINIONS_THAT_DIED_THIS_GAME value=1 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -         TAG_CHANGE "
            "Entity=[entityName=Icky Imp id=455 zone=PLAY zonePos=1 cardId=BG21_029 "
            "player=5] tag=DAMAGE value=0 \n"

            "D 13:20:35.0997287 GameState.DebugPrintPower() -     BLOCK_END\n"
        )

        assert list(BattlegroundsLogFilter(minion_death)) == []

    def test_preserve_deaths_162867(self):
        full_entity = (
            "D 04:48:45.7822406 GameState.DebugPrintPower() -     BLOCK_START "
            "BlockType=DEATHS Entity=GameEntity "
            "EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=0 "
            "Target=0 SubOption=-1 \n"

            "D 04:48:45.7822406 GameState.DebugPrintPower() -         FULL_ENTITY - "
            "Creating ID=7724 CardID=BG24_005\n"

            "D 04:48:45.7822406 GameState.DebugPrintPower() -             tag=CONTROLLER "
            "value=4\n"

            "D 04:48:45.7822406 GameState.DebugPrintPower() -             tag=CARDTYPE "
            "value=MINION\n"

            "D 04:48:45.7822406 GameState.DebugPrintPower() - BLOCK_END\n"
        )

        assert list(BattlegroundsLogFilter(StringIO(full_entity))) == [
            line + "\n" for line in full_entity.split("\n") if line
        ]
