import logging

logger = logging.getLogger(f'andross.{__name__}')


slippi_character_url = 'https://slippi.gg/images/characters/stock-icon-?-0.png'


SlippiCharacterId = {
    'DONKEY_KONG': 0,  # Mapped to 255 in database
    'CAPTAIN_FALCON': 1,
    'FOX': 2,
    'GAME_AND_WATCH': 3,
    'KIRBY': 4,
    'BOWSER': 5,
    'LINK': 6,
    'LUIGI': 7,
    'MARIO': 8,
    'MARTH': 9,
    'MEWTWO': 10,
    'NESS': 11,
    'PEACH': 12,
    'PIKACHU': 13,
    'ICE_CLIMBERS': 14,
    'JIGGLYPUFF': 15,
    'SAMUS': 16,
    'YOSHI': 17,
    'ZELDA': 18,
    'SHEIK': 19,
    'FALCO': 20,
    'YOUNG_LINK': 21,
    'DR_MARIO': 22,
    'ROY': 23,
    'PICHU': 24,
    'GANONDORF': 25,
    'None': 256
}


def get_key_from_value(value, dict):
    for key, val in dict.items():
        if val == value:
            return key
    return None


def get_character_name(char_id: int) -> str:
    logger.debug(f'get_character_name: {char_id}')
    if char_id == 255:
        char_id = 0
    return get_key_from_value(char_id, SlippiCharacterId)


def get_character_id(name: str, dk_claus: bool = False) -> int:
    logger.debug(f'get_character_id: {name}')
    character_id = SlippiCharacterId.get(name)
    if dk_claus and character_id == 0:
        character_id = 255
    return character_id


def get_character_url(name: str) -> str:
    logger.debug(f'get_character_url: {name}')
    return slippi_character_url.replace('?', str(get_character_id(name)))
