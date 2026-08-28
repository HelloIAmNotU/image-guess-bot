import discord
import random, io, time
from discord import app_commands
from discord.ext import commands
from PIL import Image
import requests

from utils.db import db
from helpers.views import Buttons
from helpers.card import Card


class Collect(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.gameCog = bot.get_cog("Game")
        self.images = {}

    async def cog_load(self) -> None:
        self.images = self.gameCog.getImages()

    async def insertcard(self, userid: int, card: str):
        await db.connect()
        await db.execute("INSERT INTO cards (card_id, user_id) VALUES ($1, $2);",card,userid)
        await db.close()

    async def cardcount(self, name: str) -> int:
        await db.connect()
        retval = await db.execute("SELECT cardnum FROM cardcounts WHERE cardname = $1;",name)
        await db.close()
        if len(retval) == 0:
            return 0
        return retval[0][0]

    async def setcount(self, name: str, num: int):
        await db.connect()
        if (num == 1):
            await db.execute("INSERT INTO cardcounts (cardname, cardnum) VALUES ($1, $2);",name,1)
        else:
            await db.execute("UPDATE cardcounts SET cardnum = $1 WHERE cardname = $2;",num,name)
        await db.close()

    @app_commands.command(name="collection",description="Gets the collection of a user (self if not specified)")
    async def collection(self, interaction: discord.Interaction, user: discord.Member = None):
        if user == None:
            user = interaction.user
        await db.connect()
        retval = await db.execute("SELECT card_id FROM cards WHERE user_id = $1;",user.id)
        await db.close()
        msg = f"{user.mention}'s cards:\n"
        for row in retval:
            msg += ((Card(row[0]).toString())+"\n")
        await interaction.response.send_message(content=msg,ephemeral=True)
        
    #picks three random characters and displays them for choosing
    @app_commands.command(name="drop",description="A drop of 3 characters!")
    async def drop(self, interaction: discord.Interaction):

        lastDropped = 0
        now = time.time_ns()

        await db.connect()
        retval = await db.execute("SELECT dropped_time FROM timeout WHERE user_id = $1;",interaction.user.id)
        if len(retval) == 0:
            await db.execute("INSERT INTO timeout (user_id, dropped_time) VALUES ($1, $2);",interaction.user.id,now)
        else:
            lastDropped = retval[0]['dropped_time']
        await db.close()

        timeRemaining = 43200-((now-lastDropped)/1000000000)

        if timeRemaining > 0:
            return await interaction.response.send_message(content=f"You may drop again in {int(timeRemaining//3600)} hours {int((timeRemaining%3600)//60)} minutes {int(timeRemaining%3600%60)} seconds.",ephemeral=True)
        else:
            await db.connect()
            await db.execute("UPDATE timeout SET dropped_time = $1 WHERE user_id = $2;",now,interaction.user.id)
            await db.close()

        await interaction.response.defer()

        name1 = random.choice(list(self.images.keys()))
        name2 = random.choice(list(self.images.keys()))
        name3 = random.choice(list(self.images.keys()))

        image1 = Image.open(io.BytesIO(requests.get(self.images[name1]).content))
        image2 = Image.open(io.BytesIO(requests.get(self.images[name2]).content))
        image3 = Image.open(io.BytesIO(requests.get(self.images[name3]).content))

        x1,y1 = image1.size
        x2,y2 = image2.size
        x3,y3 = image3.size

        imggroup = Image.new(mode="RGB", size=(x1+x2+x3+40,max(y1,y2,y3)), color="white")
        imggroup.paste(image1, (0, 0))
        imggroup.paste(image2, (x1+20, 0))
        imggroup.paste(image3, (x1+x2+40, 0))

        with io.BytesIO() as image_binary:
            imggroup.save(image_binary, "JPEG")
            image_binary.seek(0)
            choices = [ name1, name2, name3 ]
            msg = await interaction.followup.send(content=f"{interaction.user.mention}, your drop will be ready soon!")
            view = Buttons(collect=self, names=choices, user=interaction.user, msg=msg)
            return await msg.edit(content=f"{interaction.user.mention}, here is your drop!",attachments=[discord.File(fp=image_binary, filename='image.png')], view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Collect(bot))