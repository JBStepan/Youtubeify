from typing import Tuple
import discord
import os
from dotenv import load_dotenv
import asyncio
import subprocess
import embeds

load_dotenv()
bot = discord.Bot()

os.makedirs("downloads", exist_ok=True)

task_queue: asyncio.Queue[Tuple[discord.User, str]] = asyncio.Queue()

def get_shell_string(playlist: str):
    return f'yt-dlp -o "%(uploader)s - %(title)s.%(ext)s" --audio-format mp3 --audio-quality 0 --extract-audio --add-metadata  "{playlist}"'

async def task_worker():
    task_data = await task_queue.get()
    user, playlist_url = task_data

    await user.send(embeds=[embeds.download_added(playlist_url, user.display_name)])

    try:
        process = subprocess.Popen(get_shell_string(playlist_url), shell=True, cwd="downloads" )
        process.wait()

        if process.returncode == 1:
            await user.send(f"There has been an issue downloading `{playlist_url}`")
        else:
            await user.send(f"Done downloading `{playlist_url}`")
    except Exception as e:
        print(e)

@bot.command(name="download")
async def download_content(ctx: discord.ApplicationContext, *, playlist_url: str):
    await task_queue.put((ctx.author, playlist_url)) 
    await ctx.respond(embeds=[embeds.download_added(playlist_url, ctx.author.display_name)])
    
@bot.event
async def on_ready():
    bot.loop.create_task(task_worker())
    print(f"Bot ready!")

bot.run(os.getenv('TOKEN'))