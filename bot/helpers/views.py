import discord
import random

from helpers.card import Card

class Buttons(discord.ui.View):
    def __init__(self, collect, names: list[str], timeout=45):
        self.names = names
        self.collect = collect
        super().__init__(timeout=timeout)

    async def clicked(self, interaction: discord.Interaction, index: int):
        curid = await self.collect.cardcount(self.names[index])
        qualityrand = random.randrange(0,200)
        qualityrand = 4 if qualityrand == 0 else 3 if qualityrand <= 17 else 2 if qualityrand <= 33 else 1 if qualityrand <= 50 else 0
        card = Card(self.names[index].capitalize(),random.randrange(0,5),qualityrand,curid+1)
        await self.collect.insertcard(interaction.user.id, card.compress())
        await self.collect.setcount(self.names[index], curid+1)
        message = f"{interaction.user.mention} has grabbed {self.names[index].capitalize()}. "
        if card.quality == 4:
            message += "Nice! "
        message += f"It's in {card.quality_arr[card.quality]} condition."
        if card.edition != 0:
            message += f"\nWow! Your card has a {card.edition_arr[card.edition]} edition!"
        await interaction.channel.send(content=message)
        for child in self.children:
            child.disabled = True
        return await interaction.response.edit_message(view=self)

    @discord.ui.button(label="1",style=discord.ButtonStyle.blurple)
    async def blurple1_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        return await self.clicked(interaction, 0)
    @discord.ui.button(label="2",style=discord.ButtonStyle.blurple)
    async def blurple2_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        return await self.clicked(interaction, 1)
    @discord.ui.button(label="3",style=discord.ButtonStyle.blurple)
    async def blurple3_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        return await self.clicked(interaction, 2)