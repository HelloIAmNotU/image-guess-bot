import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# MUCH CREDIT TO https://github.com/DylanHNicolay/MatchCraft,
# from which most of the bot startup and Docker code was derived

# Credit to https://github.com/alexpetrangelo-netizen/uma-bot/
# For Card class, Button class, and Collect Cog

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')

# Define the intents your bot needs
intents = discord.Intents.default()
intents.message_content = True


class MyClient(commands.Bot):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.game")
        await self.load_extension("cogs.collect")
        await self.load_extension("cogs.botHelp")
        if GUILD_ID and GUILD_ID.isdigit():
            guild=discord.Object(id=int(GUILD_ID))  
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        print(f'Logged in as {self.user} (ID: {self.user.id})') # type: ignore
        print('------')


client = MyClient(intents=intents)

def main() -> None:
    client.run(TOKEN) # type: ignore

if __name__ == "__main__":
    main()

    