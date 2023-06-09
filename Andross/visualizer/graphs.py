import os
from typing import Tuple
from matplotlib import pyplot, dates, cycler
from datetime import timedelta, datetime

from Andross.database.models import User, Elo
from Andross.database.database_crud import get_all_elo, get_user
from Andross.database.queries import get_users_latest_characters
from Andross.slippi.slippi_ranks import rank_list
from Andross.slippi.slippi_characters import SlippiCharacterColors


discord_colors = {
    'green': '#57F287',
    'slippi_green': '#21ba45',
    'yellow': '#FAA61A',
    'blurple': '#5865F2',
    'fuchsia': '#EB459E',
    'red': '#ED4245',
    'grey': '#B9BBBE',
    'dark': '#36393F',
    'dark_theme_bg': '#313338',
    'dark_theme_highlight': '#2b2d31',
    'light_blue': '#4FC1E9',
    'orange': '#FFA500',
    'purple': '#9B59B6',
    'turquoise': '#1ABC9C',
    'pink': '#E91E63',
    'grey_blue': '#607D8B',
    'black': '#000000',
}

discord_dark_style = {
    'axes.facecolor': discord_colors['dark_theme_bg'],
    'axes.edgecolor': discord_colors['grey'],
    'axes.labelcolor': discord_colors['grey'],
    'text.color': discord_colors['grey'],
    'xtick.color': discord_colors['grey'],
    'ytick.color': discord_colors['grey'],
    'grid.color': discord_colors['grey'],
    'figure.facecolor': discord_colors['dark_theme_bg'],
    'figure.edgecolor': discord_colors['dark_theme_bg'],
    'savefig.facecolor': discord_colors['dark_theme_highlight'],
    'savefig.edgecolor': discord_colors['dark_theme_bg'],
    'font.family': 'sans-serif',
    'font.sans-serif': ['Open Sans', 'Arial', 'Helvetica', 'DejaVu Sans', 'Bitstream Vera Sans', 'sans-serif'],
    'axes.prop_cycle': cycler(color=[discord_colors['slippi_green'], discord_colors['yellow'],
                                     discord_colors['blurple'], discord_colors['fuchsia'], discord_colors['green'],
                                     discord_colors['red'], discord_colors['light_blue'], discord_colors['orange'],
                                     discord_colors['purple'], discord_colors['turquoise'], discord_colors['pink'],
                                     discord_colors['grey_blue']]),

    'axes.titlesize': 'xx-large',
    'axes.labelsize': 'x-large'
}


def generate_character_usage_pie(user: User) -> None | str:
    labels = []
    data = []
    colors = []
    results, character_list = get_users_latest_characters(user)
    if not results:
        return

    for character in character_list:
        labels.append(character.character_info.name.title())
        data.append(character.game_count)
        colors.append(SlippiCharacterColors[character.character_info.name])

    pyplot.style.use(discord_dark_style)
    fig, ax = pyplot.subplots()
    ax.pie(data, labels=labels, colors=colors, autopct='%1.1f%%', textprops={'color': discord_colors['grey']})
    ax.set_title(user.name, fontsize='xx-large')


    cwd = os.getcwd()
    sub_directory = 'imgs'
    sub_path = os.path.join(cwd, sub_directory)

    if not os.path.exists(sub_path):
        os.makedirs(sub_path)

    # concatenate directory path with image file name
    filename = f'characters_{user.id}.png'
    filepath = os.path.join(cwd, sub_directory, filename)

    # save image to specified directory
    pyplot.savefig(filepath)
    pyplot.clf()
    pyplot.close(fig)

    return filepath


def generate_basic_elo_graph(user: User) -> None | Tuple[str, datetime, datetime]:
    x_axis = []
    y_axis = []
    results, elo_entries = get_all_elo(user.id)

    if not results:
        return None

    for elo_entry in elo_entries:
        x_axis.append(elo_entry.entry_time)
        y_axis.append(elo_entry.elo)

    if not x_axis or not y_axis:
        return

    pyplot.style.use(discord_dark_style)
    fig, ax = pyplot.subplots(figsize=(15, 10))
    ax.plot(x_axis, y_axis)
    ax.set_title(user.name, fontsize='xx-large')
    ax.set_ylabel('Elo', fontsize='x-large')
    ax.set_xlabel('Time', fontsize='x-large')
    date_range = dates.drange(min(x_axis).date(), max(x_axis).date() + timedelta(days=1), timedelta(weeks=1))
    ax.set_xticks(date_range)
    ax.set_xticklabels([dates.num2date(d).strftime('%Y-%m-%d') for d in date_range], rotation=90)

    # Get y ticks to check bounds of ranks
    y_ticks = ax.get_yticks()

    # Add extra y-axis ticks for rank names
    for rank in rank_list:
        if y_ticks[-1] > rank.lower_bound and y_ticks[0] < rank.upper_bound:
            ax.axhline(y=rank.lower_bound, color='gray', linestyle='--', linewidth=0.5)
            ax.text(x_axis[0], rank.lower_bound, rank.rank_name, fontsize='x-small')

    cwd = os.getcwd()
    sub_directory = 'imgs'
    sub_path = os.path.join(cwd, sub_directory)

    if not os.path.exists(sub_path):
        os.makedirs(sub_path)

    # concatenate directory path with image file name
    filename = f'elo_{user.id}.png'
    filepath = os.path.join(cwd, sub_directory, filename)

    # save image to specified directory
    pyplot.savefig(filepath)
    pyplot.clf()
    pyplot.close(fig)
    return filepath, min(x_axis).date(), max(x_axis).date()
