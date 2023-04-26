import discord
from discord.ext import commands

from Andross.slippi.slippi_user import Characters


class CharacterDropdown(discord.ui.Select):
    def __init__(self, ctx: commands.Context, character_list: list[Characters]):

        self.ctx = ctx
        self.characters = character_list
        options = []
        for character in self.characters:
            options.append(discord.SelectOption(label=character.character, description='Character you wish to view'))

        super().__init__(placeholder='Please selects a character...',
                         min_values=1,
                         max_values=len(options),
                         options=options)

    def create_character_embed(self, character: Characters) -> discord.Embed:
        total_games = 0
        for sum in self.characters:
            total_games += sum.game_count

        percentage_used = (character.game_count/total_games)*100

        return_embed = discord.Embed(title=character.character.title(), color=discord.Colour.green())
        return_embed.set_thumbnail(url=character.get_character_icon_url())
        return_embed.add_field(name='Game count', value=character.game_count)
        return_embed.add_field(name='\u200b', value='\u200b')
        return_embed.add_field(name='\u200b', value='\u200b')
        return_embed.add_field(name='Percentage used', value=f'{percentage_used:.2f}%')
        return return_embed

    async def callback(self, interaction: discord.Interaction):
        self.view.embeds = self.view.embeds[:1]
        character_to_view = []
        for character in self.characters:
            for check_value in self.values:
                if character.character == check_value:
                    character_to_view.append(character)

        for chars in character_to_view:
            self.view.embeds.append(self.create_character_embed(chars))

        await interaction.response.edit_message(embeds=self.view.embeds)
