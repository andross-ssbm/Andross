import discord
from discord.ext import commands


class InfoCog(commands.Cog, name='Info'):

    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx: commands.Context,
                                error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(name='idea', help='Gives link to submit idea/feature request')
    async def __showIdea(self, ctx: commands.Context):
        embed = discord.Embed(title='Idea/Feature',
                              url=f'https://forms.gle/3LeNacbjPUn9vyVf7',
                              description='Form to submit features/ideas',
                              colour=discord.Colour.dark_purple())
        await ctx.send(embed=embed)

    @commands.command(name='git', help='Gives link to git repository')
    async def __showGit(self, ctx: commands.Context):
        embed = discord.Embed(title='Github',
                              url=f'https://github.com/andross-ssbm/Andross',
                              description='Link to project repository.',
                              colour=discord.Colour.green())
        await ctx.send(embed=embed)

    @commands.command(name='website', help='Gives link to website')
    async def __showWebsite(self, ctx: commands.Context):
        embed = discord.Embed(title='Andross',
                              url=f'http://nerv.group/leaderboard',
                              description='Website leaderboard',
                              colour=discord.Colour.red())
        await ctx.send(embed=embed)

    @commands.command(name='creator', help='Gives info about creator')
    async def __showCreator(self, ctx: commands.Context):
        await ctx.send("```"
                       "Created by Sophia\n"
                       "Discord: sophimander\n"
                       "Twitter: https://twitter.com/Sophimander"
                       "```")


async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))
