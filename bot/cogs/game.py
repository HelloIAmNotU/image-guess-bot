import discord
import random
from discord import app_commands
from discord.ext import commands
from PIL import Image
import requests
import io
import time

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

            
"""
    @app_commands.command(name="setup", description="Sets up the bot for future game")
    async def creategame(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Create the channels
        category_override = { # Ensures that the access role can see the category
            interaction.guild.default_role: discord.PermissionOverwrite(
                view_channel=False, 
                send_messages=False
            ),
            access_role: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=False
            ),
            admin_role: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=True
            )
        }
        category = await interaction.guild.create_category(game_name, overwrites=category_override, reason=None)
        general_override = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                view_channel=False, 
                send_messages=False
            ),
            access_role: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=True
            ),
            admin_role: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=True
            )
        }

        await interaction.guild.create_text_channel(name = f"{game_name}-annnouncements", category=category)
        await interaction.guild.create_text_channel(name = f"{game_name}-general", overwrites = general_override, category=category)

        try:
            await db.connect()
            await db.execute("INSERT INTO game_configuration (game_name, guild, category, players_per_team, team_count, role_count) VALUES ($1, $2, $3, $4, $5, $6);", game_name, interaction.guild_id, category.id, players_per_team, teams, num_roles if role_based_matchmaking else 1)
            await db.close()
        except:
            return await interaction.followup.send(view=EmbedView(myText="Unable to add game to database"),ephemeral=True)

        if not role_based_matchmaking:
            return await interaction.followup.send(view=EmbedView(myText="Finished setting up game."),ephemeral=True)
        
        def check_user(m: discord.Message) -> bool:
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            await db.connect()
        except:
            return await interaction.followup.send(view=EmbedView(myText="Couldn't re-connect to DB for role info."),ephemeral=True)

        for role_number in range(num_roles + 1):
            await interaction.followup.send(f"Send the name of role {role_number + 1}")
            user_reply = await self.bot.wait_for('message', check=check_user, timeout=30)
            
            try:
                await db.execute("INSERT INTO role_information (game_name, role_name) VALUES ($1, $2);", game_name, user_reply.content.strip())
            except:
                return await interaction.followup.send(view=EmbedView(myText="Unable to insert role information into database"),ephemeral=True)

        await db.close()
        await interaction.followup.send(view=EmbedView(myText="Finished setting up game."),ephemeral=True)
    
    # This command now works as intended. Nice!
    @group.command(name="delete", description="ADMIN ONLY: Stops given games in dropdown. The dropdown lasts for 60 seconds")
    async def deletegames(self, interaction: discord.Interaction):
        if not self.verifyAdmin(interaction.user):
            return await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"),ephemeral=True)
        try:
            await db.connect()
            record = await db.execute("SELECT * FROM game_configuration WHERE guild = $1;",interaction.guild_id)
            await db.close()
        except:
            return await interaction.response.send_message(view=EmbedView(myText="Accessing database failed."),ephemeral=True)
        if len(record) == 0:
            return await interaction.response.send_message(view=EmbedView(myText="No games found in this server."),ephemeral=True)
        
        class Dropdown(discord.ui.Select):
            def __init__(self) -> None:
                options = []
                for game in record:
                    options.append(discord.SelectOption(label=game['game_name']))
                super().__init__(placeholder="Choose a game to delete!",min_values=1,max_values=1,options=options)
            async def callback(self, interaction: discord.Interaction) -> None:
                for game in record:
                    if game['game_name'] != self.values[0]:
                        continue
                    try:
                        category = await interaction.guild.fetch_channel(game['category'])
                        for channel in category.channels:
                            await channel.delete()
                        await category.delete()
                    except:
                        return await interaction.response.send_message(view=EmbedView(myText="Removal failed."),ephemeral=True)
                    break
                await db.connect()
                await db.execute("DELETE FROM game_configuration WHERE game_name = $1;",self.values[0])
                await db.close()
                await interaction.response.send_message(view=EmbedView(myText="Removal succeeded!"),ephemeral=True)

        class DropdownView(discord.ui.View):
            def __init__(self) -> None:
                super().__init__(timeout=180)
                self.add_item(Dropdown())

        await interaction.response.send_message(view=DropdownView(),ephemeral=True,delete_after=60)
        """
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Game(bot))