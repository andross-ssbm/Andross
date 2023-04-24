import sys
import logging
import argparse

from sqlalchemy.exc import IntegrityError, DataError, OperationalError

from custom_logging import CustomFormatter, format_string
from Andross.database.models import create_session
from Andross.database.database_slippi import update_leaderboard, update_database


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

try:
    with create_session() as session:
        logger.info('Database session established')
        if args.leaderboard:
            logger.info('Updating leaderboard')
            status = update_leaderboard()
            logger.info(f'Leaderboard {"Updated." if status else "not updated."}')

        if args.database:
            logger.info('Updating database')
            status = update_database()
            logger.info(f'Database {"Updated." if status else "not updated."}')

except (IntegrityError, DataError) as e:
    logger.error(f'Error running operation: {e}')
    session.rollback()
except OperationalError as e:
    logger.error(f'Error connecting to database: {e}')
except Exception as e:
    logger.exception(f'Unknown exception: {e}')
    raise


