import os
from random import choice

import logging

import discord
from discord.ext import commands, tasks

logger = logging.getLogger(f'andross.{__name__}')

bot = commands.Bot(command_prefix=os.environ.get('DISCORD_COMMAND_PREFIX'), intents=discord.Intents.all())

extensions_list = [
    'info',
    'stats'
]

status_messages = [
    'Slippi'
    'Slippi ranked'
]


@tasks.loop(minutes=30)
async def change_status():
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.playing,
                                                        name=choice(status_messages)))


@bot.event
async def on_ready():

    for extension in extensions_list:
        try:
            logger.info(f'loading extension {extension}')
            await bot.load_extension(f'discord_bot.cogs.{extension}')
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            logger.error('Failed to load extension {}\n{}'.format(extension, exc))

    logger.info('Extensions loaded')
    for cog in bot.cogs:
        logger.info(cog)

    # set bot status to online and game it is playing
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.playing, name='Slippi'))

    logger.info(f'Logging in as: {bot.user.name} | {bot.user.id}')

