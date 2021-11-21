import nextcord
import asyncio
from nextcord.ext import commands
from nextcord import File
from nextcord import Intents
import os

token = os.environ["starlight_token"]
intents = Intents(messages = True, guilds = True, members = True)
bot = commands.Bot(command_prefix="!", description="General Purpose Discord Bot.", intents=intents)

@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    

    await bot.change_presence(
        status=nextcord.Status.idle
    )

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")
        print('loaded cog')
    else:
        if os.path.isfile(filename):
            print(f"Unable to load {filename[:-3]}")
            
            
loop = asyncio.get_event_loop()
loop.run_until_complete(
    bot.start(token)
)