import sys
import logging
import argparse
import requests

from custom_logging import CustomFormatter, format_string
from Andross.andross_api.andross_api import api_url, authorization_header


logger = logging.getLogger('andross')
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('log.log')

stdout_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(format_string)
stdout_handler.setFormatter(CustomFormatter())
file_handler.setFormatter(formatter)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)

logger.info(f'create_snapshot.py ran')

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help='Sets logging level to debug')
parser.add_argument('-l', '--leaderboard', help='Update the leaderboard', action='store_true')
parser.add_argument('-d', '--database', help='Update the main database entries', action='store_true')

args = parser.parse_args()
logger.debug(f'--verbose: {args.verbose}')
logger.debug(f'--leaderboard: {args.leaderboard}')
logger.debug(f'--database {args.database}')

if args.leaderboard:
    logger.info('Updating leaderboard')
    response = requests.post(f'{api_url}/rest/update_leaderboard/', headers=authorization_header)
    logger.info(f'Leaderboard {"Updated." if response.status_code == 201 else "not updated."}')

if args.database:
    logger.info('Updating database')
    response = requests.post(f'{api_url}/rest/update/', headers=authorization_header)
    logger.info(f'Database {"Updated." if response.status_code == 201 else "not updated."}')
