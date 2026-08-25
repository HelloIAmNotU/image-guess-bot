import discord
import random, io, time
from discord import app_commands
from discord.ext import commands
from PIL import Image
import requests

class Game(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.images = {}

    @app_commands.command(name="setchannel",description="ADMIN ONLY: Sets the image-containing channel")
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(content="This command is reserved for administrators",ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        count = 0

        try:
            async for message in channel.history(limit=500):
                if len(message.attachments) != 1:
                    continue
                if not message.attachments[0].filename.lower().endswith(".jpeg"):
                    continue
                answer = message.attachments[0].filename.lower().removesuffix(".jpeg")
                self.images[answer] = message.attachments[0].url
                count += 1
            return await interaction.followup.send(content=f"{count} images added!")
        except:
            return await interaction.followup.send(content="Command failed.")

    @app_commands.command(name="test",description="test command")
    async def test(self, interaction: discord.Interaction):
        choice = random.choice(list(self.images.keys()))
        response = requests.get(self.images[choice])
        image = Image.open(io.BytesIO(response.content))

        with io.BytesIO() as image_binary:
            image.save(image_binary,"JPEG")
            image_binary.seek(0)
            return await interaction.response.send_message(file=discord.File(fp=image_binary,filename='image.jpeg'))
    
    @app_commands.command(name="start",description="Start a 10-round game")
    async def start(self, interaction: discord.Interaction):
        await interaction.response.defer()
        for i in range(10):
            choice = random.choice(list(self.images.keys()))
            response = requests.get(self.images[choice])
            image = Image.open(io.BytesIO(response.content))
    
            with io.BytesIO() as image_binary:
                image.save(image_binary,"JPEG")
                image_binary.seek(0)
                await interaction.followup.send(content="Who is this?",file=discord.File(fp=image_binary,filename='image.jpeg'))

            def check_user(m: discord.Message):
                return m.author == interaction.user and m.channel == interaction.channel

            while True:
                user_reply = await self.bot.wait_for('message',check=check_user,timeout=30)
                if user_reply.content.lower() == choice:
                    await interaction.followup.send(content="Correct!")
                    time.sleep(0.5)     # prevents spamming
                    break
                else:
                    await interaction.followup.send(content=f"Incorrect. Try again!")
                    time.sleep(0.5)     # prevents spamming

        return await interaction.followup.send(content=f"Congratulations {interaction.user.mention}! You finished!")

    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Game(bot))