import datetime
import logging
import os
from datetime import datetime

import discord
import requests
from discord.ext import commands

from Andross.database.database_crud import get_user
from Andross.discord_bot.cogs.utils.colors import slippi_green
from Andross.visualizer.graphs import generate_basic_elo_graph, generate_character_usage_pie
from Andross.andross_api.andross_api import api_url, api_key

logger = logging.getLogger(f'andross.{__name__}')

discordMemberStr = discord.Member | str
memberstr_description = 'Connect code or a discord member, if left empty it will use the person who issues the command'
memberstr_parameter = commands.parameter(default=lambda ctx: ctx.author, description=memberstr_description)
memberbool_description = 'Boolean (ex. 0, 1, True, False) or a discord member'


class VisualizerCog(commands.Cog, name='Visualizer'):

    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        logger.error(f'{error}')

        await ctx.send(f'An error occurred: {error}')

    @commands.command(name='elo', help='Generate a graph of your elo overtime')
    async def __elo(self, ctx: commands.Context):
        logger.info(f'__elo: {ctx}')

        # Attempt to get local user info
        response = requests.get(f'{api_url}/user_id/', params={'id': ctx.author.id})
        if response.status_code == 404 or response.status_code != 200:
            await ctx.send('You\'re not registered, please register with the register command.')
            await ctx.send_help('reg')
            return
        local_user = response.json()

        response = requests.get(f'{api_url}/get_elo_graph', params={'id': ctx.author.id, 'as_image': 'true'})
        if response.status_code != 200:
            await ctx.send('Unable to generate a graph, please try again later.')
            return

        cwd = os.getcwd()
        sub_directory = 'imgs'
        sub_path = os.path.join(cwd, sub_directory)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # concatenate directory path with image file name
        filename = f'elo_{local_user["id"]}.png'
        filepath = os.path.join(cwd, sub_directory, filename)

        with open(filepath, 'wb') as file:
            file.write(response.content)

        file = discord.File(filepath, filename='elo_graph.png')

        # create an embed object and set its properties
        embed = discord.Embed(title=f'{local_user["name"]}\'s elo graph',
                              description='',
                              color=slippi_green)
        embed.set_footer(text=f'{datetime(2022, 12, 1, 0, 0, 0) .strftime("%m/%d/%Y")} -> '
                              f'{datetime.utcnow().strftime("%m/%d/%Y")}',
                         icon_url='https://avatars.githubusercontent.com/u/45867030?s=200&v=4')
        embed.set_image(url='attachment://elo_graph.png')
        # send the embed with the image to a channel
        await ctx.send(file=file, embed=embed)

        if os.path.exists(filepath):
            os.remove(filepath)

    @commands.command(name='characters', help='Generate a pie graph of your character usage')
    async def __characters(self, ctx: commands.Context):
        logger.info(f'__characters: {ctx}')

        # Attempt to get local user info
        response = requests.get(f'{api_url}/user_id/', params={'id': ctx.author.id})
        if response.status_code == 404 or response.status_code != 200:
            await ctx.send('You\'re not registered, please register with the register command.')
            await ctx.send_help('reg')
            return
        local_user = response.json()

        response = requests.get(f'{api_url}/get_character_graph', params={'id': ctx.author.id, 'as_image': 'true'})
        if response.status_code != 200:
            await ctx.send('Unable to generate a graph, please try again later.')
            return

        cwd = os.getcwd()
        sub_directory = 'imgs'
        sub_path = os.path.join(cwd, sub_directory)

        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # concatenate directory path with image file name
        filename = f'characters_{local_user["id"]}.png'
        filepath = os.path.join(cwd, sub_directory, filename)

        with open(filepath, 'wb') as file:
            file.write(response.content)

        file = discord.File(filepath, filename='character_graph.png')

        # create an embed object and set its properties
        embed = discord.Embed(title=f'{local_user["name"]}\'s character usage',
                              description='',
                              color=slippi_green)
        embed.set_footer(text=f'Characters',
                         icon_url='https://avatars.githubusercontent.com/u/45867030?s=200&v=4')
        embed.set_image(url='attachment://character_graph.png')
        # send the embed with the image to a channel
        await ctx.send(file=file, embed=embed)

        if os.path.exists(filepath):
            os.remove(filepath)


async def setup(bot: commands.Bot):
    await bot.add_cog(VisualizerCog(bot))
