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

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handles reactions being added to messages."""
        ctx: commands.Context = await self.get_context(reaction.message)
        match, discordMessage, canContinue = await self.getMatchData(ctx)

        if discordMessage is None or discordMessage['matchMessageId'] != reaction.message.id or user == bot.user:
            return     
        if user.mention not in [player['mention'] for player in match.players] or reaction.emoji not in discordMessage['reactions'] or not canContinue:
            await reaction.message.remove_reaction(reaction, user)
            return

        await reaction.message.remove_reaction(reaction, user)
        if reaction.emoji == '🇼':
            await self.get_cog('Ongoing Match')._won(ctx)
        elif reaction.emoji == '🇱':
            await self.get_cog('Ongoing Match')._lost(ctx)
        elif reaction.emoji == '⚔️':
            if match.currRound == 0:
                await self.get_cog('Ongoing Match')._startAttack(ctx)
            elif (match.currRound == 6 and match.scores["red"] == 3):
                await self.get_cog('Ongoing Match')._won(ctx, 'attack')
            elif (match.currRound == 6 and match.scores["blue"] == 3):
                await self.get_cog('Ongoing Match')._lost(ctx, 'attack')
            else:
                print('Unknown reaction/match state combination: ⚔️', match.currRound, match.scores)
        elif reaction.emoji == '🛡️':
            if match.currRound == 0:
                await self.get_cog('Ongoing Match')._startDefense(ctx)
            elif (match.currRound == 6 and match.scores["red"] == 3):
                await self.get_cog('Ongoing Match')._won(ctx, 'defense')
            elif (match.currRound == 6 and match.scores["blue"] == 3):
                await self.get_cog('Ongoing Match')._lost(ctx, 'defense')
            else:
                print('Unknown reaction/match state combination: 🛡️', match.currRound, match.scores)
        elif reaction.emoji == '🔁':
            await self.get_cog('Ongoing Match')._reshuffle(ctx)
        elif reaction.emoji == '👍':
            await ctx.send('Starting **!another** match...')
            await self.get_cog('Match Management')._another(ctx)
        elif reaction.emoji == '👎':
            await self.get_cog('Match Management')._goodnight(ctx)
        else:
            print('Unknown reaction:', reaction.emoji)
            return

    def resetDiscordMessage(self, serverId: str):
        self.cursor.execute("DELETE FROM matches WHERE server_id = ?", (serverId,))
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
            },
            'reactions': []
        }

    async def sendMessage(self, ctx: commands.Context, discordMessage, forgetMatch=False):
        message = '\n'.join([v for v in discordMessage['messageContent'].values() if v != ''])

        if discordMessage['matchMessageId']:
            matchMessage = await ctx.channel.fetch_message(discordMessage['matchMessageId'])
            await matchMessage.edit(content=message)
        else:
            matchMessage = (await ctx.send(message))
            discordMessage['matchMessageId'] = matchMessage.id
        
        await self._manageReactions(matchMessage, discordMessage)

        if forgetMatch:
            self.resetDiscordMessage(ctx.guild.id)
            return

        self.saveDiscordMessage(ctx, discordMessage)
    
    async def _manageReactions(self, message: discord.Message, discordMessage):
        currentReactions = [r.emoji for r in message.reactions]

        if not any(reaction in discordMessage['reactions'] for reaction in currentReactions):
            await message.clear_reactions()
        else:
            for reaction in reversed(currentReactions):
                if reaction not in discordMessage['reactions']:
                    await message.clear_reaction(reaction)

        for reaction in discordMessage['reactions']:
            if reaction in currentReactions:
                reaction = next((r for r in message.reactions if r.emoji == reaction), None)
                if reaction and reaction.count > 1:
                    users = [user async for user in reaction.users()]
                    for user in users[1:]:
                        await message.remove_reaction(reaction, user)
            else:
                await message.add_reaction(reaction)
    
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
        """Gets the match data and discord message from the database. If there is no match in progress, it will return a message to the user. If there is a match in progress, it will return the match data and discord message."""
        serverId = str(ctx.guild.id)
        matchData, discordMessage = None, None
        result = self.cursor.execute("SELECT match_data, discord_message FROM matches WHERE server_id = ?", (serverId,)).fetchone()

        if result is not None:
            matchData, discordMessage = result
            matchData = json.loads(matchData) if matchData is not None else None
            discordMessage = json.loads(discordMessage) if discordMessage is not None else self.resetDiscordMessage(ctx.guild.id)
        else:
            discordMessage = self.resetDiscordMessage(ctx.guild.id)

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
