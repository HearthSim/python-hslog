from __future__ import unicode_literals


EMPTY_GAME = """
D 02:59:14.6088620 GameState.DebugPrintPower() - CREATE_GAME
D 02:59:14.6149420 GameState.DebugPrintPower() -     GameEntity EntityID=1
D 02:59:14.6446530 GameState.DebugPrintPower() -     Player EntityID=2 PlayerID=1 GameAccountId=[hi=1 lo=0]
D 02:59:14.6481950 GameState.DebugPrintPower() -     Player EntityID=3 PlayerID=2 GameAccountId=[hi=3 lo=2]
""".strip()

INITIAL_GAME = """
D 02:59:14.6088620 GameState.DebugPrintPower() - CREATE_GAME
D 02:59:14.6149420 GameState.DebugPrintPower() -     GameEntity EntityID=1
D 02:59:14.6420450 GameState.DebugPrintPower() -         tag=TURN value=1
D 02:59:14.6428100 GameState.DebugPrintPower() -         tag=ZONE value=PLAY
D 02:59:14.6430430 GameState.DebugPrintPower() -         tag=ENTITY_ID value=1
D 02:59:14.6436240 GameState.DebugPrintPower() -         tag=NEXT_STEP value=BEGIN_MULLIGAN
D 02:59:14.6438920 GameState.DebugPrintPower() -         tag=CARDTYPE value=GAME
D 02:59:14.6442880 GameState.DebugPrintPower() -         tag=STATE value=RUNNING
D 02:59:14.6446530 GameState.DebugPrintPower() -     Player EntityID=2 PlayerID=1 GameAccountId=[hi=1 lo=0]
D 02:59:14.6450220 GameState.DebugPrintPower() -         tag=PLAYSTATE value=PLAYING
D 02:59:14.6463220 GameState.DebugPrintPower() -         tag=PLAYER_ID value=1
D 02:59:14.6466060 GameState.DebugPrintPower() -         tag=TEAM_ID value=1
D 02:59:14.6469080 GameState.DebugPrintPower() -         tag=ZONE value=PLAY
D 02:59:14.6470710 GameState.DebugPrintPower() -         tag=CONTROLLER value=1
D 02:59:14.6472580 GameState.DebugPrintPower() -         tag=ENTITY_ID value=2
D 02:59:14.6476340 GameState.DebugPrintPower() -         tag=CARDTYPE value=PLAYER
D 02:59:14.6481950 GameState.DebugPrintPower() -     Player EntityID=3 PlayerID=2 GameAccountId=[hi=3 lo=2]
D 02:59:14.6483770 GameState.DebugPrintPower() -         tag=PLAYSTATE value=PLAYING
D 02:59:14.6485530 GameState.DebugPrintPower() -         tag=CURRENT_PLAYER value=1
D 02:59:14.6486970 GameState.DebugPrintPower() -         tag=FIRST_PLAYER value=1
D 02:59:14.6492590 GameState.DebugPrintPower() -         tag=PLAYER_ID value=2
D 02:59:14.6493880 GameState.DebugPrintPower() -         tag=TEAM_ID value=2
D 02:59:14.6495200 GameState.DebugPrintPower() -         tag=ZONE value=PLAY
D 02:59:14.6496470 GameState.DebugPrintPower() -         tag=CONTROLLER value=2
D 02:59:14.6497780 GameState.DebugPrintPower() -         tag=ENTITY_ID value=3
D 02:59:14.6500380 GameState.DebugPrintPower() -         tag=CARDTYPE value=PLAYER
""".strip()

FULL_ENTITY = """D 22:25:48.0678873 GameState.DebugPrintPower() - FULL_ENTITY - Creating ID=4 CardID=
D 22:25:48.0678873 GameState.DebugPrintPower() -     tag=ZONE value=DECK
D 22:25:48.0678873 GameState.DebugPrintPower() -     tag=CONTROLLER value=1
D 22:25:48.0678873 GameState.DebugPrintPower() -     tag=ENTITY_ID value=4
""".strip()

