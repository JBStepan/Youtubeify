import discord
import datetime

def download_added(playlist, user):
    return discord.Embed(
        title="Added playlist to queue",
        description=f"`{playlist}`",
        timestamp=datetime.datetime.now(),
        color=discord.Color.red(),
        url=playlist
    ).set_footer(text=f"Requested by {user}")

def download_done(playlist_url):
    return discord.Embed(
        title=f"Done downloding playlist",
        description=f"Playlist {playlist_url} is down downloading!",
        timestamp=datetime.datetime.now(),
        color=discord.Color.red(),
    )

def download_error(size, user):
    return discord.Embed(
        title=f"Current queue size is {size}",
        timestamp=datetime.datetime.now(),
        color=discord.Color.dark_red(),
    )