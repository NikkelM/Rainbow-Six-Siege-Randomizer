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
        self.conn = sqlite3.connect("rainbowDiscordBot.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                server_id TEXT PRIMARY KEY,
                match_data TEXT,
                discord_message TEXT
            )
        """)
        # TODO: Create table for cross-match statistics
        self.conn.commit()

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        commands.Bot.__init__(self, command_prefix='!', intents=intents)
        self.setupBotCommands()

    async def on_ready(self):
        print(f'Logged in as {bot.user}')
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='for !startMatch'))

    def setupBotCommands(self):
        @self.command(name='startMatch')
        async def _startMatch(ctx, *playerNames):
            serverId = str(ctx.guild.id)
            matchData = self.cursor.execute("SELECT match_data FROM matches WHERE server_id = ?", (serverId,)).fetchone()

            if matchData is not None and matchData[0] is not None:
                await ctx.message.delete()
                discordMessage = self.cursor.execute("SELECT discord_message FROM matches WHERE server_id = ?", (serverId,)).fetchone()[0]
                discordMessage = json.loads(discordMessage)
                discordMessage['messageContent']['actionPrompt'] = 'A match is already in progress. Use **!another** to start a new match with the same players or **!goodnight** to end the session.'
                await bot._sendMessage(ctx, discordMessage)
                return

            match = RainbowMatch()
            discordMessage = self._resetDiscordMessage(ctx)
            self.cursor.execute("INSERT INTO matches (server_id, discord_message) VALUES (?, ?)", (serverId, json.dumps(discordMessage)))

            if len(playerNames) > 5:
                discordMessage['messageContent']['playersBanner'] = 'You can only start a match with up to **five** players! Use "**!startMatch @player1 @player2...**" to try again.'
                await bot._sendMessage(ctx, discordMessage)
                return
            elif len(playerNames) > 0:
                playerObjects = self._validatePlayerNames(ctx, playerNames)
                if playerObjects is not None:
                    match.setPlayers(playerObjects)
                    discordMessage['messageContent']['playersBanner'] = f"Starting a new match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
                else:
                    discordMessage['messageContent']['playersBanner'] = 'At least one of the players you mentioned is not on this server, please try again.'
                    await bot._sendMessage(ctx, discordMessage)
                    return
            else:
                discordMessage['messageContent']['playersBanner'] = 'You can start a match using "**!startMatch @player1 @player2...**".'
                await bot._sendMessage(ctx, discordMessage)
                return

            discordMessage['messageContent']['matchMetadata'] = f'Ban the **{match.getMapBan()}** map in rotation, and these operators:\n'
            attBans, defBans = match.getOperatorBanChoices()
            att1, att2 = attBans
            def1, def2 = defBans
            discordMessage['messageContent']['matchMetadata'] += f'Attack:    **{att1}** or if banned **{att2}**\n'
            discordMessage['messageContent']['matchMetadata'] += f'Defense: **{def1}** or if banned **{def2}**\n'

            discordMessage['messageContent']['actionPrompt'] = 'Next, use "**!setMap map**" and "**!ban op1 op2...**"'

            self._saveMatch(ctx, match)
            await bot._sendMessage(ctx, discordMessage)

        @self.command(name='addPlayers')
        async def _addPlayers(ctx, *playerNames):
            await ctx.message.delete()
            match, discordMessage, canContinue = await self._getMatchData(ctx)
            if not canContinue:
                return

            if len(playerNames) + len(match.players) > 5:
                discordMessage['messageContent']['playersBanner'] = f'A match can only have up to **five** players! **!removePlayers** first if you need to. Current players are {match.playersString}.\n'
                await bot._sendMessage(ctx, discordMessage)
                return
            elif len(playerNames) > 0:
                playerObjects = self._validatePlayerNames(ctx, playerNames)
                if playerObjects is not None:
                    match.setPlayers(playerObjects + match.players)
                    discordMessage['messageContent']['playersBanner'] = f"Player{'s' if len(playerNames) > 1 else ''} added! Current players are {match.playersString}.\n"
                else:
                    discordMessage['messageContent']['playersBanner'] = f'At least one of the players you mentioned is not on this server. Current players are {match.playersString}.\n'
                    await bot._sendMessage(ctx, discordMessage)
                    return
            else:
                discordMessage['messageContent']['playersBanner'] = f'No new player passed with the command. Current players are {match.playersString}.\n'
                await bot._sendMessage(ctx, discordMessage)
                return

            self._saveMatch(ctx, match)
            await bot._sendMessage(ctx, discordMessage)

        @self.command(name='removePlayers')
        async def _removePlayers(ctx, *playerNames):
            await ctx.message.delete()
            match, discordMessage, canContinue = await self._getMatchData(ctx)
            if not canContinue:
                return

            if len(playerNames) > 0:
                playerObjects = self._validatePlayerNames(ctx, playerNames)
                if playerObjects is not None:
                    removalSuccessful = match.removePlayers(playerObjects)
                    if not removalSuccessful:
                        discordMessage['messageContent']['playersBanner'] = f'You cannot remove all players from the match! Current players are {match.playersString}.\n'
                        await bot._sendMessage(ctx, discordMessage)
                        return
                    discordMessage['messageContent']['playersBanner'] = f"Player{'s' if len(playerNames) > 1 else ''} removed! Current players are {match.playersString}.\n"
                else:
                    discordMessage['messageContent']['playersBanner'] = f'At least one of the players you mentioned is not on this server. Current players are {match.playersString}.\n'
                    await bot._sendMessage(ctx, discordMessage)
                    return
            else:
                discordMessage['messageContent']['playersBanner'] = f'No player removed. Current players are {match.playersString}.\n'
                await bot._sendMessage(ctx, discordMessage)
                return

            self._saveMatch(ctx, match)
            await bot._sendMessage(ctx, discordMessage)

        @self.command(name='ban')
        async def _ban(ctx, *args):
            await self._banUnban(ctx, *args, ban=True)

        @self.command(name='unban')
        async def _unban(ctx, *args):
            await self._banUnban(ctx, *args, ban=False)

        @self.command(name='setMap')
        async def _setMap(ctx, *mapName):
            mapName = ' '.join(mapName)
            await ctx.message.delete()

            if self.match == None:
                self.messageContent['playersBanner'] = 'No match in progress. Use "**!startMatch**" to start a new match.'
                await bot._sendMessage(ctx, True)
                return
            self.messageContent['actionPrompt'] = ''
            couldSetMap = self.match.setMap(mapName)
            if couldSetMap == 2:
                self.messageContent['playersBanner'] = f"Playing a match with {self.match.playersString}{' on **' + self.match.map + '**' if self.match.map else ''}.\n"
            elif couldSetMap == 1:
                self.messageContent['actionPrompt'] += f'**{mapName}** is not a valid map. Use "**!setMap map**" to try again.\n'
            else:
                self.messageContent['actionPrompt'] += f'A map has already been set, you cannot change it anymore. Use "**!another**" to restart the match.\n'

            if self.match.currRound == 0:
                if not self.match.bannedOperators:
                    self.messageContent['actionPrompt'] += 'Use "**!ban op1 op2...**" or use "**!startAttack**" or "**!startDefense**" to start the match.'
                else:
                    self.messageContent['actionPrompt'] += 'Use "**!startAttack**" or "**!startDefense**" to start the match.'
            else:
                self.messageContent['actionPrompt'] += 'Use "**!won**" or "**!lost**" to continue.'
            await bot._sendMessage(ctx)

        @self.command(name='startAttack')
        async def _startAttack(ctx):
            await ctx.message.delete()
            await self._playMatch(ctx, 'attack')

        @self.command(name='startDefense')
        async def _startDefense(ctx):
            await ctx.message.delete()
            await self._playMatch(ctx, 'defense')

        @self.command(name='won')
        async def _won(ctx, overtimeSide=None):
            await ctx.message.delete()
            if not self.match.playingOnSide:
                self.messageContent['actionPrompt'] = 'You must specify what side you start on. Use **!startAttack** or **!startDefense**.'
                await bot._sendMessage(ctx)
                return

            if (self.match.currRound == 6 and self.match.scores["red"] == 3):
                if not overtimeSide:
                    self.messageContent['actionPrompt'] = 'You must specify what side you start overtime on. Use **!won attack** or **!won defense**.'
                    await bot._sendMessage(ctx)
                    return
            if self.match.resolveRound('won', overtimeSide):
                await self._playRound(ctx)
            else:
                await self._endMatch(ctx)

        @self.command(name='lost')
        async def _lost(ctx, overtimeSide=None):
            await ctx.message.delete()
            if not self.match.playingOnSide:
                self.messageContent['actionPrompt'] = 'You must specify what side you start on. Use **!startAttack** or **!startDefense**.'
                await bot._sendMessage(ctx)
                return

            if (self.match.currRound == 6 and self.match.scores["blue"] == 3):
                if not overtimeSide:
                    self.messageContent['actionPrompt'] = 'You must specify what side you start overtime on. Use **!lost attack** or **!lost defense**.'
                    await bot._sendMessage(ctx)
                    return
            if self.match.resolveRound('lost', overtimeSide):
                await self._playRound(ctx)
            else:
                await self._endMatch(ctx)

        @self.command(name='another')
        async def _another(ctx):
            playerIdStrings = [f'<@{player.id}>' for player in self.match.players]
            self.match = None
            self.matchMessage = None
            await _startMatch(ctx, *playerIdStrings)

        @self.command(name='goodnight')
        async def _goodnight(ctx):
            await ctx.message.delete()
            match, discordMessage, canContinue = await self._getMatchData(ctx)
            if not canContinue:
                return

            discordMessage['messageContent']['playersBanner'] = f"Finished a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
            discordMessage['messageContent']['roundMetadata'] = ''
            discordMessage['messageContent']['roundLineup'] = ''
            discordMessage['messageContent']['matchMetadata'] = 'Ending the session here... '
            if match.scores["blue"] > match.scores["red"]:
                discordMessage['messageContent']['matchMetadata'] += 'better to end on a high note!'
            else:
                discordMessage['messageContent']['matchMetadata'] += 'it\'s not going anywhere, let\'s call it a night.'
            discordMessage['messageContent']['actionPrompt'] = 'Use **!startMatch** to start a new match.'
            await bot._sendMessage(ctx, discordMessage)

            self.cursor.execute("DELETE FROM matches WHERE server_id = ?", (str(ctx.guild.id),))
            self.conn.commit()

    async def _banUnban(self, ctx, *args, ban=True):
        await ctx.message.delete()
        if self.match == None:
            self.messageContent['playersBanner'] = 'No match in progress. Use "**!startMatch**" to start a new match.'
            await bot._sendMessage(ctx, True)
            return

        bans = ' '.join(args)
        sanitizedBans = self.match.banOperators(bans, ban)

        if self.match.bannedOperators == []:
            self.messageContent['matchMetadata'] = 'No operators are banned in this match.\n'
        else:
            self.messageContent['matchMetadata'] = f'The following operators are banned in this match:\n{", ".join([f"**{op}**" for op in self.match.bannedOperators])}\n'
            unrecognizedBans = [ban for ban in zip(sanitizedBans, args) if ban[0] is None]
            if len(unrecognizedBans) > 0:
                if ban:
                    self.messageContent['matchMetadata'] += f'The following operators were not recognized:\n{", ".join([f"**{ban[1]}**" for ban in unrecognizedBans])}\n'
                else:
                    self.messageContent['matchMetadata'] += f'The following operators were not recognized, or not banned:\n{", ".join([f"**{ban[1]}**" for ban in unrecognizedBans])}\n'

        if self.match.currRound == 0:
            self.messageContent['actionPrompt'] = ''
            if not self.match.map:
                self.messageContent['actionPrompt'] += 'Next, use "**!setMap map**" to set the map.\n'
            self.messageContent['actionPrompt'] += 'You can also "**!ban**" or "**!unban**" more operators.\n'
            self.messageContent['actionPrompt'] += 'Use "**!startAttack**" or "**!startDefense**" to start the match.'
        else:
            self.messageContent['actionPrompt'] = 'Use "**!won**" or "**!lost**" to continue.'
        await bot._sendMessage(ctx)

    async def _playMatch(self, ctx, side):
        if self.match == None:
            self.messageContent['playersBanner'] = 'No match in progress. Use "**!startMatch**" to start a new match.'
            await bot._sendMessage(ctx, True)
            return
        
        self.messageContent['playersBanner'] = f"Playing a match with {self.match.playersString}{' on **' + self.match.map + '**' if self.match.map else ''}.\n"
        self.messageContent['matchMetadata'] = ''
        
        if side == 'attack':
            self.match.playingOnSide = 'attack'
        else:
            self.match.playingOnSide = 'defense'

        if self.match.currRound == 0:
                self.match.currRound = 1

        await self._playRound(ctx)

    async def _playRound(self, ctx):
        self.messageContent['playersBanner'] = f"Playing a match with {self.match.playersString}{' on **' + self.match.map + '**' if self.match.map else ''}.\n"
        self.messageContent['matchScore'] = f'The score is **{self.match.scores["blue"]}**:**{self.match.scores["red"]}**, we are playing on **{self.match.playingOnSide}**.\n'
        self.messageContent['roundMetadata'] = f'Here is your lineup for round {self.match.currRound}:'

        operators = self.match.getPlayedOperators(self.match.playingOnSide)
        if self.match.playingOnSide == 'defense':
            site = self.match.getPlayedSite()
            self.messageContent['roundMetadata'] += f'\nChoose the **{site}** site.'

        self.messageContent['roundLineup'] = ''
        operators_copy = operators.copy()
        for player, operator in zip(self.match.players, operators_copy):
            self.messageContent['roundLineup'] += f'{player.mention} plays **{operator}**\n'
            operators.remove(operator)
        
        if(operators):
            self.messageContent['roundLineup'] += f'Backup operators: **{", ".join(operators)}**\n'

        if self.match.currRound != 6:
            self.messageContent['actionPrompt'] = 'Use "**!won**" or "**!lost**" to continue.'
        elif self.match.scores["red"] == 3:
            self.messageContent['actionPrompt'] = 'If you won, use "**!won attack**" (or "**!won defense**") to start overtime on the specified side, otherwise use **!lost** to end the match.'
        elif self.match.scores["blue"] == 3:
            self.messageContent['actionPrompt'] = 'If you lost, use "**!lost attack**" (or "**!lost defense**") to start overtime on the specified side, otherwise use **!won** to end the match.'

        await bot._sendMessage(ctx)

    async def _endMatch(self, ctx):
        self.messageContent['roundMetadata'] = ''
        self.messageContent['roundLineup'] = ''
        self.messageContent['playersBanner'] = f"Finished a match with {self.match.playersString}{' on **' + self.match.map + '**' if self.match.map else ''}.\n"
        self.messageContent['matchScore'] = f'The match is over! The final score was **{self.match.scores["blue"]}**:**{self.match.scores["red"]}**.'
        self.messageContent['actionPrompt'] = 'Use "**!another**" to start a new match with the same players or "**!goodnight**" to end the session.'
        await bot._sendMessage(ctx)

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
                'matchMetadata': '',
                'roundMetadata': '',
                'roundLineup': '',
                'actionPrompt': ''
            }
        }

    async def _sendMessage(self, ctx, discordMessage, forgetMessage=False):
        serverId = str(ctx.guild.id)
        message = '\n'.join([v for v in discordMessage['messageContent'].values() if v != ''])

        if discordMessage['matchMessageId']:
            match_message = await ctx.channel.fetch_message(discordMessage['matchMessageId'])
            await match_message.edit(content=message)
        else:
            discordMessage['matchMessageId'] = (await ctx.send(message)).id
        if forgetMessage:
            self._resetDiscordMessage(ctx)
            return

        discordMessage = json.dumps(discordMessage)
        self.cursor.execute("UPDATE matches SET discord_message = ? WHERE server_id = ?", (discordMessage, serverId))
        self.conn.commit()
    
    def _saveMatch(self, ctx, match):
        serverId = str(ctx.guild.id)
        matchData = json.dumps(match.__dict__)
        self.cursor.execute("UPDATE matches SET match_data = ? WHERE server_id = ?", (matchData, serverId))
        self.conn.commit()

    async def _getMatchData(self, ctx):
        serverId = str(ctx.guild.id)
        result = self.cursor.execute("SELECT match_data, discord_message FROM matches WHERE server_id = ?", (serverId,)).fetchone()

        if result is not None:
            matchData, discordMessage = result
            matchData = json.loads(matchData) if matchData is not None else None
            discordMessage = json.loads(discordMessage) if discordMessage is not None else self._resetDiscordMessage(ctx)

        if matchData is None:
            discordMessage['messageContent']['playersBanner'] = 'No match in progress. Use "**!startMatch**" to start a new match.'
            await bot._sendMessage(ctx, discordMessage, True)
            return None, None, False

        match = RainbowMatch(matchData)
        return match, discordMessage, True

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    bot = RainbowBot()
    bot.run(TOKEN)
