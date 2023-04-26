import logging
import os

import discord
from discord.ext import commands

from Andross.database.models import create_session, User
from Andross.database.database_crud import get_user
from Andross.visualizer.graphs import generate_basic_elo_graph

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
        results, local_user = get_user(ctx.author.id)
        if not results:
            await ctx.send('You\'re not registered, please register with the register command.')
            await ctx.send_help('reg')
            return

        graph_info = generate_basic_elo_graph(local_user)
        if not graph_info:
            await ctx.send('Unable to generate a graph, please try again later.')
            return

        file = discord.File(graph_info[0], filename='elo_graph.png')

        # create an embed object and set its properties
        embed = discord.Embed(title=f'{local_user.name}\'s elo graph',
                              description='',
                              color=discord.Colour.from_rgb(33, 186, 69))
        embed.set_footer(text=f'{graph_info[1].strftime("%m/%d/%Y")} -> {graph_info[2].strftime("%m/%d/%Y")}',
                         icon_url='https://avatars.githubusercontent.com/u/45867030?s=200&v=4')
        embed.set_image(url='attachment://elo_graph.png')
        # send the embed with the image to a channel
        await ctx.send(file=file, embed=embed)

        if os.path.exists(graph_info[0]):
            os.remove(graph_info[0])


async def setup(bot: commands.Bot):
    await bot.add_cog(VisualizerCog(bot))
