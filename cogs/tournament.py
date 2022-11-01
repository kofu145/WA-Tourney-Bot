import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
sys.path.insert(0, "..")
from osuapi.osu_wrapper import OsuWrapper
from tourneydata import datamanager

class Tournament(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Tournament cog loaded!")

    @app_commands.command(name="leaderboard", description="Combined individual score leaderboard of all users!")
    async def app_command_leaderboard(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"Washington Arena Suiji Bonanza score leaderboard!",
                              description="Ranked lowest to highest")

        score_leaderboard = self.bot.data_manager.get_leaderboards()
        sorted_leaderboard = dict(reversed(sorted(score_leaderboard.items(), key=lambda item: item[1])))
        count = 0
        for key, value in sorted_leaderboard.items():
            if count > 9:
                await interaction.response.send_message(embed=embed)

                break
            embed.add_field(name=f"{count + 1}: {self.bot.data_manager.get_user(key)['username']}",
                            value=f"Total Score: {value}", inline=count % 2 == 0)
            count += 1

    @app_commands.command(name="results", description="View match results!")
    async def results(self, interaction: discord.Interaction, match_id: str = "None"):


        if match_id == "None":
            embed = discord.Embed(title=f"Washington Arena: Suiji Bonanza", type="rich", url=None, description="Match results")
            embed.add_field(name="Pick out a match result from the dropdown below to view it!", value="(This is a test function)")
            view = TournamentResultsSelection(bot=self.bot, match_data=None, main_embed=embed, isSelection=True, timeout=180)

            await interaction.response.send_message(embed=embed, view=view)
        else:
            if "https://osu.ppy.sh/community/matches/" in match_id:
                match_id = match_id.split("/")[-1]
            is_local = True if int(match_id) < 1000 else False

            match_data = self.bot.data_manager.get_match(int(match_id), is_local)

            red_pts = 0
            blue_pts = 0

            for map_result in self.bot.data_manager.parse_match_data(match_data):
                if map_result['red_score'] > map_result['blue_score']:
                    red_pts += 1
                elif map_result['blue_score'] > map_result['red_score']:
                    blue_pts += 1

            match_res = "**Red wins: " if red_pts > blue_pts else "**Blue wins: "
            match_res += f":red_square: {red_pts} | {blue_pts} :blue_square:**"

            embed = discord.Embed(title=f"{match_data['match']['name']}",
                type="rich",
                url=f"https://osu.ppy.sh/community/matches/{match_data['match']['id']}",
                description=match_res
            )

            if is_local:
                embed.add_field(name=f":red_square: **Team Red** :red_square:",
                    value=f"{self.bot.data_manager.get_team(match_data['suijidata']['teams']['red'])['name']}",
                    inline=True
                )

                embed.add_field(name=f":blue_square: **Team Blue** :blue_square:",
                    value=f"{self.bot.data_manager.get_team(match_data['suijidata']['teams']['blue'])['name']}",
                    inline=True
                )

            count = 1
            for map_result in self.bot.data_manager.parse_match_data(match_data):

                value_str = f"{count}: :red_square: **Score: {map_result['red_score']}** | **:blue_square: Score: {map_result['blue_score']}**\n"
                if map_result['red_score'] > map_result['blue_score']:
                    value_str += f"Red won by {map_result['red_score'] - map_result['blue_score']} pts"
                    red_pts += 1
                elif map_result['blue_score'] > map_result['red_score']:
                    value_str += f"Blue won by {map_result['blue_score'] - map_result['red_score']} pts\n"
                    blue_pts += 1

                #for score in map_result["scores"]:
                #    value_str += score + "\n"

                print(map_result["name"])
                embed.add_field(name=f"{map_result['name']}",
                    value=value_str,
                    inline=False
                )
                count += 1

            embed.set_image(url=self.bot.data_manager.parse_match_data(match_data)[0]['image_url'])
            embed.set_footer(text="You can press the buttons corresponding to each score to learn more about them!", icon_url=None)
            view = TournamentResultsSelection(bot=self.bot, match_data=match_data, main_embed=embed, isSelection=False, timeout=180)
            await interaction.response.send_message(embed=embed, view=view)


    @commands.command()
    async def sync(self, ctx):
        print("entered command")
        if self.bot.data_manager.validate_staff(ctx.author.id):
            result = await ctx.bot.tree.sync()

            await ctx.send(f"synced {len(result)} commands")
        else:
            await ctx.send("You aren't allowed to use this!")

    @commands.command(description="Combined individual score leaderboard of all users!")
    async def leaderboard(self, ctx):
        embed = discord.Embed(title=f"Washington Arena Suiji Bonanza score leaderboard!",
            description="Ranked lowest to highest")

        score_leaderboard = self.bot.data_manager.get_leaderboards()
        sorted_leaderboard = dict(reversed(sorted(score_leaderboard.items(), key=lambda item: item[1])))
        count = 0
        for key, value in sorted_leaderboard.items():
            if count > 9:
                await ctx.send(embed=embed)
                break
            embed.add_field(name=f"{count + 1}: {self.bot.data_manager.get_user(key)['username']}", value=f"Total Score: {value}", inline=count %2==0)
            count += 1

    @leaderboard.error
    async def leaderboard_error(error, ctx):
        print("leaderboard error")
        print(f"{str(error)}")


    # imported test code for error handling, temporary
    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        print("This error was handled with option 2 from ?tag treeerrorcog")
        print(f"{str(error)}")


class TournamentResultsSelection(discord.ui.View):
    def __init__(self, *, bot=None, match_data=None, main_embed=None, isSelection=False, timeout=180):
        super().__init__(timeout=timeout)
        self.match_data = match_data
        self.bot = bot
        self.main_embed=main_embed
        self.selection = SelectMatch(bot)
        if isSelection:
            self.add_item(self.selection)
        else:
            self.add_beatmap_buttons()

    async def edit_selection_choice(self, match_data, embed, interaction):
        self.match_data = match_data
        self.main_embed = embed
        self.remove_item(self.selection)
        self.add_beatmap_buttons()
        await interaction.response.edit_message(embed=embed, view=self)


    def add_beatmap_buttons(self):
        count = 1
        for map_result in self.bot.data_manager.parse_match_data(self.match_data):

            self.add_item(TournamentResultButton(label=count,
                color=discord.ButtonStyle.red if map_result['red_score'] > map_result['blue_score'] else discord.ButtonStyle.blurple,
                map_result=map_result,
                match_data=self.match_data,
                bot=self.bot)
            )
            count += 1
        return_button = discord.ui.Button(label="Return to overview")

        async def return_callback(interaction):
            await interaction.response.edit_message(embed=self.main_embed, view=self)

        return_button.callback = return_callback

        self.add_item(return_button)

    async def on_error(self, error, item, interaction):
        await interaction.response.send_message(str(error))

    # @discord.ui.button(label="Test Button", style=discord.ButtonStyle.blurple)
    # async def test_blurple_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        # button.disabled = True
        # await interaction.response.send_message("I'm just a test button >///<")

class TournamentResultButton(discord.ui.Button):
    def __init__(self, label, color, map_result, match_data, bot):
        super().__init__(label=label, style=color)
        self.count = int(label)
        self.map_result = map_result
        self.match_data = match_data
        self.bot = bot


    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.map_result['name']}",
            type="rich",
            url=self.map_result['url'],
            description=f"**{self.match_data['match']['name']}**"
        )
        for score in self.map_result["scores"]:
            mods = ""
            for mod in score['mods']:
                mods += mod
            value_str = f"{score['max_combo']}x +{mods} {round(score['accuracy'] * 100, 2)}%\nScore: {score['score']}"
            embed.add_field(
                name=f":{score['match']['team']}_square: {self.bot.data_manager.get_user(str(score['user_id']))['username']}",
                value=value_str,
                inline=(True if self.label not in [1, 4] else False)
            )
        value_str = ""
        if self.map_result['red_score'] > self.map_result['blue_score']:
            value_str += f"Red won by {self.map_result['red_score'] - self.map_result['blue_score']} pts"
        elif self.map_result['blue_score'] > self.map_result['red_score']:
            value_str += f"Blue won by {self.map_result['blue_score'] - self.map_result['red_score']} pts\n"
        embed.add_field(name=f":red_square: **Score: {self.map_result['red_score']}** | **:blue_square: Score: {self.map_result['blue_score']}**\n",
            value=value_str
        )
        embed.set_image(url=self.map_result['image_url'])

        await interaction.response.edit_message(embed=embed, view=self.view)

