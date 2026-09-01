import discord
import random, io, time
from discord import app_commands
from discord.ext import commands

from utils.db import db
from helpers.views import EmbedView, TradeView
from helpers.card import Card

# TODO: 
# NEEDS ADDING: FUNCTIONALITY WITH MORE THAN 25 CARDS (ADD A BUTTON TO DROPDOWNVIEW TO "GO NEXT PAGE")
# MAYBE MAKE BUTTONS TO ACCEPT/REJECT TRADE ON THE TRADE MESSAGE?

class Trade(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.collectCog = bot.get_cog("Collect")
        self.tradeDict = {}
        self.images = {}

    def setImages(self, images: dict[str,str]) -> None:
        self.images = images

    def remove(self, user: discord.Member):
        del self.tradeDict[user]

    async def complete(self, init: discord.Member, initList: list[str], reci: discord.Member, reciList: list[str]):
        await db.connect()
        for str in initList:
            await db.execute("UPDATE cards SET user_id = $1 WHERE card_id = $2;",reci.id,str)
        for str in reciList:
            await db.execute("UPDATE cards SET user_id = $1 WHERE card_id = $2;",init.id,str)
        await db.close()

        await (self.tradeDict[init]).delete()
        return await (self.tradeDict[reci]).delete()

    @app_commands.command(name="trade",description="Start a trade with a given user")
    async def trade(self, interaction: discord.Interaction, user: discord.Member):
        if len(self.images) == 0:
            return await interaction.response.send_message(content="The bot is not ready",ephemeral=True)
        if user == interaction.user or user.bot:
            return await interaction.response.send_message(content="You cannot trade with that user",ephemeral=True)
        if interaction.user in list(self.tradeDict.keys()):
            return await interaction.response.send_message(content="You have an outgoing trade request",ephemeral=True)
        if user in list(self.tradeDict.keys()):
            return await interaction.response.send_message(content="That user has an ongoing trade request",ephemeral=True)

        msg = await interaction.channel.send(view=EmbedView(myText=f"{user.mention}, {interaction.user.mention} wants to trade! Use '/accept' or '/reject'."))
        self.tradeDict[interaction.user] = [ msg, user ]
        self.tradeDict[user] = interaction.user
        return await interaction.response.send_message(content="Trade request sent!",ephemeral=True)

    @app_commands.command(name="cancel",description="Cancel an outgoing trade request")
    async def cancel(self, interaction: discord.Interaction):
        if interaction.user not in list(self.tradeDict.keys()):
            return await interaction.response.send_message(content="You do not have an incoming trade request",ephemeral=True)
        if not isinstance(self.tradeDict[interaction.user],list):
            return await interaction.response.send_message(content="You are already in a trade!",ephemeral=True)

        msg = (self.tradeDict[interaction.user])[0]
        recipient = (self.tradeDict[interaction.user])[1]
        del self.tradeDict[interaction.user]
        del self.tradeDict[recipient]
        
        await msg.edit(view=EmbedView(myText=f"{interaction.user.mention} has cancelled their trade request"))
        return await interaction.response.send_message(content="You have cancelled your trade",ephemeral=True)

    @app_commands.command(name="reject",description="Reject an incoming trade request")
    async def reject(self, interaction: discord.Interaction):
        if interaction.user not in list(self.tradeDict.keys()):
            return await interaction.response.send_message(content="You do not have an incoming trade request",ephemeral=True)
        if not isinstance(self.tradeDict[interaction.user],discord.Member):
            return await interaction.response.send_message(content="You are already in a trade!",ephemeral=True)

        initiator = self.tradeDict[interaction.user]
        del self.tradeDict[interaction.user]
        msg = (self.tradeDict[initiator])[0]
        del self.tradeDict[initiator]

        await msg.edit(view=EmbedView(myText=f"{initiator}'s trade quest has been rejected."))
        return await interaction.response.send_message(content=f"You have rejected {initiator.mention}'s trade request",ephemeral=True)
        
    @app_commands.command(name="accept",description="Accept an incoming trade request")
    async def accept(self, interaction: discord.Interaction):
        if interaction.user not in list(self.tradeDict.keys()):
            return await interaction.response.send_message(content="You do not have an incoming trade request",ephemeral=True)
        if not isinstance(self.tradeDict[interaction.user],discord.Member):
            return await interaction.response.send_message(content="You are already in a trade!",ephemeral=True)

        await interaction.response.send_message(content="Trade accepted!",ephemeral=True)
        initiator = self.tradeDict[interaction.user]
        msg = (self.tradeDict[initiator])[0]

        self.tradeDict[interaction.user] = None
        self.tradeDict[initiator] = None

        tradeview = TradeView(self,msg,initiator,interaction.user)
        await msg.edit(view=tradeview)

        class Dropdown(discord.ui.Select):
            def __init__(self) -> None:
                super().__init__(placeholder="Choose the cards you would like to trade!",min_values=1,max_values=1,options=[])
            async def callback(self, interaction: discord.Interaction) -> None:
                if interaction.user.id != self.parent.parent.view.user.id:
                    return await interaction.response.send_message(content="This is not your trade menu.",ephemeral=True)

                await tradeview.addCard(interaction.user == initiator,self.values[0])
                return await interaction.response.send_message(content="Success!",ephemeral=True,delete_after=1)

        class DropdownView(discord.ui.LayoutView):
            def __init__(self, user: discord.Member, options) -> None:
                super().__init__(timeout=180)
                self.user = user
                self.text = discord.ui.TextDisplay(f"{user.mention}'s Dropdown")
                self.dropdownView = discord.ui.ActionRow(Dropdown())
                for i in range(min(25,len(options))):
                    self.dropdownView.children[0].add_option(label=Card(options[i][0]).toString(),value=options[i][0])
                container = discord.ui.Container(self.text,self.dropdownView)
                self.add_item(container)

        initCards = await self.collectCog.getCards(initiator)
        reciCards = await self.collectCog.getCards(interaction.user)
        initDrop = await interaction.channel.send(view=DropdownView(initiator,initCards))
        reciDrop = await interaction.channel.send(view=DropdownView(interaction.user,reciCards))

        self.tradeDict[initiator] = initDrop
        self.tradeDict[interaction.user] = reciDrop


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Trade(bot))