INVALID_GAME = """
D 02:59:14.6088620 GameState.DebugPrintPower() - CREATE_GAME
D 02:59:14.6149420 GameState.DebugPrintPower() -     GameEntity EntityID=1
D 02:59:14.6428100 GameState.DebugPrintPower() -         tag=ZONE value=PLAY
D 02:59:14.6481950 GameState.DebugPrintPower() -     Player EntityID=3 PlayerID=2 GameAccountId=[hi=3 lo=2]
D 02:59:14.6483770 GameState.DebugPrintPower() -         tag=PLAYSTATE value=PLAYING
D 02:59:14.6492590 GameState.DebugPrintPower() -         tag=PLAYER_ID value=2
""".strip() + "\n" + FULL_ENTITY

CONTROLLER_CHANGE = """
D 22:25:48.0708939 GameState.DebugPrintPower() - TAG_CHANGE Entity=4 tag=CONTROLLER value=2
""".strip()

OPTIONS_WITH_ERRORS = """
D 23:16:30.5267690 GameState.DebugPrintOptions() - id=38
D 23:16:30.5274350 GameState.DebugPrintOptions() -   option 0 type=END_TURN mainEntity= error=INVALID errorParam=
D 23:16:30.5292340 GameState.DebugPrintOptions() -   option 1 type=POWER mainEntity=[name=Shadow Word: Pain id=33 zone=HAND zonePos=1 cardId=CS2_234 player=1] error=NONE errorParam=
D 23:16:30.5304620 GameState.DebugPrintOptions() -     target 0 entity=[name=Friendly Bartender id=9 zone=PLAY zonePos=3 cardId=CFM_654 player=1] error=NONE errorParam=
D 23:16:30.5315490 GameState.DebugPrintOptions() -     target 1 entity=[name=Flame Juggler id=26 zone=PLAY zonePos=4 cardId=AT_094 player=1] error=NONE errorParam=
D 23:16:30.5326920 GameState.DebugPrintOptions() -     target 2 entity=[name=Friendly Bartender id=15 zone=PLAY zonePos=5 cardId=CFM_654 player=1] error=NONE errorParam=
D 23:16:30.5335050 GameState.DebugPrintOptions() -     target 3 entity=[name=UNKNOWN ENTITY [cardType=INVALID] id=44 zone=HAND zonePos=1 cardId= player=2] error=NONE errorParam=
D 23:16:30.5343760 GameState.DebugPrintOptions() -     target 4 entity=GameEntity error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5350590 GameState.DebugPrintOptions() -     target 5 entity=BehEh error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5357980 GameState.DebugPrintOptions() -     target 6 entity=The Innkeeper error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5365690 GameState.DebugPrintOptions() -     target 7 entity=[name=Tyrande Whisperwind id=64 zone=PLAY zonePos=0 cardId=HERO_09a player=1] error=REQ_MINION_TARGET errorParam=
D 23:16:30.5378770 GameState.DebugPrintOptions() -     target 8 entity=[name=Lesser Heal id=65 zone=PLAY zonePos=0 cardId=CS1h_001_H1 player=1] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5387770 GameState.DebugPrintOptions() -     target 9 entity=[name=Anduin Wrynn id=66 zone=PLAY zonePos=0 cardId=HERO_09 player=2] error=REQ_MINION_TARGET errorParam=
D 23:16:30.5396470 GameState.DebugPrintOptions() -     target 10 entity=[name=Lesser Heal id=67 zone=PLAY zonePos=0 cardId=CS1h_001 player=2] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5405690 GameState.DebugPrintOptions() -     target 11 entity=[name=Chillwind Yeti id=37 zone=PLAY zonePos=1 cardId=CS2_182 player=2] error=REQ_TARGET_MAX_ATTACK errorParam=3
D 23:16:30.5413980 GameState.DebugPrintOptions() -   option 2 type=POWER mainEntity=[name=The Coin id=68 zone=HAND zonePos=3 cardId=GAME_005 player=1] error=NONE errorParam=
D 23:16:30.5422920 GameState.DebugPrintOptions() -   option 3 type=POWER mainEntity=[name=Shadow Madness id=13 zone=HAND zonePos=4 cardId=EX1_334 player=1] error=NONE errorParam=
D 23:16:30.5431510 GameState.DebugPrintOptions() -     target 0 entity=[name=UNKNOWN ENTITY [cardType=INVALID] id=44 zone=HAND zonePos=1 cardId= player=2] error=NONE errorParam=
D 23:16:30.5454830 GameState.DebugPrintOptions() -     target 1 entity=GameEntity error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5477520 GameState.DebugPrintOptions() -     target 2 entity=BehEh error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5485390 GameState.DebugPrintOptions() -     target 3 entity=The Innkeeper error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5493210 GameState.DebugPrintOptions() -     target 4 entity=[name=Tyrande Whisperwind id=64 zone=PLAY zonePos=0 cardId=HERO_09a player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.5507390 GameState.DebugPrintOptions() -     target 5 entity=[name=Lesser Heal id=65 zone=PLAY zonePos=0 cardId=CS1h_001_H1 player=1] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5517260 GameState.DebugPrintOptions() -     target 6 entity=[name=Anduin Wrynn id=66 zone=PLAY zonePos=0 cardId=HERO_09 player=2] error=REQ_MINION_TARGET errorParam=
D 23:16:30.5527880 GameState.DebugPrintOptions() -     target 7 entity=[name=Lesser Heal id=67 zone=PLAY zonePos=0 cardId=CS1h_001 player=2] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5537070 GameState.DebugPrintOptions() -     target 8 entity=[name=Friendly Bartender id=9 zone=PLAY zonePos=3 cardId=CFM_654 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.5545530 GameState.DebugPrintOptions() -     target 9 entity=[name=Flame Juggler id=26 zone=PLAY zonePos=4 cardId=AT_094 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.5554740 GameState.DebugPrintOptions() -     target 10 entity=[name=Friendly Bartender id=15 zone=PLAY zonePos=5 cardId=CFM_654 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.5563420 GameState.DebugPrintOptions() -     target 11 entity=[name=Chillwind Yeti id=37 zone=PLAY zonePos=1 cardId=CS2_182 player=2] error=REQ_TARGET_MAX_ATTACK errorParam=3
D 23:16:30.5571950 GameState.DebugPrintOptions() -   option 4 type=POWER mainEntity=[name=Prophet Velen id=22 zone=DECK zonePos=0 cardId= player=1] error=NONE errorParam=
D 23:16:30.5581040 GameState.DebugPrintOptions() -   option 5 type=POWER mainEntity=[name=Lesser Heal id=65 zone=PLAY zonePos=0 cardId=CS1h_001_H1 player=1] error=NONE errorParam=
D 23:16:30.5590640 GameState.DebugPrintOptions() -     target 0 entity=[name=Tyrande Whisperwind id=64 zone=PLAY zonePos=0 cardId=HERO_09a player=1] error=NONE errorParam=
D 23:16:30.5599700 GameState.DebugPrintOptions() -     target 1 entity=[name=Anduin Wrynn id=66 zone=PLAY zonePos=0 cardId=HERO_09 player=2] error=NONE errorParam=
D 23:16:30.5609780 GameState.DebugPrintOptions() -     target 2 entity=[name=Friendly Bartender id=9 zone=PLAY zonePos=3 cardId=CFM_654 player=1] error=NONE errorParam=
D 23:16:30.5617920 GameState.DebugPrintOptions() -     target 3 entity=[name=Flame Juggler id=26 zone=PLAY zonePos=4 cardId=AT_094 player=1] error=NONE errorParam=
D 23:16:30.5626230 GameState.DebugPrintOptions() -     target 4 entity=[name=Friendly Bartender id=15 zone=PLAY zonePos=5 cardId=CFM_654 player=1] error=NONE errorParam=
D 23:16:30.5634360 GameState.DebugPrintOptions() -     target 5 entity=[name=Chillwind Yeti id=37 zone=PLAY zonePos=1 cardId=CS2_182 player=2] error=NONE errorParam=
D 23:16:30.5642140 GameState.DebugPrintOptions() -     target 6 entity=[name=UNKNOWN ENTITY [cardType=INVALID] id=44 zone=HAND zonePos=1 cardId= player=2] error=NONE errorParam=
D 23:16:30.5649970 GameState.DebugPrintOptions() -     target 7 entity=GameEntity error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5657040 GameState.DebugPrintOptions() -     target 8 entity=BehEh error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5663840 GameState.DebugPrintOptions() -     target 9 entity=The Innkeeper error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5853710 GameState.DebugPrintOptions() -     target 10 entity=[name=Lesser Heal id=65 zone=PLAY zonePos=0 cardId=CS1h_001_H1 player=1] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5866110 GameState.DebugPrintOptions() -     target 11 entity=[name=Lesser Heal id=67 zone=PLAY zonePos=0 cardId=CS1h_001 player=2] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5879360 GameState.DebugPrintOptions() -   option 6 type=POWER mainEntity=[name=Friendly Bartender id=9 zone=PLAY zonePos=3 cardId=CFM_654 player=1] error=NONE errorParam=
D 23:16:30.5888760 GameState.DebugPrintOptions() -     target 0 entity=[name=UNKNOWN ENTITY [cardType=INVALID] id=44 zone=HAND zonePos=1 cardId= player=2] error=NONE errorParam=
D 23:16:30.5899630 GameState.DebugPrintOptions() -     target 1 entity=GameEntity error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5906880 GameState.DebugPrintOptions() -     target 2 entity=BehEh error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5913550 GameState.DebugPrintOptions() -     target 3 entity=The Innkeeper error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5922220 GameState.DebugPrintOptions() -     target 4 entity=[name=Tyrande Whisperwind id=64 zone=PLAY zonePos=0 cardId=HERO_09a player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.5930550 GameState.DebugPrintOptions() -     target 5 entity=[name=Lesser Heal id=65 zone=PLAY zonePos=0 cardId=CS1h_001_H1 player=1] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5939620 GameState.DebugPrintOptions() -     target 6 entity=[name=Lesser Heal id=67 zone=PLAY zonePos=0 cardId=CS1h_001 player=2] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.5948320 GameState.DebugPrintOptions() -     target 7 entity=[name=Friendly Bartender id=9 zone=PLAY zonePos=3 cardId=CFM_654 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.5961510 GameState.DebugPrintOptions() -     target 8 entity=[name=Flame Juggler id=26 zone=PLAY zonePos=4 cardId=AT_094 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.5986050 GameState.DebugPrintOptions() -     target 9 entity=[name=Friendly Bartender id=15 zone=PLAY zonePos=5 cardId=CFM_654 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.5994940 GameState.DebugPrintOptions() -     target 10 entity=[name=Chillwind Yeti id=37 zone=PLAY zonePos=1 cardId=CS2_182 player=2] error=REQ_TARGET_TAUNTER errorParam=
D 23:16:30.6003150 GameState.DebugPrintOptions() -     target 11 entity=[name=Anduin Wrynn id=66 zone=PLAY zonePos=0 cardId=HERO_09 player=2] error=REQ_TARGET_TAUNTER errorParam=
D 23:16:30.6011520 GameState.DebugPrintOptions() -   option 7 type=POWER mainEntity=[name=Flame Juggler id=26 zone=PLAY zonePos=4 cardId=AT_094 player=1] error=NONE errorParam=
D 23:16:30.6019770 GameState.DebugPrintOptions() -     target 0 entity=[name=UNKNOWN ENTITY [cardType=INVALID] id=44 zone=HAND zonePos=1 cardId= player=2] error=NONE errorParam=
D 23:16:30.6027890 GameState.DebugPrintOptions() -     target 1 entity=GameEntity error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6034650 GameState.DebugPrintOptions() -     target 2 entity=BehEh error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6041340 GameState.DebugPrintOptions() -     target 3 entity=The Innkeeper error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6048310 GameState.DebugPrintOptions() -     target 4 entity=[name=Tyrande Whisperwind id=64 zone=PLAY zonePos=0 cardId=HERO_09a player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.6057680 GameState.DebugPrintOptions() -     target 5 entity=[name=Lesser Heal id=65 zone=PLAY zonePos=0 cardId=CS1h_001_H1 player=1] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6066080 GameState.DebugPrintOptions() -     target 6 entity=[name=Lesser Heal id=67 zone=PLAY zonePos=0 cardId=CS1h_001 player=2] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6074100 GameState.DebugPrintOptions() -     target 7 entity=[name=Friendly Bartender id=9 zone=PLAY zonePos=3 cardId=CFM_654 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.6082410 GameState.DebugPrintOptions() -     target 8 entity=[name=Flame Juggler id=26 zone=PLAY zonePos=4 cardId=AT_094 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.6090360 GameState.DebugPrintOptions() -     target 9 entity=[name=Friendly Bartender id=15 zone=PLAY zonePos=5 cardId=CFM_654 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.6098350 GameState.DebugPrintOptions() -     target 10 entity=[name=Chillwind Yeti id=37 zone=PLAY zonePos=1 cardId=CS2_182 player=2] error=REQ_TARGET_TAUNTER errorParam=
D 23:16:30.6106390 GameState.DebugPrintOptions() -     target 11 entity=[name=Anduin Wrynn id=66 zone=PLAY zonePos=0 cardId=HERO_09 player=2] error=REQ_TARGET_TAUNTER errorParam=
D 23:16:30.6114800 GameState.DebugPrintOptions() -   option 8 type=POWER mainEntity=[name=Friendly Bartender id=15 zone=PLAY zonePos=5 cardId=CFM_654 player=1] error=NONE errorParam=
D 23:16:30.6123260 GameState.DebugPrintOptions() -     target 0 entity=[name=UNKNOWN ENTITY [cardType=INVALID] id=44 zone=HAND zonePos=1 cardId= player=2] error=NONE errorParam=
D 23:16:30.6130940 GameState.DebugPrintOptions() -     target 1 entity=GameEntity error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6137570 GameState.DebugPrintOptions() -     target 2 entity=BehEh error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6143980 GameState.DebugPrintOptions() -     target 3 entity=The Innkeeper error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6151260 GameState.DebugPrintOptions() -     target 4 entity=[name=Tyrande Whisperwind id=64 zone=PLAY zonePos=0 cardId=HERO_09a player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.6159780 GameState.DebugPrintOptions() -     target 5 entity=[name=Lesser Heal id=65 zone=PLAY zonePos=0 cardId=CS1h_001_H1 player=1] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6168520 GameState.DebugPrintOptions() -     target 6 entity=[name=Lesser Heal id=67 zone=PLAY zonePos=0 cardId=CS1h_001 player=2] error=REQ_HERO_OR_MINION_TARGET errorParam=
D 23:16:30.6180250 GameState.DebugPrintOptions() -     target 7 entity=[name=Friendly Bartender id=9 zone=PLAY zonePos=3 cardId=CFM_654 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.6188420 GameState.DebugPrintOptions() -     target 8 entity=[name=Flame Juggler id=26 zone=PLAY zonePos=4 cardId=AT_094 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.6196650 GameState.DebugPrintOptions() -     target 9 entity=[name=Friendly Bartender id=15 zone=PLAY zonePos=5 cardId=CFM_654 player=1] error=REQ_ENEMY_TARGET errorParam=
D 23:16:30.6204660 GameState.DebugPrintOptions() -     target 10 entity=[name=Chillwind Yeti id=37 zone=PLAY zonePos=1 cardId=CS2_182 player=2] error=REQ_TARGET_TAUNTER errorParam=
D 23:16:30.6212910 GameState.DebugPrintOptions() -     target 11 entity=[name=Anduin Wrynn id=66 zone=PLAY zonePos=0 cardId=HERO_09 player=2] error=REQ_TARGET_TAUNTER errorParam=
D 23:16:30.6222210 GameState.DebugPrintOptions() -   option 9 type=POWER mainEntity=[name=Shadow Word: Death id=23 zone=HAND zonePos=2 cardId=EX1_622 player=1] error=REQ_TARGET_TO_PLAY errorParam=
D 23:16:30.6232190 GameState.DebugPrintOptions() -   option 10 type=POWER mainEntity=[name=Ragnaros the Firelord id=16 zone=HAND zonePos=5 cardId=EX1_298 player=1] error=REQ_ENOUGH_MANA errorParam=
D 23:16:30.6242450 GameState.DebugPrintOptions() -   option 11 type=POWER mainEntity=GameEntity error=REQ_YOUR_TURN errorParam=
D 23:16:30.6249860 GameState.DebugPrintOptions() -   option 12 type=POWER mainEntity=The Innkeeper error=REQ_YOUR_TURN errorParam=
D 23:16:30.6257420 GameState.DebugPrintOptions() -   option 13 type=POWER mainEntity=[name=Tyrande Whisperwind id=64 zone=PLAY zonePos=0 cardId=HERO_09a player=1] error=REQ_ATTACK_GREATER_THAN_0 errorParam=
D 23:16:30.6274730 GameState.DebugPrintOptions() -   option 14 type=POWER mainEntity=[name=Anduin Wrynn id=66 zone=PLAY zonePos=0 cardId=HERO_09 player=2] error=REQ_YOUR_TURN errorParam=
D 23:16:30.6284990 GameState.DebugPrintOptions() -   option 15 type=POWER mainEntity=[name=Lesser Heal id=67 zone=PLAY zonePos=0 cardId=CS1h_001 player=2] error=REQ_YOUR_TURN errorParam=
D 23:16:30.6293790 GameState.DebugPrintOptions() -   option 16 type=POWER mainEntity=[name=Chillwind Yeti id=37 zone=PLAY zonePos=1 cardId=CS2_182 player=2] error=REQ_YOUR_TURN errorParam=
D 23:16:30.6303440 GameState.DebugPrintOptions() -   option 17 type=POWER mainEntity=[name=UNKNOWN ENTITY [cardType=INVALID] id=44 zone=HAND zonePos=1 cardId= player=2] error=REQ_YOUR_TURN errorParam=
""".strip()

