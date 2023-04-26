import discord
from discord.ext import commands
from discord.ui import View

from Andross.slippi.slippi_user import SlippiUser
from Andross.discord_bot.cogs.utils.components import CharacterDropdown


class UserStatsView(View):

    def __init__(self, ctx: commands.Context, embed: discord.Embed, user_slippi: SlippiUser):
        super().__init__()

        self._ctx = ctx
        self.embeds = [embed]

        self.characters = user_slippi.ranked_profile.characters

        self.add_item(CharacterDropdown(ctx, self.characters))
