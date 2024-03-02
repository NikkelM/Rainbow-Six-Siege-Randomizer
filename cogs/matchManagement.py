from discord.ext import commands
import json
import re
from rainbow import RainbowMatch
from bot import RainbowBot

class MatchManagement(commands.Cog, name='Match Management'):
    """Commands related to setting up matches and managing players."""
    def __init__(self, bot):
        self.bot: RainbowBot = bot

    @commands.command(aliases=['startMatch', 'start', 'play'], category='Rainbow Six')
    async def _startMatch(self, ctx: commands.Context, *playerNamesOrHereCommand):
        """Starts a new match with up to five players. Use **!startMatch here** to start a match with everyone in your current voice channel, or **!startMatch @player1 @player2...** to start a match with the mentioned players. This command must be used before in order for any other match commands to work."""
        serverId = ctx.guild.id
        matchData = self.bot.cursor.execute("SELECT match_data FROM ongoing_matches WHERE server_id = ?", (serverId,)).fetchone()

        if matchData is not None and matchData[0] is not None:
            await ctx.message.delete()
            discordMessage = self.bot.cursor.execute("SELECT discord_message FROM ongoing_matches WHERE server_id = ?", (serverId,)).fetchone()[0]
            discordMessage = json.loads(discordMessage)
            discordMessage['messageContent']['actionPrompt'] = 'A match is already in progress. Use "**!another**" to start a new match with the same players, "**!another here**" to start a match with everyone in your voice channel, or "**!goodnight**" to end the session.'
            await self.bot.sendMessage(ctx, discordMessage)
            return

        match = RainbowMatch()
        discordMessage = self.bot.resetDiscordMessage(ctx.guild.id)
        self.bot.cursor.execute("INSERT INTO ongoing_matches (server_id, discord_message) VALUES (?, ?)", (serverId, json.dumps(discordMessage)))

        # Instead of a player name, the user can use the argument "here" to start a match with the players in their voice channel
        if len(playerNamesOrHereCommand) == 1 and playerNamesOrHereCommand[0].lower() in ['voice', 'voicechannel', 'channel', 'here']:
            voiceChannel = ctx.author.voice.channel if ctx.author.voice else None
            if voiceChannel is None:
                discordMessage['messageContent']['playersBanner'] = 'You must be in a voice channel to use this command argument. You can always start a match using "**!startMatch @player1 @player2...**".'
                await self.bot.sendMessage(ctx, discordMessage)
                return
            playerObjects = voiceChannel.members
            if len(playerObjects) > 5:
                discordMessage['messageContent']['playersBanner'] = 'You can only start a match with up to **five** players! Make sure at most five players are in your voice channel, or use "**!startMatch @player1 @player2...**" to select participating players.'
                await self.bot.sendMessage(ctx, discordMessage)
                return
            match.setPlayers(playerObjects)
            discordMessage['messageContent']['playersBanner'] = f"Starting a new match with everyone in **{voiceChannel}**: {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"

        elif len(playerNamesOrHereCommand) > 5:
            discordMessage['messageContent']['playersBanner'] = 'You can only start a match with up to **five** players! Use "**!startMatch @player1 @player2...**" to try again.'
            await self.bot.sendMessage(ctx, discordMessage)
            return
        elif len(playerNamesOrHereCommand) > 0:
            playerObjects = self._validatePlayerNames(ctx, playerNamesOrHereCommand)
            if len(playerObjects) > 0:
                match.setPlayers(playerObjects)
                discordMessage['messageContent']['playersBanner'] = f"Starting a new match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
            else:
                discordMessage['messageContent']['playersBanner'] = 'None of the players were mentioned correctly using the **@player** syntax, or none of the mentioned players are on this server. Use "**!startMatch @player1 @player2...**" to try again.'
                await self.bot.sendMessage(ctx, discordMessage)
                return
        else:
            discordMessage['messageContent']['playersBanner'] = 'You can start a match using "**!startMatch @player1 @player2...**".'
            await self.bot.sendMessage(ctx, discordMessage, True)
            return

        discordMessage['messageContent']['banMetadata'] = f'Ban the **{match.getMapBan()}** map in rotation, and these operators:\n'
        attBans, defBans = match.getOperatorBanChoices()
        att1, att2 = attBans
        def1, def2 = defBans
        discordMessage['messageContent']['banMetadata'] += f'Attack:    **{att1}** or if banned **{att2}**\n'
        discordMessage['messageContent']['banMetadata'] += f'Defense: **{def1}** or if banned **{def2}**\n'

        discordMessage['messageContent']['actionPrompt'] = 'Next, use "**!setMap map**" and "**!ban op1 op2...**", or start the match with **!attack** ⚔️ or **!defense** 🛡️.'
        discordMessage['reactions'] = ['⚔️', '🛡️']

        self.bot.saveOngoingMatch(ctx, match)
        await self.bot.sendMessage(ctx, discordMessage)

    @commands.command(aliases=['addPlayers', 'addPlayer', 'add'])
    async def _addPlayers(self, ctx: commands.Context, *playerNames):
        """Adds additional players to the match. Use **!addPlayers @player1 @player2...** to add the mentioned players to the match. The total number of players cannot exceed five, use **!removePlayers** first if you need to."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if len(playerNames) + len(match.players) > 5:
            discordMessage['messageContent']['playersBanner'] = f"A match can only have up to **five** players! **!removePlayers** first if you need to. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            await self.bot.sendMessage(ctx, discordMessage)
            return
        elif len(playerNames) > 0:
            playerObjects = self._validatePlayerNames(ctx, playerNames)
            if playerObjects is not None:
                match.setPlayers(playerObjects + match.players)
                discordMessage['messageContent']['playersBanner'] = f"Player{'s' if len(playerNames) > 1 else ''} added! Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            else:
                discordMessage['messageContent']['playersBanner'] = f"At least one of the players you mentioned is not on this server. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
                await self.bot.sendMessage(ctx, discordMessage)
                return
        else:
            discordMessage['messageContent']['playersBanner'] = f"No new player passed with the command. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            await self.bot.sendMessage(ctx, discordMessage)
            return

        self.bot.saveOngoingMatch(ctx, match)
        await self.bot.sendMessage(ctx, discordMessage)

    @commands.command(aliases=['removePlayers', 'removePlayer', 'remove'])
    async def _removePlayers(self, ctx: commands.Context, *playerNames):
        """Removes players from the match. Use **!removePlayers @player1 @player2...** to remove the mentioned players from the match. At least one player must remain in the match."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if len(playerNames) > 0:
            playerObjects = self._validatePlayerNames(ctx, playerNames)
            if playerObjects is not None:
                removalSuccessful = match.removePlayers(playerObjects)
                if not removalSuccessful:
                    discordMessage['messageContent']['playersBanner'] = f"You cannot remove all players from the match! Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
                    await self.bot.sendMessage(ctx, discordMessage)
                    return
                discordMessage['messageContent']['playersBanner'] = f"Player{'s' if len(playerNames) > 1 else ''} removed! Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            else:
                discordMessage['messageContent']['playersBanner'] = f"At least one of the players you mentioned is not on this server. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
                await self.bot.sendMessage(ctx, discordMessage)
                return
        else:
            discordMessage['messageContent']['playersBanner'] = f"No player removed. Current players are {match.playersString}{', playing on **' + match.map + '**' if match.map else ''}.\n"
            await self.bot.sendMessage(ctx, discordMessage)
            return

        self.bot.saveOngoingMatch(ctx, match)
        await self.bot.sendMessage(ctx, discordMessage)

    @commands.command(aliases=['another', 'again'])
    async def _another(self, ctx: commands.Context, here: str = None):
        """Starts a new match with the same players as the previous one, or with everyone in the current voice channel if the **here** argument was provided."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return

        if not match.isMatchFinished():
            discordMessage['messageContent']['playersBanner'] = f"Stopped a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''} before completing it.\n"
            discordMessage['messageContent']['matchScore'] = f"The score was **{match.scores['blue']}**:**{match.scores['red']}**.\n"
        else:
            discordMessage['messageContent']['matchScore'] = f"The final score was **{match.scores['blue']}**:**{match.scores['red']}**.\n"
        discordMessage['messageContent']['roundMetadata'] = ''
        discordMessage['messageContent']['roundLineup'] = ''
        discordMessage['messageContent']['banMetadata'] = ''
        discordMessage['messageContent']['statsBanner'] = ''
        discordMessage['messageContent']['actionPrompt'] = ''
        discordMessage['reactions'] = []
        await self.bot.sendMessage(ctx, discordMessage, True)

        self.bot.cursor.execute("DELETE FROM ongoing_matches WHERE server_id = ?", (ctx.guild.id,))
        self.bot.conn.commit()

        playerIdStrings = [f'<@{player["id"]}>' for player in match.players]
        if here is not None and here.lower() in ['voice', 'voicechannel', 'channel', 'here']:
            playerIdStrings = ['here']

        await self._startMatch(ctx, *playerIdStrings)

    @commands.command(aliases=['goodnight', 'bye'])
    async def _goodnight(self, ctx: commands.Context):
        """Ends the current match and/or session."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if not match.isMatchFinished():
            discordMessage['messageContent']['playersBanner'] = f"Stopped a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''} before completing it.\n"
            discordMessage['messageContent']['matchScore'] = f"The score was **{match.scores['blue']}**:**{match.scores['red']}**.\n"
        else:
            discordMessage['messageContent']['matchScore'] = f"The final score was **{match.scores['blue']}**:**{match.scores['red']}**.\n"
            discordMessage['messageContent']['playersBanner'] = f"Finished a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        discordMessage['messageContent']['roundMetadata'] = ''
        discordMessage['messageContent']['roundLineup'] = ''
        discordMessage['messageContent']['banMetadata'] = ''
        discordMessage['messageContent']['statsBanner'] = ''
        discordMessage['messageContent']['actionPrompt'] = 'Use **!startMatch** to start a new match.'
        discordMessage['reactions'] = []
        await self.bot.sendMessage(ctx, discordMessage)

        self.bot.cursor.execute("DELETE FROM ongoing_matches WHERE server_id = ?", (ctx.guild.id,))
        self.bot.conn.commit()

    def _validatePlayerNames(self, ctx: commands.Context, playerNames):
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

async def setup(bot: RainbowBot):
    await bot.add_cog(MatchManagement(bot))