UNROUNDABLE_TIMESTAMP = """
D 14:43:59.9999997 GameState.DebugPrintPower() - BLOCK_START BlockType=PLAY Entity=[entityName=Bonemare id=25 zone=HAND zonePos=2 cardId=ICC_705 player=1] EffectCardId= EffectIndex=0 Target=[entityName=Spellbreaker id=32 zone=PLAY zonePos=1 cardId=EX1_048 player=1] SubOption=-1
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=Doomflow tag=RESOURCES_USED value=8
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=Doomflow tag=NUM_RESOURCES_SPENT_THIS_GAME value=46
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=Doomflow tag=NUM_CARDS_PLAYED_THIS_TURN value=2
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=Doomflow tag=NUM_MINIONS_PLAYED_THIS_TURN value=2
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=[entityName=Soulfire id=4 zone=HAND zonePos=6 cardId=EX1_308 player=1] tag=ZONE_POSITION value=5
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=[entityName=Spellbreaker id=33 zone=HAND zonePos=5 cardId=EX1_048 player=1] tag=ZONE_POSITION value=4
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=[entityName=Flame Imp id=28 zone=HAND zonePos=4 cardId=EX1_319 player=1] tag=ZONE_POSITION value=3
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=[entityName=Malchezaar's Imp id=18 zone=HAND zonePos=3 cardId=KAR_089 player=1] tag=ZONE_POSITION value=2
D 14:43:59.9999997 GameState.DebugPrintPower() -     TAG_CHANGE Entity=[entityName=Bonemare id=25 zone=HAND zonePos=2 cardId=ICC_705 player=1] tag=ZONE_POSITION value=0
""".strip()

