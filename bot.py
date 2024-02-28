import discord
import json
import os
import re
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv
from botHelp import CustomHelpCommand
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
        self.setupBotCommands()

    async def on_ready(self):
        print(f'Logged in as {bot.user}')
        await bot.load_extension('cogs.general')
        await bot.load_extension('cogs.matchSetup')
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='for !startMatch'))

    def setupBotCommands(self):
        @self.command(name='ban')
        async def _ban(ctx, *operators):
            """Bans operators from the match. Use **!ban op1 op2...** to ban the mentioned operators from the match. You can ban as many operators as you like."""
            await self._banUnban(ctx, *operators, ban=True)

        @self.command(name='unban')
        async def _unban(ctx, *operators):
            """Unbans operators from the match. Use **!unban op1 op2...** to unban the mentioned operators from the match."""
            await self._banUnban(ctx, *operators, ban=False)

        @self.command(aliases=['setMap', 'map'])
        async def _setMap(ctx, *mapName):
            """Sets the map for the match. This will influence the sites displayed for defensive rounds. Use **!setMap map** to set the map. A map can be set at any point in the match."""
            match, discordMessage, canContinue = await self._getMatchData(ctx)
            if not canContinue:
                return
            await ctx.message.delete()

            if len(mapName) == 0:
                discordMessage['messageContent']['actionPrompt'] = 'You must specify a map. Use "**!setMap map**" to try again.'
                await bot._sendMessage(ctx, discordMessage)
                return

            discordMessage['messageContent']['actionPrompt'] = ''
            mapName = ' '.join(mapName)
            couldSetMap = match.setMap(mapName)
            if couldSetMap:
                discordMessage['messageContent']['playersBanner'] = f"Playing a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
            else:
                discordMessage['messageContent']['actionPrompt'] += f'**{mapName}** is not a valid map. Use "**!setMap map**" to try again.\n'

            if match.currRound == 0:
                if not match.bannedOperators:
                    discordMessage['messageContent']['actionPrompt'] += 'Use "**!ban op1 op2...**" or use "**!attack**" or "**!defense**" to start the match.'
                else:
                    discordMessage['messageContent']['actionPrompt'] += 'Use "**!attack**" or "**!defense**" to start the match.'
            else:
                discordMessage['messageContent']['actionPrompt'] += 'Use "**!won**" or "**!lost**" to continue.'

            self._saveMatch(ctx, match)
            await bot._sendMessage(ctx, discordMessage)

        @self.command(aliases=['attack', 'startAttack'])
        async def _startAttack(ctx):
            """Starts the match on attack."""
            await ctx.message.delete()
            await self._playMatch(ctx, 'attack')

        @self.command(aliases=['defense', 'startDefense', 'defend'])
        async def _startDefense(ctx):
            """Starts the match on defense."""
            await ctx.message.delete()
            await self._playMatch(ctx, 'defense')

        @self.command(name='won')
        async def _won(ctx, overtimeSide=None):
            """Marks the current round as won and starts a new round. If winning starts overtime, you must specify the side you start overtime on with **!won attack** or **!won defense**."""
            match, discordMessage, canContinue = await self._getMatchData(ctx)
            if not canContinue:
                return
            await ctx.message.delete()

            if not match.playingOnSide:
                discordMessage['messageContent']['actionPrompt'] = 'You must specify what side you start on. Use **!attack** or **!defense**.'
                await bot._sendMessage(ctx, discordMessage)
                return

            if (match.currRound == 6 and match.scores["red"] == 3):
                if not overtimeSide:
                    discordMessage['messageContent']['actionPrompt'] = 'You must specify what side you start overtime on. Use **!won attack** or **!won defense**.'
                    await bot._sendMessage(ctx, discordMessage)
                    return

            if match.resolveRound('won', overtimeSide):
                self._saveMatch(ctx, match)
                self._saveDiscordMessage(ctx, discordMessage)
                await self._playRound(ctx)
            else:
                self._saveMatch(ctx, match)
                self._saveDiscordMessage(ctx, discordMessage)
                await self._endMatch(ctx)

        @self.command(name='lost')
        async def _lost(ctx, overtimeSide=None):
            """Marks the current round as lost and starts a new round. If losing starts overtime, you must specify the side you start overtime on with **!lost attack** or **!lost defense**."""
            match, discordMessage, canContinue = await self._getMatchData(ctx)
            if not canContinue:
                return
            await ctx.message.delete()

            if not match.playingOnSide:
                discordMessage['messageContent']['actionPrompt'] = 'You must specify what side you start on. Use **!attack** or **!defense**.'
                await bot._sendMessage(ctx, discordMessage)
                return

            if (match.currRound == 6 and match.scores["blue"] == 3):
                if not overtimeSide:
                    discordMessage['messageContent']['actionPrompt'] = 'You must specify what side you start overtime on. Use **!lost attack** or **!lost defense**.'
                    await bot._sendMessage(ctx, discordMessage)
                    return

            if match.resolveRound('lost', overtimeSide):
                self._saveMatch(ctx, match)
                self._saveDiscordMessage(ctx, discordMessage)
                await self._playRound(ctx)
            else:
                self._saveMatch(ctx, match)
                self._saveDiscordMessage(ctx, discordMessage)
                await self._endMatch(ctx)

        @self.command(aliases=['reshuffle', 'shuffle'])
        async def _reshuffle(ctx):
            """Reshuffles the operator choices and site (if playing on defense) for the current round. You can reshuffle up to twice per match."""
            match, discordMessage, canContinue = await self._getMatchData(ctx)
            if not canContinue:
                return
            await ctx.message.delete()

            if match.reshuffles >= 2:
                discordMessage['messageContent']['actionPrompt'] = 'You cannot reshuffle more than twice per match. Next time, choose more carefully!\nUse **!won** or **!lost** to continue.'
                await bot._sendMessage(ctx, discordMessage)
                return

            if match.currRound == 0:
                discordMessage['messageContent']['actionPrompt'] = 'You can only reshuffle the lineup after the first round has started.\nUse **!attack** or **!defense** to start the first round.'
                await bot._sendMessage(ctx, discordMessage)
                return

            match.reshuffles += 1
            self._saveMatch(ctx, match)
            await self._playRound(ctx)

    async def _banUnban(self, ctx, *operators, ban=True):
        match, discordMessage, canContinue = await self._getMatchData(ctx)
        if not canContinue:
            return
        await ctx.message.delete()

        bans = ' '.join(operators)
        sanitizedBans = match.banOperators(bans, ban)

        if match.bannedOperators == []:
            discordMessage['messageContent']['banMetadata'] = 'No operators are banned in this match.\n'
        else:
            discordMessage['messageContent']['banMetadata'] = f'The following operators are banned in this match:\n{", ".join([f"**{op}**" for op in match.bannedOperators])}\n'
            unrecognizedBans = [ban for ban in zip(sanitizedBans, operators) if ban[0] is None]
            if len(unrecognizedBans) > 0:
                if ban:
                    discordMessage['messageContent']['banMetadata'] += f'The following operators were not recognized:\n{", ".join([f"**{ban[1]}**" for ban in unrecognizedBans])}\n'
                else:
                    discordMessage['messageContent']['banMetadata'] += f'The following operators were not recognized, or not banned:\n{", ".join([f"**{ban[1]}**" for ban in unrecognizedBans])}\n'

        if match.currRound == 0:
            discordMessage['messageContent']['actionPrompt'] = ''
            if not match.map:
                discordMessage['messageContent']['actionPrompt'] += 'Next, use "**!setMap map**" to set the map.\n'
            discordMessage['messageContent']['actionPrompt'] += 'You can also "**!ban**" or "**!unban**" more operators.\n'
            discordMessage['messageContent']['actionPrompt'] += 'Use "**!attack**" or "**!defense**" to start the match.'
        else:
            discordMessage['messageContent']['actionPrompt'] = 'Use "**!won**" or "**!lost**" to continue.'

        self._saveMatch(ctx, match)
        await bot._sendMessage(ctx, discordMessage)

    async def _playMatch(self, ctx, side):
        match, discordMessage, canContinue = await self._getMatchData(ctx)
        if not canContinue:
            return

        if match == None:
            discordMessage['messageContent']['playersBanner'] = 'No match in progress. Use "**!startMatch @player1 @player2...**" to start a new match.'
            await bot._sendMessage(ctx, True)
            return
        
        discordMessage['messageContent']['playersBanner'] = f"Playing a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        
        if side == 'attack':
            match.playingOnSide = 'attack'
        else:
            match.playingOnSide = 'defense'

        if match.currRound == 0:
                match.currRound = 1

        self._saveMatch(ctx, match)
        self._saveDiscordMessage(ctx, discordMessage)
        await self._playRound(ctx)

    async def _playRound(self, ctx):
        match, discordMessage, canContinue = await self._getMatchData(ctx)
        if not canContinue:
            return

        discordMessage['messageContent']['playersBanner'] = f"Playing a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        discordMessage['messageContent']['matchScore'] = f'The score is **{match.scores["blue"]}**:**{match.scores["red"]}**, we are playing on **{match.playingOnSide}**.\n'
        discordMessage['messageContent']['banMetadata'] = ''
        discordMessage['messageContent']['roundMetadata'] = f'Here is your lineup for round {match.currRound}:'

        operators = match.getPlayedOperators(match.playingOnSide)
        if match.playingOnSide == 'defense':
            site = match.getPlayedSite()
            discordMessage['messageContent']['roundMetadata'] += f'\nChoose the **{site}** site.'

        discordMessage['messageContent']['roundLineup'] = ''
        operators_copy = operators.copy()
        for player, operator in zip(match.players, operators_copy):
            discordMessage['messageContent']['roundLineup'] += f'{player["mention"]} plays **{operator}**\n'
            operators.remove(operator)
        
        if(operators):
            discordMessage['messageContent']['roundLineup'] += f'Backup operators: **{", ".join(operators)}**\n'

        discordMessage['messageContent']['actionPrompt'] = ''
        if match.reshuffles < 2:
            discordMessage['messageContent']['actionPrompt'] += f'Use **!reshuffle** to get new choices (**{2 - match.reshuffles}** remaining).\n'
        if match.currRound != 6:
            discordMessage['messageContent']['actionPrompt'] += 'Use "**!won**" or "**!lost**" to continue.'
        elif match.scores["red"] == 3:
            discordMessage['messageContent']['actionPrompt'] += 'If you won, use "**!won attack**" (or "**!won defense**") to start overtime on the specified side, otherwise use **!lost** to end the match.'
        elif match.scores["blue"] == 3:
            discordMessage['messageContent']['actionPrompt'] += 'If you lost, use "**!lost attack**" (or "**!lost defense**") to start overtime on the specified side, otherwise use **!won** to end the match.'

        self._saveMatch(ctx, match)
        await bot._sendMessage(ctx, discordMessage)

    async def _endMatch(self, ctx):
        match, discordMessage, canContinue = await self._getMatchData(ctx)
        if not canContinue:
            return

        discordMessage['messageContent']['roundMetadata'] = ''
        discordMessage['messageContent']['roundLineup'] = ''
        discordMessage['messageContent']['playersBanner'] = f"Finished a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        discordMessage['messageContent']['matchScore'] = f'The match is over! The final score was **{match.scores["blue"]}**:**{match.scores["red"]}**.'
        discordMessage['messageContent']['actionPrompt'] = 'Use "**!another**" to start a new match with the same players or "**!goodnight**" to end the session.'

        self._saveMatch(ctx, match)
        await bot._sendMessage(ctx, discordMessage)

    def _validatePlayerNames(self, ctx, playerNames):
        playerIds = [re.findall(r'\d+', name) for name in playerNames if name.startswith('<@')]
        playerIds = [item for sublist in playerIds for item in sublist]

        members = [str(member.id) for member in ctx.guild.members]

        playerObjects = []
        for playerId in playerIds:
            if playerId not in members:
                return None
            else:
                playerObjects.append(ctx.guild.get_member(int(playerId)))

        return playerObjects

    def _resetDiscordMessage(self, ctx):
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

    async def _sendMessage(self, ctx, discordMessage, forgetMessage=False):
        message = '\n'.join([v for v in discordMessage['messageContent'].values() if v != ''])

        if discordMessage['matchMessageId']:
            match_message = await ctx.channel.fetch_message(discordMessage['matchMessageId'])
            await match_message.edit(content=message)
        else:
            discordMessage['matchMessageId'] = (await ctx.send(message)).id
        if forgetMessage:
            self._resetDiscordMessage(ctx)
            return

        self._saveDiscordMessage(ctx, discordMessage)
    
    def _saveMatch(self, ctx, match):
        serverId = str(ctx.guild.id)
        matchData = json.dumps(match.__dict__)
        self.cursor.execute("UPDATE matches SET match_data = ? WHERE server_id = ?", (matchData, serverId))
        self.conn.commit()

    def _saveDiscordMessage(self, ctx, discordMessage):
        serverId = str(ctx.guild.id)
        discordMessage = json.dumps(discordMessage)
        self.cursor.execute("UPDATE matches SET discord_message = ? WHERE server_id = ?", (discordMessage, serverId))
        self.conn.commit()

    async def _getMatchData(self, ctx):
        serverId = str(ctx.guild.id)
        matchData, discordMessage = None, None
        result = self.cursor.execute("SELECT match_data, discord_message FROM matches WHERE server_id = ?", (serverId,)).fetchone()

        if result is not None:
            matchData, discordMessage = result
            matchData = json.loads(matchData) if matchData is not None else None
            discordMessage = json.loads(discordMessage) if discordMessage is not None else self._resetDiscordMessage(ctx)
        else:
            discordMessage = self._resetDiscordMessage(ctx)

        if matchData is None:
            discordMessage['messageContent']['playersBanner'] = 'No match in progress. Use "**!startMatch @player1 @player2...**" to start a new match.'
            await bot._sendMessage(ctx, discordMessage, True)
            return None, None, False

        match = RainbowMatch(matchData)
        return match, discordMessage, True

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    bot = RainbowBot()
    bot.help_command = CustomHelpCommand()
    bot.run(TOKEN)
