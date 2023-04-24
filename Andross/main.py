import datetime
import logging
import os
import sys

from database.models import initialize, create_session, User, EntryDate, get_users_leaderboard, Leaderboard
from database.queries import get_leaderboard_quick, get_leaderboard_standard, get_leaderboard_between, get_writeable_leaderboard
from database.database_slippi import update_leaderboard, update_database
from decimal import Decimal
from slippi.slippi_ranks import get_rank
from discord_bot.bot import bot
from custom_logging import CustomFormatter, format_string


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


def main():
    logger.info('Andross started')

    initialize()

    logger.info('Database initialized')

    update_database()

    bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    main()
