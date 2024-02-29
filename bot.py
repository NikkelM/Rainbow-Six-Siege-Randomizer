import discord
import json
import os
import re
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv
from rainbow import RainbowMatch

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

class RainbowBot(commands.Bot):
    def __init__(self):
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect("data/rainbowDiscordBot.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                server_id TEXT PRIMARY KEY,
                match_data TEXT,
                discord_message TEXT
            )
        """)
        self.conn.commit()

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        commands.Bot.__init__(self, command_prefix='!', intents=intents, case_insensitive=True, help_command=commands.HelpCommand())

    async def on_ready(self):
        print(f'Logged in as {bot.user}')
        cogs_list = [
            'general',
            'matchManagement',
            'ongoingMatch',
        ]
        for cog in cogs_list:
            await bot.load_extension(f'cogs.{cog}')
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='!startMatch | !help'))

    def resetDiscordMessage(self, ctx: commands.Context):
        self.cursor.execute("DELETE FROM matches WHERE server_id = ?", (str(ctx.guild.id),))
        self.conn.commit()
        return {
            'matchMessageId': None,
            'messageContent': {
                'playersBanner': '',
                'matchScore': '',
                'banMetadata': '',
                'roundMetadata': '',
                'roundLineup': '',
                'actionPrompt': ''
            }
        }

    async def sendMessage(self, ctx: commands.Context, discordMessage, forgetMessage=False):
        message = '\n'.join([v for v in discordMessage['messageContent'].values() if v != ''])

        if discordMessage['matchMessageId']:
            match_message = await ctx.channel.fetch_message(discordMessage['matchMessageId'])
            await match_message.edit(content=message)
        else:
            discordMessage['matchMessageId'] = (await ctx.send(message)).id
        if forgetMessage:
            self.resetDiscordMessage(ctx)
            return

        self.saveDiscordMessage(ctx, discordMessage)
    
    def saveMatch(self, ctx: commands.Context, match):
        serverId = str(ctx.guild.id)
        matchData = json.dumps(match.__dict__)
        self.cursor.execute("UPDATE matches SET match_data = ? WHERE server_id = ?", (matchData, serverId))
        self.conn.commit()

    def saveDiscordMessage(self, ctx: commands.Context, discordMessage):
        serverId = str(ctx.guild.id)
        discordMessage = json.dumps(discordMessage)
        self.cursor.execute("UPDATE matches SET discord_message = ? WHERE server_id = ?", (discordMessage, serverId))
        self.conn.commit()

    async def getMatchData(self, ctx: commands.Context):
        serverId = str(ctx.guild.id)
        matchData, discordMessage = None, None
        result = self.cursor.execute("SELECT match_data, discord_message FROM matches WHERE server_id = ?", (serverId,)).fetchone()

        if result is not None:
            matchData, discordMessage = result
            matchData = json.loads(matchData) if matchData is not None else None
            discordMessage = json.loads(discordMessage) if discordMessage is not None else self.resetDiscordMessage(ctx)
        else:
            discordMessage = self.resetDiscordMessage(ctx)

        if matchData is None:
            discordMessage['messageContent']['playersBanner'] = 'No match in progress. Use "**!startMatch @player1 @player2...**" to start a new match.'
            await bot.sendMessage(ctx, discordMessage, True)
            return None, None, False

        match = RainbowMatch(matchData)
        return match, discordMessage, True

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    bot = RainbowBot()
    bot.run(TOKEN)
