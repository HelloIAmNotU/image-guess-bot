import discord
import random, io, time, asyncio
from discord import app_commands
from discord.ext import commands
from PIL import Image
import requests

class Game(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.images = {}
        self.game = True

    @app_commands.command(name="setchannel",description="ADMIN ONLY: Sets the image-containing channel")
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(content="This command is reserved for administrators",ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        count = 0

        try:
            async for message in channel.history(limit=500):
                if len(message.attachments) < 1:
                    continue
                for i in range(len(message.attachments)):
                    if not message.attachments[i].filename.lower().endswith(".jpeg"):
                        continue
                    answer = message.attachments[i].filename.lower().replace("_"," ").removesuffix(".jpeg")
                    self.images[answer] = message.attachments[i].url
                    count += 1
            return await interaction.followup.send(content=f"{count} images added!")
        except:
            return await interaction.followup.send(content="Command failed.")

    """
    @app_commands.command(name="test",description="test command")
    async def test(self, interaction: discord.Interaction):
        choice = random.choice(list(self.images.keys()))
        response = requests.get(self.images[choice])
        image = Image.open(io.BytesIO(response.content))

        with io.BytesIO() as image_binary:
            image.save(image_binary,"JPEG")
            image_binary.seek(0)
            return await interaction.response.send_message(file=discord.File(fp=image_binary,filename='image.jpeg'))
    """

    @app_commands.command(name="ready",description="ADMIN ONLY: Allows the bot to start a game")
    async def ready(self, interaction: discord.Interaction):
        self.game = False
        return await interaction.response.send_message(content="Success!",ephemeral=True)

    @app_commands.command(name="stop",description="ADMIN ONLY: Stops the bot from starting a game")
    async def stop(self, interaction: discord.Interaction):
        self.game = True
        return await interaction.response.send_message(content="Success!",ephemeral=True)

    @app_commands.command(name="start",description="Starts the game. Admin can type 'end' to force stop")
    async def start(self, interaction: discord.Interaction, rounds: int):
        if self.game:
            return await interaction.response.send_message(content="A game cannot be started right now.",ephemeral=True)
        await interaction.response.defer()
        correct = {}
        self.game = True
        for i in range(rounds):
            choice = random.choice(list(self.images.keys()))
            response = requests.get(self.images[choice])
            image = Image.open(io.BytesIO(response.content))
    
            with io.BytesIO() as image_binary:
                image.save(image_binary,"JPEG")
                image_binary.seek(0)
                await interaction.followup.send(content="What is this?",file=discord.File(fp=image_binary,filename='image.jpeg'))

            while True:
                try:
                    user_reply = await self.bot.wait_for('message',timeout=10)
                except asyncio.TimeoutError:
                    await interaction.channel.send(content=f"Question timed out. The answer was {choice}.")
                    break
                else:
                    if user_reply.author.guild_permissions.administrator:
                        if user_reply.content.lower() == "end":
                            self.game = True
                            return await interaction.followup.send(content="Game terminated. Admin must run /ready to restart.")
                        elif user_reply.content.lower() == "next":
                            await interaction.followup.send(content=f"Going next. The answer was {choice}.")
                            time.sleep(1)
                            break
                    if user_reply.content.lower() == choice:
                        mention = user_reply.author.mention
                        await interaction.followup.send(content=f"{mention} got it right!")
                        if (mention not in list(correct.keys())):
                            correct[mention] = 1
                        else:
                            correct[mention] += 1
                        time.sleep(1)  
                        break

        sorted_correct = []
        for key in sorted(correct, key=correct.get, reverse=True):
            sorted_correct.append(key)

        msg = ""
        for mention in sorted_correct:
            msg += (mention + f": {correct[mention]} correct\n")

        self.game = False
        return await interaction.followup.send(content=msg)

    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Game(bot))