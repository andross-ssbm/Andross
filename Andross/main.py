import logging
import os
import sys

from database.models import initialize
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

    bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    main()
