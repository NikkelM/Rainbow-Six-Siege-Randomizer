from discord.ext import commands
from fuzzywuzzy import process
from bot import RainbowBot
from rainbow import RainbowData, RainbowMatch

class OngoingMatch(commands.Cog, name='Ongoing Match'):
    """Commands to interact with an ongoing match, such as banning operators or playing rounds."""
    def __init__(self, bot):
        self.bot: RainbowBot = bot

    @commands.command(name='ban')
    async def _ban(self, ctx: commands.Context, *operators):
        """Bans operators from the match. Use **!ban op1 op2...** to ban the mentioned operators from the match. You can ban as many operators as you like."""
        await self._banUnban(ctx, *operators, ban=True)

    @commands.command(name='unban')
    async def _unban(self, ctx: commands.Context, *operators):
        """Unbans operators from the match. Use **!unban op1 op2...** to unban the mentioned operators from the match."""
        await self._banUnban(ctx, *operators, ban=False)

    @commands.command(aliases=['setMap', 'map'])
    async def _setMap(self, ctx: commands.Context, *mapName):
        """Sets the map for the match. This will influence the sites displayed for defensive rounds. Use **!setMap map** to set the map. A map can be set at any point in the match. Matches without a map set will not be included in statistics."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if len(mapName) == 0:
            discordMessage['messageContent']['actionPrompt'] = 'You must specify a map. Use "**!setMap map**" to try again.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return

        discordMessage['messageContent']['actionPrompt'] = ''
        mapName = ' '.join(mapName)
        couldSetMap = match.setMap(mapName)
        if couldSetMap:
            discordMessage['messageContent']['playersBanner'] = f"Playing a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
            discordMessage['messageContent']['banMetadata'] = ''

            if match.currRound > 0 and match.playingOnSide == 'defense':
                site = match.getCurrentSiteName()
                discordMessage['messageContent']['roundMetadata'] = f'Here is your lineup for round {match.currRound}:'
                discordMessage['messageContent']['roundMetadata'] += f'\nChoose the **{site}** site.'
        else:
            discordMessage['messageContent']['actionPrompt'] += f'**{mapName}** is not a valid map. Use "**!setMap map**" to try again.\n'

        if match.currRound == 0:
            discordMessage['messageContent']['actionPrompt'] += 'Use "**!attack**" ⚔️ or "**!defense**" 🛡️ to start the match.'
        else:
            discordMessage['messageContent']['actionPrompt'] += 'Use "**!won**" 🇼 or "**!lost**" 🇱 to continue.'

        self.bot.saveOngoingMatch(ctx, match)
        await self.bot.sendMatchMessage(ctx, discordMessage)

    @commands.command(aliases=['attack', 'startAttack'])
    async def _startAttack(self, ctx: commands.Context):
        """Starts the match on attack."""
        await self._playMatch(ctx, 'attack')

    @commands.command(aliases=['defense', 'startDefense', 'defend'])
    async def _startDefense(self, ctx: commands.Context):
        """Starts the match on defense."""
        await self._playMatch(ctx, 'defense')

    @commands.command(aliases=['won', 'w'])
    async def _won(self, ctx: commands.Context, overtimeSide = None):
        """Marks the current round as won and starts a new round. If winning starts overtime, you must specify the side you start overtime on with **!won attack** ⚔️ or **!won defense** 🛡️."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if not match.playingOnSide:
            discordMessage['messageContent']['actionPrompt'] = 'You must specify what side you start on. Use "**!attack**" ⚔️ or "**!defense**" 🛡️.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return

        if (match.currRound == 6 and match.scores["red"] == 3):
            overtimeSide = overtimeSide.lower() if overtimeSide else None
            if not overtimeSide or overtimeSide not in ['attack', 'defense']:
                discordMessage['messageContent']['actionPrompt'] = 'You must specify what side you start overtime on. Use "**!won attack**" ⚔️ or "**!won defense**" 🛡️.'
                await self.bot.sendMatchMessage(ctx, discordMessage)
                return

        if match.resolveRound('won', overtimeSide):
            self.bot.saveOngoingMatch(ctx, match)
            self.bot.saveDiscordMessage(ctx, discordMessage)
            if match.isMatchInOvertime():
                await self._playRound(ctx)
            else:
                await self._banPhase(ctx)
        else:
            self.bot.saveOngoingMatch(ctx, match)
            self.bot.saveDiscordMessage(ctx, discordMessage)
            await self._endMatch(ctx)

    @commands.command(aliases=['lost', 'l'])
    async def _lost(self, ctx: commands.Context, overtimeSide = None):
        """Marks the current round as lost and starts a new round. If losing starts overtime, you must specify the side you start overtime on with **!lost attack** ⚔️ or **!lost defense** 🛡️."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if not match.playingOnSide:
            discordMessage['messageContent']['actionPrompt'] = 'You must specify what side you start on. Use ""**!attack**" ⚔️ or "**!defense**" 🛡️.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return

        if (match.currRound == 6 and match.scores["blue"] == 3):
            overtimeSide = overtimeSide.lower() if overtimeSide else None
            if not overtimeSide or overtimeSide not in ['attack', 'defense']:
                discordMessage['messageContent']['actionPrompt'] = 'You must specify what side you start overtime on. Use "**!lost attack**" ⚔️ or "**!lost defense**" 🛡️.'
                await self.bot.sendMatchMessage(ctx, discordMessage)
                return

        if match.resolveRound('lost', overtimeSide):
            self.bot.saveOngoingMatch(ctx, match)
            self.bot.saveDiscordMessage(ctx, discordMessage)
            if match.isMatchInOvertime():
                await self._playRound(ctx)
            else:
                await self._banPhase(ctx)
        else:
            self.bot.saveOngoingMatch(ctx, match)
            self.bot.saveDiscordMessage(ctx, discordMessage)
            await self._endMatch(ctx)

    @commands.command(aliases=['swap', 'switch'])
    async def _swap(self, ctx: commands.Context, operator = None, player = None):
        """Swaps the operator a player is playing for another. Use **!swap operator** to swap the operator you are playing, or **!swap operator @player** to swap the operator another player is playing."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if match.currRound == 0:
            discordMessage['messageContent']['actionPrompt'] = 'You can only swap operators during an ongoing round. Use "**!attack**" ⚔️ or "**!defense**" 🛡️ to start the match.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return
        
        validOperators = RainbowData.attackers if match.playingOnSide == 'attack' else RainbowData.defenders

        if operator is None:
            discordMessage['messageContent']['statsBanner'] = 'You must include the operator you are swapping to. Use "**!swap operator**" or "**!swap operator @player**" to try again.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return
        if player is None:
            player = ctx.author
        else:
            player = await commands.MemberConverter().convert(ctx, player)

        operator = operator.lower().capitalize()
        operatorMatch, score = process.extractOne(operator, validOperators)
        if score >= 75:
            operator = operatorMatch
        else:
            discordMessage['messageContent']['statsBanner'] = f'**{operator}** is not a valid operator. Use "**!swap operator**" or "**!swap operator @player**" to try again.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return

        playerOperators, backupOperators = match.swapOperator(player, operator)

        discordMessage = self._setRoundLineup(discordMessage, match, playerOperators, backupOperators)

        self.bot.saveOngoingMatch(ctx, match)
        await self.bot.sendMatchMessage(ctx, discordMessage)

    @commands.command(aliases=['swapSite', 'site'])
    async def _swapSite(self, ctx: commands.Context, siteNumber: str = None):
        """Changes the site the round is played on, if playing on defense. Only sites that have not been won yet can be switched to. Use **!site <siteNumber>** to change the site for the current round."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if match.currRound == 0:
            discordMessage['messageContent']['actionPrompt'] = 'You can only change the site during an ongoing round. Use "**!attack**" ⚔️ or "**!defense**" 🛡️ to start the match.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return

        if match.playingOnSide != 'defense':
            discordMessage['messageContent']['statsBanner'] = 'You can only change the site during a defensive round. Use "**!site <siteNumber>**" to try again.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return
        
        if siteNumber is None:
            discordMessage['messageContent']['statsBanner'] = 'You must specify the site you are playing. Use "**!site <siteNumber>**" to try again.'
            await self.bot.sendMatchMessage(ctx, discordMessage)
            return

        wordToNumber = {
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4
        }
        try:
            siteNumber = wordToNumber[siteNumber.lower()] if siteNumber.isalpha() else int(siteNumber)
        except KeyError:
            discordMessage['messageContent']['statsBanner'] = f'**{siteNumber}** is not a valid site number. Use "**!site <siteNumber>**" to try again.'
            siteNumber = None

        if 1 <= siteNumber <= 4:
            newSite = match.trySetSite(siteNumber)
            if newSite is not None:
                discordMessage['messageContent']['roundMetadata'] = f'Here is your lineup for round {match.currRound}:'
                discordMessage['messageContent']['roundMetadata'] += f'\nChoose the **{newSite}** site.'
                discordMessage['messageContent']['statsBanner'] = 'The site has been changed successfully.'
            else:
                discordMessage['messageContent']['statsBanner'] = f'You have already won on the **{siteNumber}** site, so you cannot play it again.'
        else:
            discordMessage['messageContent']['statsBanner'] = f'**{siteNumber}** is not a valid site number (1-4). Use "**!site <siteNumber>**" to try again.'

        self.bot.saveOngoingMatch(ctx, match)
        await self.bot.sendMatchMessage(ctx, discordMessage)

    async def _banUnban(self, ctx: commands.Context, *operators, ban: bool = True):
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        operators = [op.lower().capitalize() for op in operators]

        if operators == ['None']:
            # No bans to process, just continue
            self.bot.saveOngoingMatch(ctx, match)
            await self._playRound(ctx)
            return

        bans = ' '.join(operators)
        sanitizedBans = match.banOperators(bans, "defense" if match.playingOnSide == "defense" else "attack", ban)

        discordMessage['messageContent']['banMetadata'] = ''
        unrecognizedBans = [ban for ban in zip(sanitizedBans, operators) if ban[0] is None]
        if len(unrecognizedBans) > 0:
            discordMessage['messageContent']['banMetadata'] += f'You can\'t ban these operators for your current side:\n{", ".join([f"**{ban[1]}**" for ban in unrecognizedBans])} (**!ban None** to skip banning)\n'
        if len(sanitizedBans) > len(unrecognizedBans):
            # At least one valid operator ban was made, so we continue
            self.bot.saveOngoingMatch(ctx, match)
            await self._playRound(ctx)
        else:
            # Otherwise, just print the message and wait for a proper ban
            await self.bot.sendMatchMessage(ctx, discordMessage)

    async def _playMatch(self, ctx: commands.Context, side: str):
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()

        if match == None:
            discordMessage['messageContent']['playersBanner'] = 'No match in progress. Use "**!startMatch @player1 @player2...**" to start a new match.'
            await self.bot.sendMatchMessage(ctx, discordMessage, True)
            return
        
        discordMessage['messageContent']['playersBanner'] = f"Playing a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        
        if side == 'attack':
            match.playingOnSide = 'attack'
        else:
            match.playingOnSide = 'defense'

        if match.currRound == 0:
                match.currRound = 1

        self.bot.saveOngoingMatch(ctx, match)
        self.bot.saveDiscordMessage(ctx, discordMessage)
        await self._banPhase(ctx)

    async def _banPhase(self, ctx: commands.Context):
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        
        discordMessage['messageContent']['playersBanner'] = f"Playing a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        discordMessage['messageContent']['matchScore'] = f'The score is **{match.scores["blue"]}**:**{match.scores["red"]}**, we are playing on **{match.playingOnSide}**.\n'
        opBan = match.getNewOperatorBan()
        discordMessage['messageContent']['roundMetadata'] = f'Ban **{opBan}** from being played by your opponents.\n'
        discordMessage['messageContent']['roundMetadata'] += f"Then, use **!ban** to ban the operator your opponents banned. (**!ban None** to skip banning)\n"
        discordMessage['messageContent']['roundLineup'] = ''
        discordMessage['messageContent']['banMetadata'] = ''
        discordMessage['messageContent']['actionPrompt'] = ''
        discordMessage['reactions'] = []
        await self.bot.sendMatchMessage(ctx, discordMessage)

    async def _playRound(self, ctx: commands.Context):
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return

        bannedOperators = list(reversed(match.getBannedOperators("defense" if match.playingOnSide == "defense" else "attack")))
        discordMessage['messageContent']['playersBanner'] = f"Playing a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        discordMessage['messageContent']['matchScore'] = f'The score is **{match.scores["blue"]}**:**{match.scores["red"]}**, we are playing on **{match.playingOnSide}**.\n'
        discordMessage['messageContent']['banMetadata'] = ''
        if len(bannedOperators) > 0:
            discordMessage['messageContent']['banMetadata'] = f'Your opponents have banned the following operators:\n'
            discordMessage['messageContent']['banMetadata'] += f'**{", ".join(bannedOperators)}**\n'
        discordMessage['messageContent']['statsBanner'] = ''
        discordMessage['messageContent']['roundMetadata'] = f'Here is your lineup for round {match.currRound}:'

        operators, site = match.setupRound()
        if match.playingOnSide == 'defense':
            discordMessage['messageContent']['roundMetadata'] += f'\nChoose the **{site}** site.'

        discordMessage['messageContent']['actionPrompt'] = ''
        discordMessage['reactions'] = []

        if match.currRound != 6:
            discordMessage['messageContent']['actionPrompt'] += 'Use "**!won**" 🇼 or "**!lost**" 🇱 to continue.'
            discordMessage['reactions'] += ['🇼', '🇱']
        elif match.scores["red"] == 3:
            discordMessage['messageContent']['actionPrompt'] += 'If you won, use "**!won attack**" ⚔️ (or "**!won defense**" 🛡️) to start overtime on the specified side, otherwise use "**!lost**" 🇱 to end the match.'
            discordMessage['reactions'] += ['⚔️', '🛡️', '🇱']
        elif match.scores["blue"] == 3:
            discordMessage['messageContent']['actionPrompt'] += 'If you lost, use "**!lost attack**" ⚔️ (or "**!lost defense**" 🛡️) to start overtime on the specified side, otherwise use "**!won**" 🇼 to end the match.'
            discordMessage['reactions'] += ['🇼', '⚔️', '🛡️']

        discordMessage = self._setRoundLineup(discordMessage, match, operators)

        self.bot.saveOngoingMatch(ctx, match)
        await self.bot.sendMatchMessage(ctx, discordMessage)

    async def _endMatch(self, ctx: commands.Context):
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return

        discordMessage['messageContent']['roundMetadata'] = ''
        discordMessage['messageContent']['roundLineup'] = ''
        discordMessage['messageContent']['playersBanner'] = f"Finished a match with {match.playersString}{' on **' + match.map + '**' if match.map else ''}.\n"
        discordMessage['messageContent']['matchScore'] = f'The match is over! The final score was **{match.scores["blue"]}**:**{match.scores["red"]}**.\n'
        discordMessage['messageContent']['statsBanner'] = ''
        discordMessage['messageContent']['actionPrompt'] = 'Use "**!another**" 👍 for a new match with the same players, "**!another here**" 🎤 for a new match in your voice channel, or "**!goodbye [delete]**" 👎 (✋) to end the match (and exclude it from statistics).'
        discordMessage['reactions'] = ['👍', '🎤', '👎', '✋']
        self.bot.saveOngoingMatch(ctx, match)
        self.bot.saveCompletedMatch(ctx, match)
        await self.bot.createMatchRecapThread(ctx, match, discordMessage)
        await self.bot.sendMatchMessage(ctx, discordMessage)
    
    def _setRoundLineup(self, discordMessage: dict, match: RainbowMatch, operators: list, backupOperators: list = None):
        operatorsCopy = operators.copy()

        discordMessage['messageContent']['roundLineup'] = ''
        for player, operator in zip(match.players, operatorsCopy):
            discordMessage['messageContent']['roundLineup'] += f'{player["mention"]} plays **{operator}**\n'
            operators.remove(operator)

        if backupOperators is None:
            backupOperators = operators

        if len(backupOperators) > 0:
            discordMessage['messageContent']['roundLineup'] += f'Backup operators: **{", ".join(backupOperators)}**.\n'
        discordMessage['messageContent']['roundLineup'] += 'Use "**!swap**" to switch operator.\n'

        # If one of the operators is Caveira, add the interrogation emoji to the message
        if 'Caveira' in operatorsCopy and '🗡️' not in discordMessage['reactions']:
            discordMessage['reactions'] += ['🗡️']
        
        return discordMessage

async def setup(bot: RainbowBot):
    await bot.add_cog(OngoingMatch(bot))