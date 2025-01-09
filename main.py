import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import platform

#test

load_dotenv()

TOKEN = os.getenv('TOKEN')

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('.'), intents=discord.Intents().all())

        self.cogslist = [
            "cogs.elo"
        ]

    async def setup_hook(self):
        for ext in self.cogslist:
            await self.load_extension(ext)

    async def on_ready(self):
        print(f"Logged in as {self.user.name}")
        print(f"Bot ID: {self.user.id}")
        print(f"Discord Version: {discord.__version__}")
        print(f"Python Version: {platform.python_version()}")
        synced = await self.tree.sync()

client = Client()
client.run(TOKEN)