REPEATED_TIMESTAMP = """
D 02:59:14.6492595 GameState.DebugPrintPower() - BLOCK_START BlockType=PLAY Entity=[entityName=Bonemare id=25 zone=HAND zonePos=2 cardId=ICC_705 player=1] EffectCardId= EffectIndex=0 Target=[entityName=Spellbreaker id=32 zone=PLAY zonePos=1 cardId=EX1_048 player=1] SubOption=-1
D 02:59:14.6492595 GameState.DebugPrintPower() - BLOCK_END
D 02:59:14.6492595 GameState.DebugPrintPower() - BLOCK_START BlockType=PLAY Entity=[entityName=Bonemare id=25 zone=HAND zonePos=2 cardId=ICC_705 player=1] EffectCardId= EffectIndex=0 Target=[entityName=Spellbreaker id=32 zone=PLAY zonePos=1 cardId=EX1_048 player=1] SubOption=-1
D 02:59:14.6492595 GameState.DebugPrintPower() - BLOCK_END
""".strip()

SUB_SPELL_BLOCK = """
D 23:58:17.9818688 GameState.DebugPrintPower() - BLOCK_START BlockType=PLAY Entity=[entityName=UNKNOWN ENTITY [cardType=INVALID] id=80 zone=HAND zonePos=4 cardId= player=2] EffectCardId= EffectIndex=0 Target=0 SubOption=-1 
D 23:58:17.9828680 GameState.DebugPrintPower() -     BLOCK_START BlockType=POWER Entity=[entityName=UNKNOWN ENTITY [cardType=INVALID] id=80 zone=HAND zonePos=4 cardId= player=2] EffectCardId= EffectIndex=0 Target=0 SubOption=-1 
D 23:58:17.9838675 GameState.DebugPrintPower() -         SUB_SPELL_START - SpellPrefabGUID=CannonBarrage_Missile_FX:e26b4681614e0964aa8ef7afebc560d1 Source=59 TargetCount=1
D 23:58:17.9838675 GameState.DebugPrintPower() -                           Source = [entityName=Ol' Toomba id=59 zone=PLAY zonePos=0 cardId=DALA_BOSS_37h player=2]
D 23:58:17.9838675 GameState.DebugPrintPower() -                           Targets[0] = [entityName=Don Han'Cho id=41 zone=PLAY zonePos=7 cardId=CFM_685 player=1]
D 23:58:17.9838675 GameState.DebugPrintPower() -             META_DATA - Meta=HISTORY_TARGET Data=0 InfoCount=1
D 23:58:17.9838675 GameState.DebugPrintPower() -                         Info[0] = [entityName=Don Han'Cho id=41 zone=PLAY zonePos=7 cardId=CFM_685 player=1]
D 23:58:17.9838675 GameState.DebugPrintPower() -             TAG_CHANGE Entity=[entityName=Don Han'Cho id=41 zone=PLAY zonePos=7 cardId=CFM_685 player=1] tag=PREDAMAGE value=3 
D 23:58:17.9838675 GameState.DebugPrintPower() -         SUB_SPELL_END
D 23:58:17.9848671 GameState.DebugPrintPower() - BLOCK_END
""".strip()


