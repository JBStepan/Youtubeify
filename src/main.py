import asyncio
from backend import run_backend
from discord_app import run_bot

async def main():
    backend_task = asyncio.create_task(run_backend())
    discord_task = asyncio.create_task(asyncio.to_thread(run_bot()))

    await asyncio.gather(backend_task, discord_task)

if __name__ == "__main__":
    asyncio.run(main())