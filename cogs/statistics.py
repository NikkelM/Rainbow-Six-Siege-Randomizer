import discord
from discord.ext import commands
from bot import RainbowBot
from rainbow import RainbowData

class Statistics(commands.Cog, name='Statistics'):
    """Commands to view statistics for players and past matches."""
    def __init__(self, bot: RainbowBot):
        self.bot = bot

    @commands.command(aliases=['stats', 'statistics'])
    async def _stats(self, ctx: commands.Context, statisticType: str = None, player: discord.User = None):
        """View a specific statistic for yourself or another user. Use **!stats help** for more information."""
        # No arguments given
        if statisticType is None:
            statisticType = 'overall'
            player = ctx.author
        # Only a player mention is given
        elif statisticType.startswith('<@') and statisticType.endswith('>'):
            player = ctx.message.mentions[0]
            statisticType = 'overall'
        # Only a statisticType is given
        elif player is None:
            player = ctx.author

        if player not in ctx.guild.members:
            return await ctx.send(f'{player.mention} is not a member of this server, so their statistics cannot be viewed.')
        
        target = player.mention
        if statisticType == 'server':
            target = ctx.guild.name

        message = f'Here are the requested statistics for **{target}**:\n\n'
        # Returns the player's Win/Loss ratio and additional statistics
        if statisticType == 'overall' or statisticType == 'server':
            if statisticType == 'overall':
                maps = self._getPlayerStatisticFromDatabase(player, 'maps')
                additionalStatistics = self._getPlayerStatisticFromDatabase(player, 'additionalStatistics')
                operators = self._getPlayerStatisticFromDatabase(player, 'operators')
            else:
                maps = self._getServerStatisticFromDatabase(ctx.guild, 'maps')
                additionalStatistics = []
                operators = self._getServerStatisticFromDatabase(ctx.guild, 'operators')

            # Maps/Sites
            message += self._createMapStatisticsString(ctx, statisticType, maps, player)

            # Operators
            message += self._createOperatorStatisticsString(operators)

            # Additional statistics
            if len(additionalStatistics) > 0:
                message += '\nSome additional statistics:\n'
                for stat in additionalStatistics:
                    message += f'**{stat[0].title()}**: {stat[1]}\n'
        elif statisticType == 'help':
            message = 'The **!stats** command allows you to query and view statistics for yourself, your server, or another user on this server.\n\n'
            message += 'Available *statisticTypes* are:\n'
            message += '**overall**: General statistics for a player, such as win/loss ratios for maps and operators.\n'
            message += '**server**: The same as the **overall** statistic, but for matches played on the current server.\n'
            message += 'If no *statisticType* is given, the **overall** statistics for the mentioned player are displayed.\n'
            message += 'If no player is mentioned, the message author\'s statistics are displayed.'
        else:
            message = f'The statistic you wanted to view is unknown: {statisticType}'

        await ctx.send(message)

    def _getPlayerStatisticFromDatabase(self, player: discord.User, statType: str, additionalArguments: list = None):
        """Gets all data related to the given player and statistic from the database."""
        # Returns a list of maps and match results for matches this player played
        if statType == 'maps':
            return self.bot.cursor.execute("""
                SELECT matches.map, matches.result
                FROM matches
                JOIN player_matches ON matches.match_id = player_matches.match_id
                WHERE player_matches.player_id = ?
            """, (player.id,)).fetchall()
        # Returns a list of all additional statistics for this player, such as interrogations or aces
        elif statType == 'additionalStatistics':
            return self.bot.cursor.execute("""
                SELECT stat_type, value
                FROM player_additional_stats
                WHERE player_id = ?
            """, (player.id,)).fetchall()
        # Gets a list of operators played by this player, and if the player won the round
        elif statType == 'operators':
            return self.bot.cursor.execute("""
                SELECT player_rounds.operator, rounds.result
                FROM player_rounds
                JOIN rounds ON player_rounds.match_id = rounds.match_id AND player_rounds.round_num = rounds.round_num
                WHERE player_rounds.player_id = ?
            """, (player.id,)).fetchall()
        # Gets a list of played sites for a given map, and if the player won the round
        elif statType == 'sites':
            map = additionalArguments[0]
            return self.bot.cursor.execute("""
                SELECT rounds.site, rounds.result
                FROM rounds
                JOIN matches ON rounds.match_id = matches.match_id
                JOIN player_rounds ON rounds.match_id = player_rounds.match_id AND rounds.round_num = player_rounds.round_num
                WHERE matches.map = ? AND player_rounds.player_id = ?
            """, (map, player.id)).fetchall()
        else:
            return None
    
    def _getServerStatisticFromDatabase(self, server: discord.Guild, statType: str, additionalArguments: list = None):
        """Gets all data related to the given server and statistic from the database."""
        # Returns a list of maps and match results for matches played on this server
        if statType == 'maps':
            return self.bot.cursor.execute("""
                SELECT matches.map, matches.result
                FROM matches
                WHERE matches.server_id = ?
            """, (server.id,)).fetchall()
        # Gets a list of operators played in matches on this server, and if the player won the round
        elif statType == 'operators':
            return self.bot.cursor.execute("""
                SELECT player_rounds.operator, rounds.result
                FROM player_rounds
                JOIN rounds ON player_rounds.match_id = rounds.match_id AND player_rounds.round_num = rounds.round_num
                JOIN matches ON player_rounds.match_id = matches.match_id
                WHERE matches.server_id = ?
            """, (server.id,)).fetchall()
        # Gets a list of played sites for a given map, and if the players won the round
        elif statType == 'sites':
            map = additionalArguments[0]
            return self.bot.cursor.execute("""
                SELECT rounds.site, rounds.result
                FROM rounds
                JOIN matches ON rounds.match_id = matches.match_id
                WHERE matches.map = ? AND matches.server_id = ?
            """, (map, server.id)).fetchall()
        else:
            return None

    def _calculateWinLossRatio(self, maps: list):
        res = {}
        overallWins = 0
        overallLosses = 0
        for map in maps:
            if map[0] not in res:
                res[map[0]] = {'wins': 0, 'losses': 0}
            if map[1] == 1:
                overallWins += 1
                res[map[0]]['wins'] += 1
            else:
                overallLosses += 1
                res[map[0]]['losses'] += 1
        # None means no map is set, or the round was played on attack
        none = res.pop(None, None)
        overall = {'wins': overallWins, 'losses': overallLosses}
        return res, overall, none
    
    def _getOperatorFromId(self, operatorId: int):
        if operatorId > 0:
            return RainbowData.attackers[operatorId - 1]
        return RainbowData.defenders[abs(operatorId) - 1]

    def _createMapStatisticsString(self, ctx: commands.Context, statisticType: str, maps: list, player: discord.User):
        mapsWinLoss, overallWinLoss, _ = self._calculateWinLossRatio(maps)
        message = f'Matches played: **{len(maps)}**, with **{overallWinLoss["wins"]}** wins and **{overallWinLoss["losses"]}** losses.\n'
        message += f'Overall Win/Loss Ratio: **{round(overallWinLoss["wins"]/overallWinLoss["losses"], 2) if overallWinLoss["losses"] != 0 else float(overallWinLoss["wins"])}**\n\n'
        sortedMaps = sorted(mapsWinLoss, key=lambda x: mapsWinLoss[x]['wins']/mapsWinLoss[x]['losses']if mapsWinLoss[x]["losses"] != 0 else mapsWinLoss[x]['wins'], reverse=True)[:3]
        if len(sortedMaps) > 0:
            # Get the win/loss of each defensive site for the top maps
            message += 'Top maps:\n'
            for map in sortedMaps:
                numMapPlays = len([m for m in maps if m[0] == map])
                if statisticType == 'overall':
                    sites = self._getPlayerStatisticFromDatabase(player, 'sites', [map])
                elif statisticType == 'server':
                    sites = self._getServerStatisticFromDatabase(ctx.guild, 'sites', [map])
                siteWinsLosses, siteOverallWinLoss, attackWinLoss = self._calculateWinLossRatio(sites)
                sortedSites = sorted(siteWinsLosses, key=lambda x: siteWinsLosses[x]['wins']/siteWinsLosses[x]['losses'] if siteWinsLosses[x]["losses"] != 0 else siteWinsLosses[x]['wins'], reverse=True)

                message += f'**{map}: {round(mapsWinLoss[map]["wins"]/mapsWinLoss[map]["losses"], 2) if mapsWinLoss[map]["losses"] != 0 else float(mapsWinLoss[map]["wins"])}** (**{numMapPlays}** plays)\n'

                if attackWinLoss is not None:
                    message += f'\tAttack:    **{round(attackWinLoss["wins"]/attackWinLoss["losses"], 2) if attackWinLoss["losses"] != 0 else float(attackWinLoss["wins"])}**\n'
                # defenseWinLoss is the overall win/loss minus the attack win/loss
                defenseWinLoss = {'wins': siteOverallWinLoss['wins'] - attackWinLoss['wins'], 'losses': siteOverallWinLoss['losses'] - attackWinLoss['losses']}
                message += f'\tDefense: **{round(defenseWinLoss["wins"]/defenseWinLoss["losses"], 2) if defenseWinLoss["losses"] != 0 else float(defenseWinLoss["wins"])}**\n'
                for site in sortedSites:
                    siteName = RainbowData.maps[map][site]
                    message += f'\t\t{siteName}: **{round(siteWinsLosses[site]["wins"]/siteWinsLosses[site]["losses"], 2) if siteWinsLosses[site]["losses"] != 0 else float(siteWinsLosses[site]["wins"])}**\n'
                message += '\n'

        return message

    def _createOperatorStatisticsString(self, operators: list):
        message = ''
        if len(operators) == 0:
            return message

        operatorWinsLosses = {}
        for operator in operators:
            if operator[0] not in operatorWinsLosses:
                operatorWinsLosses[operator[0]] = {'wins': 0, 'losses': 0}
            if operator[1] == 1:
                operatorWinsLosses[operator[0]]['wins'] += 1
            else:
                operatorWinsLosses[operator[0]]['losses'] += 1

        attackers = {k: operatorWinsLosses[k] for k in operatorWinsLosses if k > 0}
        defenders = {k: operatorWinsLosses[k] for k in operatorWinsLosses if k < 0}
        sorted_attackers = sorted(attackers, key=lambda x: attackers[x]['wins']/attackers[x]['losses'] if attackers[x]["losses"] != 0 else attackers[x]['wins'], reverse=True)[:3]
        sorted_defenders = sorted(defenders, key=lambda x: defenders[x]['wins']/defenders[x]['losses'] if defenders[x]["losses"] != 0 else defenders[x]['wins'], reverse=True)[:3]

        # Add the top three attackers to the message
        message += 'Top Attackers:\n'
        for operator in sorted_attackers:
            numOperatorPlays = len([o for o in operators if o[0] == operator])
            message += f'**{self._getOperatorFromId(operator)}: {round(attackers[operator]["wins"]/attackers[operator]["losses"], 2) if attackers[operator]["losses"] != 0 else float(attackers[operator]["wins"])}** (**{numOperatorPlays}** plays)\n'

        # Add the top three defenders to the message
        message += '\nTop Defenders:\n'
        for operator in sorted_defenders:
            numOperatorPlays = len([o for o in operators if o[0] == operator])
            message += f'**{self._getOperatorFromId(operator)}: {round(defenders[operator]["wins"]/defenders[operator]["losses"], 2) if defenders[operator]["losses"] != 0 else float(defenders[operator]["wins"])}** (**{numOperatorPlays}** plays)\n'

        return message

async def setup(bot: RainbowBot):
    await bot.add_cog(Statistics(bot))