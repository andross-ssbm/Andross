import requests
from ratelimiter import RateLimiter
from re import match

import logging

from ..slippi.slippi_user import SlippiUser

logger = logging.Logger(f'andross.{__name__}')

limiter = RateLimiter(max_calls=1, period=1)


def connect_code_to_html(connect_code: str) -> str:
    return connect_code.replace('#', '-')


def is_valid_connect_code(connect_code: str) -> bool:
    return True if (match(r"^(?=.{3,9}$)[a-zA-Z]{1,7}#[0-9]{1,7}$", connect_code)) else False


def __get_player_data(connect_code: str):

    if not is_valid_connect_code(connect_code):
        logger.warning(f'Invalid connect_code: {connect_code}')
        return

    query = """
        fragment userProfilePage on User {
            displayName
            connectCode {
                code
                __typename
            }
            rankedNetplayProfile {
                id
                ratingOrdinal
                ratingUpdateCount
                wins
                losses
                dailyGlobalPlacement
                dailyRegionalPlacement
                continent
                characters {
                    id
                    character
                    gameCount
                    __typename
                }
                __typename
            }
            __typename
        }
        query AccountManagementPageQuery($cc: String!) {
            getConnectCode(code: $cc) {
                user {
                    ...userProfilePage
                    __typename
                }
                __typename
            }
        }
    """
    variables = {
        "cc": connect_code.upper()
    }
    payload = {
        "operationName": "AccountManagementPageQuery",
        "query": query,
        "variables": variables
    }
    headers = {
        "content-type": "application/json"
    }
    response = requests.post('https://gql-gateway-dot-slippi.uc.r.appspot.com/graphql', json=payload, headers=headers)
    return response.json()


def get_player_data_throttled(connect_code: str):
    with limiter:
        return __get_player_data(connect_code)


def get_player_ranked_data(connect_code: str) -> SlippiUser | None:
    logger.info(f'get_player_ranked_data: {connect_code}')
    player_data = get_player_data_throttled(connect_code)

    logger.debug(f'player_data: {logger}')
    if not player_data or not player_data['data']['getConnectCode']:
        return

    return SlippiUser(player_data)


def does_exist(connect_code: str) -> bool:
    results = get_player_data_throttled(connect_code)

    if not results or not results['data']['getConnectCode']:
        return False

    return True