BGS_SUB_SPELL_BLOCK = """
D 08:59:23.0098315 GameState.DebugPrintPower() - BLOCK_START BlockType=PLAY Entity=[entityName=Freeze id=2718 zone=PLAY zonePos=0 cardId=TB_BaconShopLockAll_Button player=3] EffectCardId= EffectIndex=0 Target=0 SubOption=-1 
D 08:59:23.0098315 GameState.DebugPrintPower() -     BLOCK_START BlockType=POWER Entity=[entityName=Freeze id=2718 zone=PLAY zonePos=0 cardId=TB_BaconShopLockAll_Button player=3] EffectCardId= EffectIndex=0 Target=0 SubOption=-1 
D 08:59:23.0098315 GameState.DebugPrintPower() -         SUB_SPELL_START - SpellPrefabGUID=Bacon_FreezeMinions_AE_Super.prefab:49de73d8b72602f47994a795a78f050d Source=0 TargetCount=0
D 08:59:23.0098315 GameState.DebugPrintPower() -             TAG_CHANGE Entity=[entityName=Bolvar, Fireblood id=2871 zone=PLAY zonePos=1 cardId=ICC_858 player=11] tag=FROZEN value=1 
D 08:59:23.0098315 GameState.DebugPrintPower() -             TAG_CHANGE Entity=[entityName=Cave Hydra id=2872 zone=PLAY zonePos=2 cardId=LOOT_078 player=11] tag=FROZEN value=1 
D 08:59:23.0098315 GameState.DebugPrintPower() -             TAG_CHANGE Entity=[entityName=Nightmare Amalgam id=2873 zone=PLAY zonePos=3 cardId=GIL_681 player=11] tag=FROZEN value=1 
D 08:59:23.0098315 GameState.DebugPrintPower() -             TAG_CHANGE Entity=[entityName=Bolvar, Fireblood id=2874 zone=PLAY zonePos=4 cardId=ICC_858 player=11] tag=FROZEN value=1 
D 08:59:23.0098315 GameState.DebugPrintPower() -             TAG_CHANGE Entity=[entityName=Kindly Grandmother id=2875 zone=PLAY zonePos=5 cardId=KAR_005 player=11] tag=FROZEN value=1 
D 08:59:23.0098315 GameState.DebugPrintPower() -         SUB_SPELL_END
D 08:59:23.0098315 GameState.DebugPrintPower() -     BLOCK_END
D 08:59:23.0098315 GameState.DebugPrintPower() - BLOCK_END
""".strip()

