import logging
import math

import discord
from discord.ext import commands
from sqlalchemy import or_
from zoneinfo import ZoneInfo

from Andross.database.models import create_session, User, EntryDate
from Andross.database.database_crud import get_user, create_user
from Andross.database.database_slippi import update_database
from Andross.database.queries import get_users_latest_placement, get_leaderboard_standard, \
    leaderboard_type
from Andross.slippi.slippi_ranks import get_rank
from Andross.slippi.slippi_api import get_player_ranked_data, is_valid_connect_code

from Andross.discord_bot.cogs.utils.views import UserStatsView

logger = logging.getLogger(f'andross.{__name__}')

discordMemberStr = discord.Member | str
memberstr_description = 'Connect code or a discord member, if left empty it will use the person who issues the command'
memberstr_parameter = commands.parameter(default=lambda ctx: ctx.author, description=memberstr_description)
memberbool_description = 'Boolean (ex. 0, 1, True, False) or a discord member'


def format_leaderboard(leaderboard: list[leaderboard_type]) -> list[str]:
    def generate_whitespace(n):
        return " " * n

    leaderboard_text = []
    counter = 0
    for entry in leaderboard:
        logger.debug(f'entry: {entry}')
        counter += 1
        base_whitespace = 13
        whitespace_amount_front = 2 if counter <= 9 else 1
        whitespace_amount = (base_whitespace - len(entry[0]))
        leaderboard_text.append(f"{counter}."
                                f"{generate_whitespace(whitespace_amount_front)}{entry[0]}"
                                f"{generate_whitespace(whitespace_amount)}"
                                f"| {format(entry[2], '.1f')} ({entry[3]}/{entry[4]}) "
                                f"{get_rank(entry[2], entry[5])}")
    return leaderboard_text


class LeaderboardView(discord.ui.View):

    def __init__(self, embed: discord.Embed, leaderboard: list[str], date: str, pages: int, cur_page: int):
        super().__init__(timeout=180)
        self.embed = embed
        self.leaderboard = leaderboard
        self.date = date
        self.pages = pages
        self.cur_page = cur_page

    @discord.ui.button(emoji='⬅️', style=discord.ButtonStyle.green)
    async def button_callback_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cur_page:
            self.cur_page -= 1
        else:
            self.cur_page = self.pages - 1

        page_start = self.cur_page * 10
        page_end = page_start + 10
        embed_text = '\n'.join([x for x in self.leaderboard[page_start:page_end]])

        self.embed.description = f'```{embed_text}```'
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(emoji='➡️', style=discord.ButtonStyle.green)
    async def button_callback_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cur_page < self.pages - 1:
            self.cur_page += 1
        else:
            self.cur_page = 0

        page_start = self.cur_page * 10
        page_end = page_start + 10
        embed_text = '\n'.join([x for x in self.leaderboard[page_start:page_end]])

        self.embed.description = f'```{embed_text}```'
        await interaction.response.edit_message(embed=self.embed)


