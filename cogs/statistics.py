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
        """View a specific statistic for yourself or another user. Available *statisticTypes* are:
        **overall**: General statistics for a player, such as win/loss ratios for maps and operators.
        **server**: The same as the **overall** statistic, but for matches played on the current server.
        If no *statisticType* is given, the **overall** statistics for the mentioned player are displayed.
        If no player is mentioned, the message author's statistics are displayed.
        """
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

            # Win/Loss
            mapsWinLoss, overallWinLoss, _ = self._calculateWinLossRatio(maps)
            message += f'Matches played: **{len(maps)}**, with **{overallWinLoss["wins"]}** wins and **{overallWinLoss["losses"]}** losses.\n'
            message += f'**Overall Win/Loss Ratio:** {round(overallWinLoss["wins"]/overallWinLoss["losses"], 2) if overallWinLoss["losses"] != 0 else float(overallWinLoss["wins"])}\n\n'
            sortedMaps = sorted(mapsWinLoss, key=lambda x: mapsWinLoss[x]['wins']/mapsWinLoss[x]['losses']if mapsWinLoss[x]["losses"] != 0 else mapsWinLoss[x]['wins'], reverse=True)[0:3]
            if (len(sortedMaps) > 0):
                # Get the win/loss of each defensive site for the top maps
                message += 'Top maps by Win/Loss ratio:\n'
                for map in sortedMaps:
                    sites = self._getPlayerStatisticFromDatabase(player, 'sites', [map])
                    siteWinsLosses, _, attackWinLoss = self._calculateWinLossRatio(sites)
                    sortedSites = sorted(siteWinsLosses, key=lambda x: siteWinsLosses[x]['wins']/siteWinsLosses[x]['losses'] if siteWinsLosses[x]["losses"] != 0 else siteWinsLosses[x]['wins'], reverse=True)
                    message += f'**{map}: {round(mapsWinLoss[map]["wins"]/mapsWinLoss[map]["losses"], 2) if mapsWinLoss[map]["losses"] != 0 else float(mapsWinLoss[map]["wins"])}**\n'
                    if attackWinLoss is not None:
                        message += f'\tAttack: **{round(attackWinLoss["wins"]/attackWinLoss["losses"], 2) if attackWinLoss["losses"] != 0 else float(attackWinLoss["wins"])}**\n'
                    for site in sortedSites:
                        siteName = RainbowData.maps[map][site]
                        message += f'\t{siteName}: **{round(siteWinsLosses[site]["wins"]/siteWinsLosses[site]["losses"], 2) if siteWinsLosses[site]["losses"] != 0 else float(siteWinsLosses[site]["wins"])}**\n'
                    message += '\n'

            # Operators
            if (len(operators) > 0):
                message += 'Top operators by Win/Loss:\n'
                operatorWinsLosses = {}
                for operator in operators:
                    if operator[0] not in operatorWinsLosses:
                        operatorWinsLosses[operator[0]] = {'wins': 0, 'losses': 0}
                    if operator[1] == 1:
                        operatorWinsLosses[operator[0]]['wins'] += 1
                    else:
                        operatorWinsLosses[operator[0]]['losses'] += 1
                sortedOperators = sorted(operatorWinsLosses, key=lambda x: operatorWinsLosses[x]['wins']/operatorWinsLosses[x]['losses'] if operatorWinsLosses[x]["losses"] != 0 else operatorWinsLosses[x]['wins'], reverse=True)[0:5]
                for operator in sortedOperators:
                    message += f'**{self._getOperatorFromId(operator)}:** {round(operatorWinsLosses[operator]["wins"]/operatorWinsLosses[operator]["losses"], 2) if operatorWinsLosses[operator]["losses"] != 0 else float(operatorWinsLosses[operator]["wins"])}\n'

            # Additional statistics
            if len(additionalStatistics) > 0:
                message += '\nSome additional statistics:\n'
                for stat in additionalStatistics:
                    message += f'**{stat[0].title()}**: {stat[1]}\n'
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
        # Gets a list of played sites for a given map, and if the player won the round. The map is stored in the matches table, the site and result in the rounds table
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
        # Gets a list of operators played on this server, and if the player won the round
        elif statType == 'operators':
            return self.bot.cursor.execute("""
                SELECT player_rounds.operator, rounds.result
                FROM player_rounds
                JOIN rounds ON player_rounds.match_id = rounds.match_id AND player_rounds.round_num = rounds.round_num
                JOIN matches ON player_rounds.match_id = matches.match_id
                WHERE matches.server_id = ?
            """, (server.id,)).fetchall()
        # Gets a list of played sites for a given map, and if the player won the round. The map is stored in the matches table, the site and result in the rounds table
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

async def setup(bot: RainbowBot):
    await bot.add_cog(Statistics(bot))