import discord
import random

from helpers.card import Card

class Buttons(discord.ui.View):
    def __init__(self, collect, names: list[str], user: discord.Member, msg: discord.WebhookMessage, timeout=60):
        self.names = names
        self.collect = collect
        self.user = user
        self.msg = msg
        super().__init__(timeout=timeout)

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