class StatsCog(commands.Cog, name='Stats'):

    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        logger.error(f'{error}')

        await ctx.send(f'An error occurred: {error}')

    # TODO Add try except for database functions
    @commands.command(name='user', help='In-depth stats display')
    async def __user(self, ctx: commands.Context, user_info: discordMemberStr = memberstr_parameter):
        logger.info(f'__user: {ctx}, {user_info}')

        user_id = 0
        cc = ''
        is_cc = False
        user_placement = 0

        if isinstance(user_info, str):
            is_cc = True
            cc = user_info.lower()

        if isinstance(user_info, discord.Member):
            user_id = user_info.id

        with create_session() as session:
            # Attempt to get local user info
            results, local_user = get_user(user_id, cc)
            if not results and not is_cc:
                await ctx.send('Unable to get your info from database, please provide a connect_code or register with '
                               'the register command.')
                await ctx.send_help('reg')
                return

            ranked_data = get_player_ranked_data(local_user.cc if local_user else cc)
            if not ranked_data.ranked_profile.id:
                await ctx.send('Was unable to get your stats from slippi.gg, please try again or check your info')
                return

            if local_user:
                user_placement = user_placement = get_users_latest_placement(local_user)
            else:
                user_placement = ranked_data.ranked_profile.daily_regional_placement

            wins = ranked_data.ranked_profile.wins
            losses = ranked_data.ranked_profile.losses
            if (not wins and losses) or not wins and not losses:
                win_rate = 0
            elif not losses:
                win_rate = 100
            else:
                win_rate = (wins / (wins + losses)) * 100

            user_embed = discord.Embed(title=f'{user_placement}. '
                                             f'{local_user.name if local_user else ranked_data.display_name} '
                                             f'[{ranked_data.connect_code}]',
                                       url=f'{ranked_data.get_user_profile_page()}')
            if ranked_data.ranked_profile.characters:
                user_embed.set_thumbnail(url=ranked_data.get_main_character().get_character_icon_url())
            else:
                user_embed.set_thumbnail(url='https://avatars.githubusercontent.com/u/45867030?s=200&v=4')
            user_embed.add_field(name='Elo', value=f'{ranked_data.ranked_profile.rating_ordinal:.2f}')
            user_embed.add_field(name='Rank', value=ranked_data.get_rank())
            user_embed.add_field(name='\u200b', value='\u200b')
            user_embed.add_field(name='Wins', value=wins)
            user_embed.add_field(name='Loses', value=losses)
            user_embed.add_field(name='Win-rate', value=f'{win_rate:.2f}%')

            await ctx.send(view=UserStatsView(ctx, user_embed, ranked_data), embed=user_embed)

    @commands.command(name='stats', help='Simple stats display')
    async def __stats(self, ctx: commands.Context, user_info: discordMemberStr = memberstr_parameter):
        logger.info(f'__stats: {ctx}, {user_info}')

        user_id = 0
        cc = ''
        is_cc = False

        if isinstance(user_info, str):
            is_cc = True
            cc = user_info.lower()

        if isinstance(user_info, discord.Member):
            user_id = user_info.id

        # Attempt to get local user info
        results, local_user = get_user(user_id, cc)
        if not results and not is_cc:
            await ctx.send('Unable to get your info from database, please provide a connect_code or register with '
                           'the register command.')
            await ctx.send_help('reg')
            return

        ranked_data = get_player_ranked_data(local_user.cc if results else cc)
        if not ranked_data.ranked_profile.id:
            await ctx.send('Was unable to get your stats from slippi.gg, please try again or check your info')
            return

        wins = ranked_data.ranked_profile.wins
        losses = ranked_data.ranked_profile.losses
        if not losses and not wins:
            win_rate = '100%'
        elif not wins:
            win_rate = '0%'
        else:
            win_rate = f'{(wins / (wins + losses)) * 100:.2f}%'

        await ctx.send(f'```'
                       f'{ranked_data.display_name} ({ranked_data.connect_code})\n'
                       f'{ranked_data.ranked_profile.rating_ordinal:.2f} | {ranked_data.get_rank()}\n'
                       f'{ranked_data.ranked_profile.wins}/{ranked_data.ranked_profile.losses} '
                       f'{win_rate}'
                       f'```')

    # TODO Improve discord parameter descriptions
    @commands.command(name='reg', help='Registers a user for the bot')
    async def __reg_user(self, ctx: commands.Context, user_connect_code: str, name: str = None):
        logger.info(f'__reg_user: {ctx}, {user_connect_code}, {name}')

        if not is_valid_connect_code(user_connect_code.lower()):
            await ctx.send(f'You\'ve entered a invalid connect code, please enter a valid connect code')
            await ctx.send('reg')
            return

        # Attempt to set name if none is given
        if not name:
            name = ctx.author.display_name

        if len(name) > 12:
            await ctx.send(f'Your name must be 12 characters or less. Your name was {len(name)} characters long')
            await ctx.send_help('reg')
            return

        user_connect_code = user_connect_code.lower()

        results, id_check = get_user(ctx.author.id)
        if results:
            await ctx.send(f'You\'ve already created an account your connect code is {id_check.cc}')
            return

        results, cc_check = get_user(0, user_connect_code)
        if results:
            await ctx.send(f'{user_connect_code} is already being used by {cc_check}. '
                           f'Please enter a different one.')
            return

        results = create_user(ctx.author.id, user_connect_code, name)
        if not results:
            await ctx.send('Unable to create user, please try again later.')
            return

        await ctx.send('Thank you for registering, we will now get your stats for you')

        # Attempt to create database entries for the user
        if update_database(ctx.author.id):
            await ctx.send('Updated your stats.')
            results, user_stats = get_user(ctx.author.id)
            if results:
                await ctx.send(f'```'
                               f'{user_stats.name} ({user_stats.cc})\n'
                               f'{user_stats.latest_elo:.2f} | ({user_stats.latest_wins}/{user_stats.latest_losses}) |'
                               f' {get_rank(user_stats.latest_elo, user_stats.latest_drp)}'
                               f'```')
                return

        await ctx.send('We were unable to get your stats, please check your connect_code. '
                       'If your code is correct your stats should update at the next update.')

    @commands.command(name='leaderboard', help='Prints a pagified leaderboard')
    async def __leaderboard(self, ctx: commands.Context,
                            focus_me: bool | discord.Member =
                            commands.parameter(default=None, description=memberbool_description)):
        logger.info(f'__leaderboard: {focus_me}')

        focus_user = 0
        user_index = 0

        if focus_me:
            if isinstance(focus_me, discord.Member):
                focus_user = focus_me.id
            else:
                focus_user = ctx.author.id

        results, leaderboard = get_leaderboard_standard()
        if not results or not leaderboard:
            await ctx.send('Unable to get get leaderboard please try again')

        latest_date = leaderboard[0].entry_time

        if focus_me:
            for entry in leaderboard:
                if entry[6] == focus_user:
                    user_index = leaderboard.index(entry)
                    break

        leaderboard = format_leaderboard(leaderboard)
        logger.debug(f'leaderboard: {ctx.author}, {focus_me}')

        if latest_date:
            string_date = latest_date.entry_time.astimezone(
                tz=ZoneInfo('America/Detroit')).strftime('%Y-%m-%d %H:%M:%S')
        else:
            string_date = 'Failed to get date'

        pages = math.ceil(len(leaderboard) / 10)
        cur_page = 0

        page_start = cur_page * 10
        page_end = page_start + 10

        if focus_me:
            cur_page = math.ceil(user_index / 10)
            if cur_page:
                cur_page -= 1

        inital_description = '\n'.join([x for x in leaderboard[page_start:page_end]])

        lb_embed = discord.Embed(title='Leaderboard',
                                 description=f'```{inital_description}```', colour=discord.Colour.green())
        lb_embed.set_thumbnail(url='https://avatars.githubusercontent.com/u/45867030?s=200&v=4')
        lb_embed.set_footer(text=string_date)
        lb_view = LeaderboardView(lb_embed, leaderboard, string_date, pages, 0)
        await ctx.send(view=lb_view, embed=lb_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
