import discord
import random, io, time
from discord import app_commands
from discord.ext import commands

from utils.db import db
from helpers.views import EmbedView, TradeView, DropDownActionRow
from helpers.card import Card

# TODO: 
# NEEDS ADDING: FUNCTIONALITY WITH MORE THAN 25 CARDS (ADD A BUTTON TO DROPDOWNVIEW TO "GO NEXT PAGE")
# MAYBE MAKE BUTTONS TO ACCEPT/REJECT TRADE ON THE TRADE MESSAGE?

class Trade(commands.Cog):

    group = app_commands.Group(name="request",description="Relating to trading")

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
        await (self.tradeDict[reci]).delete()
        del self.tradeDict[init]
        del self.tradeDict[reci]

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

        await interaction.response.defer(ephemeral=True)
        msg = await interaction.channel.send(view=EmbedView(myText=f"{user.mention}, {interaction.user.mention} wants to trade! Use '/accept' or '/reject'."))
        self.tradeDict[interaction.user] = [ msg, user ]
        self.tradeDict[user] = interaction.user
        return await interaction.followup.send(content="Trade request sent!",ephemeral=True)

    @group.command(name="cancel",description="Cancel an outgoing trade request")
    async def cancel(self, interaction: discord.Interaction):
        if (interaction.user not in list(self.tradeDict.keys())) or (not isinstance(self.tradeDict[interaction.user],list)):
            return await interaction.response.send_message(content="You do not have an outgoing trade request",ephemeral=True)

        msg = (self.tradeDict[interaction.user])[0]
        recipient = (self.tradeDict[interaction.user])[1]
        del self.tradeDict[interaction.user]
        del self.tradeDict[recipient]
        
        await msg.edit(view=EmbedView(myText=f"{interaction.user.mention} has cancelled their trade request"))
        return await interaction.response.send_message(content="You have cancelled your trade",ephemeral=True)

    @group.command(name="reject",description="Reject an incoming trade request")
    async def reject(self, interaction: discord.Interaction):
        if (interaction.user not in list(self.tradeDict.keys())) or (not isinstance(self.tradeDict[interaction.user],discord.Member)):
            return await interaction.response.send_message(content="You do not have an incoming trade request",ephemeral=True)
        
        initiator = self.tradeDict[interaction.user]
        del self.tradeDict[interaction.user]
        msg = (self.tradeDict[initiator])[0]
        del self.tradeDict[initiator]

        await msg.edit(view=EmbedView(myText=f"{initiator}'s trade quest has been rejected."))
        return await interaction.response.send_message(content=f"You have rejected {initiator.mention}'s trade request",ephemeral=True)
        
    @group.command(name="accept",description="Accept an incoming trade request")
    async def accept(self, interaction: discord.Interaction):
        if (interaction.user not in list(self.tradeDict.keys())) or (not isinstance(self.tradeDict[interaction.user],discord.Member)):
            return await interaction.response.send_message(content="You do not have an incoming trade request",ephemeral=True)

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
                await interaction.response.send_message(content="Success!",ephemeral=True,delete_after=1)
                self.values.clear()
                return await self.parent.parent.view.restartDropdown()

        class DropdownView(discord.ui.LayoutView):
            def __init__(self, tradeCog, user: discord.Member, options, start: int) -> None:
                super().__init__(timeout=180)
                self.user = user
                self.tradeCog = tradeCog
                self.options = options
                self.start = start
                self.text = discord.ui.TextDisplay(f"{user.mention}'s Dropdown (A maximum 25 cards are shown; use buttons to see the rest)")
                self.dropdownView = discord.ui.ActionRow(Dropdown())
                for i in range(start, min(start+25,len(options)-start)):
                    self.dropdownView.children[0].add_option(label=Card(options[i][0]).toString(),value=options[i][0])
                self.actionrow = DropDownActionRow(self)
                self.container = discord.ui.Container(self.text,self.dropdownView,self.actionrow)
                self.add_item(self.container)

            async def restartDropdown(self):
                self.remove_item(self.container)
                self.container = discord.ui.Container(self.text,self.dropdownView,self.actionrow)
                self.add_item(self.container)
                return await (self.tradeCog.tradeDict[self.user]).edit(view=self)

            async def update(self, next: bool):
                if (not next) and (self.start == 0):
                    return
                if next and (len(self.options) <= 25+self.start):
                    return
                self.start += (25 if next else -25)

                self.dropdownView = discord.ui.ActionRow(Dropdown())
                for i in range(self.start, min(self.start+25,len(self.options)-self.start)):
                    self.dropdownView.children[0].add_option(label=Card(self.options[i][0]).toString(),value=self.options[i][0])
                self.actionrow = DropDownActionRow(self)
                return await self.restartDropdown()

        initCards = await self.collectCog.getCards(initiator)
        reciCards = await self.collectCog.getCards(interaction.user)
        initDrop = await interaction.channel.send(view=DropdownView(self,initiator,initCards,0))
        reciDrop = await interaction.channel.send(view=DropdownView(self,interaction.user,reciCards,0))

        self.tradeDict[initiator] = initDrop
        self.tradeDict[interaction.user] = reciDrop


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Trade(bot))