import discord
from discord.ext import commands, tasks
import os
import asyncio
from dotenv import load_dotenv
from discord import app_commands
from tourneydata.datamanager import TDataManager
from osuapi.osu_wrapper import OsuWrapper

load_dotenv("keys.env")


intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, application_id=os.getenv("APP_ID"))

async def load():

    osu_handler = OsuWrapper(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
    bot.data_manager = TDataManager(osu_handler, 
        "tourneydata/matches.json", 
        "tourneydata/users.json", 
        "tourneydata/teams.json",
        "tourneydata/localdata.json"
        )

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    await load()
    await bot.start(os.getenv("BOT_TOKEN"))

asyncio.run(main())