MERCENARIES_SUB_SPELL_BLOCK = """
D 07:21:26.4991775 GameState.DebugPrintPower() - BLOCK_START BlockType=POWER Entity=55 EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=0 Target=0 SubOption=-1 
D 07:21:26.4991775 GameState.DebugPrintPower() -     SUB_SPELL_START - SpellPrefabGUID=ReuseFX_Missile_Object)Bomb_Dynamite_Super:63de8756b8c2c704ba59d9a31ed4e820 Source=34 TargetCount=1
D 07:21:26.4991775 GameState.DebugPrintPower() -                       Source = [entityName=Mad Bomber id=34 zone=PLAY zonePos=1 cardId=LETL_821H player=2]
D 07:21:26.4991775 GameState.DebugPrintPower() -                       Targets[0] = [entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2]
D 07:21:26.4991775 GameState.DebugPrintPower() -         META_DATA - Meta=TARGET Data=0 InfoCount=1
D 07:21:26.4991775 GameState.DebugPrintPower() -                     Info[0] = [entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2]
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=2187 value=55 
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=PREDAMAGE value=5 
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=1173 value=37 
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=2187 value=0 
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=PREDAMAGE value=0 
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=1173 value=0 
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=PREDAMAGE value=5 
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=PREDAMAGE value=0 
D 07:21:26.4991775 GameState.DebugPrintPower() -         META_DATA - Meta=DAMAGE Data=5 InfoCount=1
D 07:21:26.4991775 GameState.DebugPrintPower() -                     Info[0] = [entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2]
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=LAST_AFFECTED_BY value=55 
D 07:21:26.4991775 GameState.DebugPrintPower() -         TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=DAMAGE value=5 
D 07:21:26.4991775 GameState.DebugPrintPower() -         BLOCK_START BlockType=TRIGGER Entity=GameEntity EffectCardId=System.Collections.Generic.List`1[System.String] EffectIndex=10 Target=0 SubOption=-1 TriggerKeyword=TAG_NOT_SET
D 07:21:26.4991775 GameState.DebugPrintPower() -             TAG_CHANGE Entity=[entityName=Powdered Keg id=37 zone=PLAY zonePos=2 cardId=LETL_821H3 player=2] tag=1775 value=1 
D 07:21:26.4991775 GameState.DebugPrintPower() -         BLOCK_END
D 07:21:26.4991775 GameState.DebugPrintPower() -     SUB_SPELL_END
D 07:21:26.4991775 GameState.DebugPrintPower() - BLOCK_END
""".strip()


