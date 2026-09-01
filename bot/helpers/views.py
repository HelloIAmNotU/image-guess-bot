import discord
import random

from helpers.card import Card

class Buttons(discord.ui.View):
    def __init__(self, collect, names: list[str], user: discord.Member, msg: discord.WebhookMessage, timeout=60) -> None:
        super().__init__(timeout=timeout)
        self.names = names
        self.collect = collect
        self.user = user
        self.msg = msg

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        return await self.msg.edit(content="This drop has timed out")

    async def clicked(self, interaction: discord.Interaction, index: int):
        if interaction.user != self.user:
            return await interaction.response.send_message(content="This is not your drop.",ephemeral=True)
        curid = await self.collect.cardcount(self.names[index])
        edition = random.randrange(0,200)
        editionrand = 4 if edition == 0 else 3 if edition <= 17 else 2 if edition <= 33 else 1 if edition <= 50 else 0
        card = Card(self.names[index].capitalize(),editionrand,random.randrange(0,5),curid+1)
        await self.collect.insertcard(interaction.user.id,card.compress())
        await self.collect.setcount(self.names[index],curid+1)
        message = f"{interaction.user.mention} has grabbed {self.names[index].capitalize()}. "
        if card.quality == 4:
            message += "Nice! "
        message += f"It's in {card.quality_arr[card.quality]} condition."
        if card.edition != 0:
            message += f"\nWow! Your card has a {card.edition_arr[card.edition]} edition!"
        await interaction.channel.send(content=message)
        self.stop()
        return await self.msg.delete()

    @discord.ui.button(label="1",style=discord.ButtonStyle.blurple)
    async def blurple1_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        return await self.clicked(interaction, 0)
    @discord.ui.button(label="2",style=discord.ButtonStyle.blurple)
    async def blurple2_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        return await self.clicked(interaction, 1)
    @discord.ui.button(label="3",style=discord.ButtonStyle.blurple)
    async def blurple3_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        return await self.clicked(interaction, 2)

class EmbedView(discord.ui.LayoutView):
    def __init__(self, myText: str) -> None:
        super().__init__(timeout=None)
        self.text = discord.ui.TextDisplay(myText)
        container = discord.ui.Container(self.text, accent_color=discord.Color.red())
        self.add_item(container)

class TradeView(discord.ui.LayoutView):
    def __init__(self, trade, msg: discord.Message, initiator: discord.Member, recipient: discord.Member) -> None:
        super().__init__()
        self.trade = trade
        self.initiator = initiator
        self.recipient = recipient
        self.initReady = False
        self.reciReady = False
        self.initCards = []
        self.reciCards = []
        self.msg = msg
        self.name = discord.ui.TextDisplay(f"Trade between {initiator.mention} and {recipient.mention}")
        self.above = discord.ui.TextDisplay(f"{initiator.mention}'s cards:")
        self.below = discord.ui.TextDisplay(f"{recipient.mention}'s cards:")
        self.sep = discord.ui.Separator(visible=True)
        self.row = MyActionRow(self)

        self.container = discord.ui.Container(self.name,self.sep,self.above,self.sep,self.below,self.sep,self.row,accent_color=discord.Color.red())
        self.add_item(self.container)

    async def addCard(self, isInit: bool, card: str):
        self.initReady = False
        self.reciReady = False
        if isInit:
            if card in self.initCards:
                self.initCards.remove(card)
            else:
                self.initCards.append(card)
            msg = f"{self.initiator.mention}'s cards:"
            for card in self.initCards:
                msg += ("\n" + Card(card).toString())
            self.above = discord.ui.TextDisplay(msg)
            self.below = discord.ui.TextDisplay(self.below.content.removesuffix("\n\nREADY"))
        else:
            if card in self.reciCards:
                self.reciCards.remove(card)
            else:
                self.reciCards.append(card)
            msg = f"{self.recipient.mention}'s cards:"
            for card in self.reciCards:
                msg += ("\n" + Card(card).toString())
            self.below = discord.ui.TextDisplay(msg)
            self.above = discord.ui.TextDisplay(self.above.content.removesuffix("\n\nREADY"))

        return await self.update()

    async def update(self):
        self.remove_item(self.container)
        self.container = discord.ui.Container(self.name,self.sep,self.above,self.sep,self.below,self.sep,self.row,accent_color=discord.Color.red())
        self.add_item(self.container)
        return await self.msg.edit(view=self)

    async def ready(self, isInit: bool):
        if (isInit and self.initReady) or (not isInit and self.reciReady):
            return
        
        if isInit:
            self.initReady = True
            self.above = discord.ui.TextDisplay(f"{self.above.content}\n\nREADY")
        else:
            self.reciReady = True
            self.below = discord.ui.TextDisplay(f"{self.below.content}\n\nREADY")

        await self.update()

        if (self.initReady and self.reciReady):
            await self.trade.complete(self.initiator, self.initCards, self.recipient, self.reciCards)
            return await self.msg.edit(view=EmbedView(myText="This trade has concluded"))
        

    async def cancel(self):
        await self.msg.channel.send(content=f"The trade between {self.initiator.mention} and {self.recipient.mention} has been cancelled.")
        self.trade.remove(self.initiator)
        self.trade.remove(self.recipient)
        return await self.msg.delete()

class MyActionRow(discord.ui.ActionRow):
    def __init__(self, trade: TradeView) -> None:
        super().__init__()
        self.trade = trade

    @discord.ui.button(label='Ready', style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user != self.trade.initiator and interaction.user != self.trade.recipient:
            return await interaction.response.send_message(content="You are not part of this trade",ephemeral=True)
        await interaction.response.send_message(content="Success",ephemeral=True,delete_after=1)
        return await self.trade.ready(interaction.user == self.trade.initiator)

    #Removes the player from the queue when they press the remove button
    @discord.ui.button(label='Cancel',style=discord.ButtonStyle.red)
    async def remove(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user != self.trade.initiator and interaction.user != self.trade.recipient:
            return await interaction.response.send_message(content="You are not part of this trade",ephemeral=True)
        await interaction.response.send_message(content="Success",ephemeral=True,delete_after=1)
        return await self.trade.cancel()
