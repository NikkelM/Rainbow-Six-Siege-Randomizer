from discord.ext import commands
import json
from rainbow import RainbowMatch
from bot import RainbowBot

class MatchSetup(commands.Cog, name='Match Setup'):
    """This category contains commands relevant to setting up matches."""
    def __init__(self, bot):
        self.bot: RainbowBot = bot

    @commands.command(aliases=['startMatch', 'start', 'play'], category='Rainbow Six')
    async def _startMatch(self, ctx, *playerNames):
        """Starts a new match with up to five players. Use **!startMatch @player1 @player2...** to start a match with the mentioned players."""
        serverId = str(ctx.guild.id)
        matchData = self.bot.cursor.execute("SELECT match_data FROM matches WHERE server_id = ?", (serverId,)).fetchone()

        if matchData is not None and matchData[0] is not None:
            await ctx.message.delete()
            discordMessage = self.bot.cursor.execute("SELECT discord_message FROM matches WHERE server_id = ?", (serverId,)).fetchone()[0]
            discordMessage = json.loads(discordMessage)
            discordMessage['messageContent']['actionPrompt'] = 'A match is already in progress. Use **!another** to start a new match with the same players or **!goodnight** to end the session.'
            await self.bot._sendMessage(ctx, discordMessage)
            return

        match = RainbowMatch()
        discordMessage = self.bot._resetDiscordMessage(ctx)
        self.bot.cursor.execute("INSERT INTO matches (server_id, discord_message) VALUES (?, ?)", (serverId, json.dumps(discordMessage)))

        if len(playerNames) > 5:
            discordMessage['messageContent']['playersBanner'] = 'You can only start a match with up to **five** players! Use "**!startMatch @player1 @player2...**" to try again.'
            await self.bot._sendMessage(ctx, discordMessage)
            return
        elif len(playerNames) > 0:
            playerObjects = self.bot._validatePlayerNames(ctx, playerNames)
            if playerObjects is not None:
                match.setPlayers(playerObjects)
                discordMessage['messageContent']['playersBanner'] = f"Starting a new match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
            else:
                discordMessage['messageContent']['playersBanner'] = 'At least one of the players you mentioned is not on this server, please try again.'
                await self.bot._sendMessage(ctx, discordMessage)
                return
        else:
            discordMessage['messageContent']['playersBanner'] = 'You can start a match using "**!startMatch @player1 @player2...**".'
            await self.bot._sendMessage(ctx, discordMessage, True)
            return

        discordMessage['messageContent']['banMetadata'] = f'Ban the **{match.getMapBan()}** map in rotation, and these operators:\n'
        attBans, defBans = match.getOperatorBanChoices()
        att1, att2 = attBans
        def1, def2 = defBans
        discordMessage['messageContent']['banMetadata'] += f'Attack:    **{att1}** or if banned **{att2}**\n'
        discordMessage['messageContent']['banMetadata'] += f'Defense: **{def1}** or if banned **{def2}**\n'

        discordMessage['messageContent']['actionPrompt'] = 'Next, use "**!setMap map**" and "**!ban op1 op2...**"'

        self.bot._saveMatch(ctx, match)
        await self.bot._sendMessage(ctx, discordMessage)

    @commands.command(aliases=['addPlayers', 'addPlayer'])
    async def _addPlayers(self, ctx, *playerNames):
        """Adds additional players to the match. Use **!addPlayers @player1 @player2...** to add the mentioned players to the match. The total number of players cannot exceed five, use **!removePlayers** first if you need to."""
        match, discordMessage, canContinue = await self.bot._getMatchData(ctx)
        if not canContinue:
            return
        await ctx.message.delete()

        if len(playerNames) + len(match.players) > 5:
            discordMessage['messageContent']['playersBanner'] = f"A match can only have up to **five** players! **!removePlayers** first if you need to. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            await self.bot._sendMessage(ctx, discordMessage)
            return
        elif len(playerNames) > 0:
            playerObjects = self.bot._validatePlayerNames(ctx, playerNames)
            if playerObjects is not None:
                match.setPlayers(playerObjects + match.players)
                discordMessage['messageContent']['playersBanner'] = f"Player{'s' if len(playerNames) > 1 else ''} added! Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            else:
                discordMessage['messageContent']['playersBanner'] = f"At least one of the players you mentioned is not on this server. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
                await self.bot._sendMessage(ctx, discordMessage)
                return
        else:
            discordMessage['messageContent']['playersBanner'] = f"No new player passed with the command. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            await self.bot._sendMessage(ctx, discordMessage)
            return

        self.bot._saveMatch(ctx, match)
        await self.bot._sendMessage(ctx, discordMessage)

    @commands.command(aliases=['removePlayers', 'removePlayer'])
    async def _removePlayers(self, ctx, *playerNames):
        """Removes players from the match. Use **!removePlayers @player1 @player2...** to remove the mentioned players from the match. At least one player must remain in the match."""
        match, discordMessage, canContinue = await self.bot._getMatchData(ctx)
        if not canContinue:
            return
        await ctx.message.delete()

        if len(playerNames) > 0:
            playerObjects = self.bot._validatePlayerNames(ctx, playerNames)
            if playerObjects is not None:
                removalSuccessful = match.removePlayers(playerObjects)
                if not removalSuccessful:
                    discordMessage['messageContent']['playersBanner'] = f"You cannot remove all players from the match! Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
                    await self.bot._sendMessage(ctx, discordMessage)
                    return
                discordMessage['messageContent']['playersBanner'] = f"Player{'s' if len(playerNames) > 1 else ''} removed! Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            else:
                discordMessage['messageContent']['playersBanner'] = f"At least one of the players you mentioned is not on this server. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
                await self.bot._sendMessage(ctx, discordMessage)
                return
        else:
            discordMessage['messageContent']['playersBanner'] = f"No player removed. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            await self.bot._sendMessage(ctx, discordMessage)
            return

        self.bot._saveMatch(ctx, match)
        await self.bot._sendMessage(ctx, discordMessage)

    @commands.command(aliases=['another', 'again'])
    async def _another(self, ctx):
        """Starts a new match with the same players as the previous one."""
        match, discordMessage, canContinue = await self.bot._getMatchData(ctx)
        if not canContinue:
            return
            
        if not match.isMatchFinished():
            discordMessage['messageContent']['playersBanner'] = f"Stopped a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''} before completing it.\n"
            discordMessage['messageContent']['banMetadata'] = ''
            discordMessage['messageContent']['matchScore'] = f"The score was **{match.scores['blue']}**:**{match.scores['red']}**{', we were playing on **' + match.playingOnSide + '**' if match.playingOnSide else ''}.\n"
            discordMessage['messageContent']['roundMetadata'] = ''
            discordMessage['messageContent']['roundLineup'] = ''
        discordMessage['messageContent']['actionPrompt'] = ''
        await self.bot._sendMessage(ctx, discordMessage, True)
            
        self.bot.cursor.execute("DELETE FROM matches WHERE server_id = ?", (str(ctx.guild.id),))
        self.bot.conn.commit()
        
        playerIdStrings = [f'<@{player["id"]}>' for player in match.players]
        await self._startMatch(ctx, *playerIdStrings)

    @commands.command(aliases=['goodnight', 'bye'])
    async def _goodnight(self, ctx):
        """Ends the current match and/or session."""
        match, discordMessage, canContinue = await self.bot._getMatchData(ctx)
        if not canContinue:
            return
        await ctx.message.delete()

        if not match.isMatchFinished():
            discordMessage['messageContent']['playersBanner'] = f"Stopped a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''} before completing it.\n"
            discordMessage['messageContent']['matchScore'] = f"The score was **{match.scores['blue']}**:**{match.scores['red']}**{', we were playing on **' + match.playingOnSide + '**' if match.playingOnSide else ''}.\n"
        else:
            discordMessage['messageContent']['playersBanner'] = f"Finished a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        discordMessage['messageContent']['roundMetadata'] = ''
        discordMessage['messageContent']['roundLineup'] = ''
        discordMessage['messageContent']['banMetadata'] = ''
        discordMessage['messageContent']['actionPrompt'] = 'Ending the session here...\nUse **!startMatch** to start a new match.'
        await self.bot._sendMessage(ctx, discordMessage)

        self.bot.cursor.execute("DELETE FROM matches WHERE server_id = ?", (str(ctx.guild.id),))
        self.bot.conn.commit()

async def setup(bot: RainbowBot):
    await bot.add_cog(MatchSetup(bot))