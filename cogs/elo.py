import discord
from discord.ext import commands
from discord import app_commands
import json
import math

INITIAL_RATING = 5000
ELO_FILE = 'elo.json'

class EloCog(commands.Cog):

    elo_group = app_commands.Group(name="elo", description="Manage and view player ELO ratings")

    def __init__(self, client: commands.Bot):
        self.client = client
        self.elo_data = self.load_elo()

    def load_elo(self):
        try:
            with open(ELO_FILE, 'r') as file:
                data = json.load(file)

                for player, value in data.items():
                    if isinstance(value, float):
                        data[player] = {"rating": value, "wins": 0, "losses": 0}

                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_elo(self):
        with open(ELO_FILE, 'w') as file:
            json.dump(self.elo_data, file, indent=4)

    def get_elo(self, player_name):
        return self.elo_data.get(player_name, {
            "rating": INITIAL_RATING,
            "wins": 0,
            "losses": 0
        })

    def update_elo(self, player1_name, player2_name, score1, score2):
        player1_data = self.get_elo(player1_name)
        player2_data = self.get_elo(player2_name)

        elo1 = player1_data["rating"]
        elo2 = player2_data["rating"]
        deltaWins = score1 - score2

        WIN_SCALAR = 1.489896102405
        winFactor = .9 + ((abs(deltaWins) ** WIN_SCALAR) * .1)

        if (elo1 - elo2) * deltaWins > 0:
            eloFactor = abs((0 - abs(elo2 - elo1) + 500))
        else:
            eloFactor = abs(elo2 - elo1) + 500

        ELO_CHANGE_CONSTANT = .192
        eloChange = winFactor * max(0, eloFactor) * ELO_CHANGE_CONSTANT + 1
        INCENTIVE_ELO = ELO_CHANGE_CONSTANT / 78.125

        if score1 > score2:
            player1_data["rating"] += INCENTIVE_ELO + eloChange
            player2_data["rating"] -= eloChange
            player1_data["wins"] += 1
            player2_data["losses"] += 1
        else:
            player2_data["rating"] += INCENTIVE_ELO + eloChange
            player1_data["rating"] -= eloChange
            player2_data["wins"] += 1
            player1_data["losses"] += 1

        self.elo_data[player1_name] = player1_data
        self.elo_data[player2_name] = player2_data
        self.save_elo()

    @elo_group.command(name="winner", description="Record a match result between two Discord members")
    async def winner(self, interaction: discord.Interaction, player1: discord.Member, player2: discord.Member, score1: int, score2: int):
        player1_name = player1.display_name
        player2_name = player2.display_name

        if player1_name not in self.elo_data:
            self.elo_data[player1_name] = {"rating": INITIAL_RATING, "wins": 0, "losses": 0}
        if player2_name not in self.elo_data:
            self.elo_data[player2_name] = {"rating": INITIAL_RATING, "wins": 0, "losses": 0}

        self.update_elo(player1_name, player2_name, score1, score2)

        player1_elo = math.ceil(self.elo_data[player1_name]["rating"])
        player2_elo = math.ceil(self.elo_data[player2_name]["rating"])

        await interaction.response.send_message(
            f"ELO ratings updated! {player1_name} vs. {player2_name}. New ELO's are: "
            f"{player1_name}: {player1_elo}, {player2_name}: {player2_elo}."
        )

    @elo_group.command(name="leaderboard", description="Display the ELO leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        sorted_elo = sorted(self.elo_data.items(), key=lambda item: item[1]["rating"], reverse=True)
        leaderboard_embed = discord.Embed(title="ELO Leaderboard", color=discord.Color.blue())

        for index, (player_name, data) in enumerate(sorted_elo, start=1):
            rating = math.ceil(data["rating"])
            wins = data["wins"]
            losses = data["losses"]
            total_games = wins + losses
            win_percentage = (wins / total_games * 100) if total_games > 0 else 0
            position = ["🥇 1st", "🥈 2nd", "🥉 3rd"][index - 1] if index <= 3 else f"{index}th"
            leaderboard_embed.add_field(
                name=f"{position}",
                value=f"{player_name} (ELO: {rating})\n"
                      f"Wins: {wins}, Losses: {losses}, Win%: {win_percentage:.2f}%",
                inline=False
            )

        await interaction.response.send_message(embed=leaderboard_embed)

    @elo_group.command(name="add-player", description="Add a new player with default ELO")
    async def add_player(self, interaction: discord.Interaction, player_name: str):
        if player_name not in self.elo_data:
            self.elo_data[player_name] = {"rating": INITIAL_RATING, "wins": 0, "losses": 0}
            self.save_elo()
            await interaction.response.send_message(f"Player {player_name} added with default ELO of {INITIAL_RATING}.")
        else:
            await interaction.response.send_message(
                f"Player {player_name} already exists with an ELO of {self.elo_data[player_name]['rating']}.")

    @elo_group.command(name="remove-player", description="Remove a player from the ELO system")
    async def remove_player(self, interaction: discord.Interaction, player_name: str):
        if player_name in self.elo_data:
            del self.elo_data[player_name]
            self.save_elo()
            await interaction.response.send_message(f"Player {player_name} has been removed from the ELO system.")
        else:
            await interaction.response.send_message(f"Player {player_name} does not exist in the ELO system.")

async def setup(client: commands.Bot):
    await client.add_cog(EloCog(client))