CACHED_TAG_FOR_DORMANT_CHANGE = """
D 21:56:48.2304744 GameState.DebugPrintPower() -         CACHED_TAG_FOR_DORMANT_CHANGE Entity=[entityName=Selfless Hero id=417 zone=PLAY zonePos=1 cardId=OG_221 player=13] tag=DEATHRATTLE value=1
""".strip()


CACHED_TAG_FOR_DORMANT_CHANGE_SHORT_ENTITY = """
D 21:57:20.2521013 GameState.DebugPrintPower() -         CACHED_TAG_FOR_DORMANT_CHANGE Entity=593 tag=DEATHRATTLE value=1
""".strip()


VO_SPELL = """
D 20:02:31.8466584 GameState.DebugPrintPower() -     VO_SPELL - BrassRingGuid=VO_BTA_BOSS_07h2_Female_NightElf_Mission_Fight_07_PlayerStart_01.prefab:616c9e57bb7fce54684e26be50462d17 - VoSpellPrefabGUID= - Blocking=True - AdditionalDelayInMs=1000
""".strip()


SHUFFLE_DECK = """
D 17:21:14.4464414 GameState.DebugPrintPower() -     SHUFFLE_DECK PlayerID=2
""".strip()


CORRUPT_SHOW_ENTITY = """
D 13:24:38.7829954 GameState.DebugPrintPower() -             SHOW_ENTITY - Updating Entity=9537 CardID=BG21_017
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=CONTROLLER value=11
D 13:24:38.7829954 GameState.DebugPrintPower() -  \x01\x00\x10\x00\x01 \x10\x00\x03\x00\x10\x00   tag=CARDTYPE value=MINION
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=TAG_LAST_KNOWN_COST_IN_HAND value=4
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=479 value=4
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=COST value=4
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=ATK value=4
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=HEALTH value=4
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=TRIGGER_VISUAL value=1
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=ZONE value=PLAY
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=ENTITY_ID value=9537
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=CARDRACE value=PIRATE
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=CREATOR value=9508
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=1037 value=3
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=1067 value=0
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=1068 value=0
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=CREATOR_DBID value=72230
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=1429 value=73951
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=TECH_LEVEL value=3
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=IS_BACON_POOL_MINION value=1
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=SUPPRESS_ALL_SUMMON_VO value=1
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=SPAWN_TIME_COUNT value=1
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=COPIED_FROM_ENTITY_ID value=9531
D 13:24:38.7829954 GameState.DebugPrintPower() -                 tag=1596 value=1
""".strip()