class SelectMatch(discord.ui.Select):
    def __init__(self, bot=None, timeout=180):
        self.bot=bot

        options = []
        for match_id, match in self.bot.data_manager.matches.items():

            options.append(discord.SelectOption(label=f"Match ID: {match_id}",
                emoji='🟥',# if match['red_score'] > match['blue_score'] else ':blue_square:',
                description=f"{match['match']['name']}"))
        super().__init__(placeholder="Matches", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # self.values[0][-1] would be the match id
        match_id = self.values[0][-1]
        match_data = self.bot.data_manager.get_match(int(match_id))

        red_pts = 0
        blue_pts = 0

        for map_result in self.bot.data_manager.parse_match_data(match_data):
            if map_result['red_score'] > map_result['blue_score']:
                red_pts += 1
            elif map_result['blue_score'] > map_result['red_score']:
                blue_pts += 1

        match_res = "**Red wins: " if red_pts > blue_pts else "**Blue wins: "
        match_res += f":red_square: {red_pts} | {blue_pts} :blue_square:**"

        embed = discord.Embed(title=f"{match_data['match']['name']}",
                              type="rich",
                              url=f"https://osu.ppy.sh/community/matches/{match_data['match']['id']}",
                              description=match_res
                              )


        embed.add_field(name=f":red_square: **Team Red** :red_square:",
                        value=f"{self.bot.data_manager.get_team(match_data['suijidata']['teams']['red'])['name']}",
                        inline=True
                        )

        embed.add_field(name=f":blue_square: **Team Blue** :blue_square:",
                        value=f"{self.bot.data_manager.get_team(match_data['suijidata']['teams']['blue'])['name']}",
                        inline=True
                        )

        count = 1
        for map_result in self.bot.data_manager.parse_match_data(match_data):

            value_str = f"{count}: :red_square: **Score: {map_result['red_score']}** | **:blue_square: Score: {map_result['blue_score']}**\n"
            if map_result['red_score'] > map_result['blue_score']:
                value_str += f"Red won by {map_result['red_score'] - map_result['blue_score']} pts"
            elif map_result['blue_score'] > map_result['red_score']:
                value_str += f"Blue won by {map_result['blue_score'] - map_result['red_score']} pts\n"

            # for score in map_result["scores"]:
            #    value_str += score + "\n"

            print(map_result["name"])
            embed.add_field(name=f"{map_result['name']}",
                            value=value_str,
                            inline=False
                            )
            count += 1

        embed.set_image(url=self.bot.data_manager.parse_match_data(match_data)[0]['image_url'])
        embed.set_footer(text="You can press the buttons corresponding to each score to learn more about them!",
                         icon_url=None)

        await self.view.edit_selection_choice(match_data, embed, interaction)


async def setup(bot):
    await bot.add_cog(Tournament(bot))
