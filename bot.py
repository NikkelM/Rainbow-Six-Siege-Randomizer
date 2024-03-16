import discord
from itertools import zip_longest
import json
import os
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv
from rainbow import RainbowMatch
from version import __version__ as VERSION

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
IS_DEBUG = os.getenv('IS_DEBUG') == '1'

if IS_DEBUG:
    print('DEBUG MODE: Running in debug mode')

print(f'Running RandomSixBot v{VERSION}')

class RainbowBot(commands.Bot):
    def __init__(self):
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect("data/rainbowDiscordBot.db")
        self.cursor = self.conn.cursor()

        # Currently ongoing matches, one per server
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ongoing_matches (
                server_id INTEGER PRIMARY KEY,
                match_data TEXT,
                discord_message TEXT
            )
        """)

        # Matches with their map and overall scores
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                server_id INTEGER,
                map TEXT,
                result INTEGER
            )
        """)

        # Players that have ever played in a match
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY
            )
        """)

        # Matches a certain player has played
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_matches (
                player_id INTEGER,
                match_id TEXT,
                PRIMARY KEY(player_id, match_id),
                FOREIGN KEY(player_id) REFERENCES players(player_id),
                FOREIGN KEY(match_id) REFERENCES matches(match_id)
            )
        """)

        # Played sites and outcome for each round, 1 is win, 0 is loss
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                match_id TEXT,
                round_num INTEGER,
                site INTEGER,
                result INTEGER,
                PRIMARY KEY(match_id, round_num),
                FOREIGN KEY(match_id) REFERENCES matches(match_id)
            )
        """)

        # Operators played by a player in each round
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_rounds (
                player_id INTEGER,
                match_id TEXT,
                round_num INTEGER,
                operator INTEGER,
                PRIMARY KEY(player_id, match_id, round_num),
                FOREIGN KEY(match_id) REFERENCES matches(match_id),
                FOREIGN KEY(player_id) REFERENCES players(player_id)
            )
        """)

        # Additional player statistics, such as Caveira interrogations, Aces etc.
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_additional_stats (
                player_id INTEGER,
                stat_type INTEGER,
                value INTEGER,
                PRIMARY KEY(player_id, stat_type),
                FOREIGN KEY(player_id) REFERENCES players(player_id)
            )
        """)

        if IS_DEBUG:
            print('DEBUG MODE: Deleting matches with no map set')
            # Get all match ids where map is null
            self.cursor.execute("SELECT match_id FROM matches WHERE map IS NULL")
            match_ids = [row[0] for row in self.cursor.fetchall()]

            # Delete data associated with these match ids in the other tables
            for match_id in match_ids:
                self.cursor.execute("DELETE FROM player_matches WHERE match_id = ?", (match_id,))
                self.cursor.execute("DELETE FROM rounds WHERE match_id = ?", (match_id,))
                self.cursor.execute("DELETE FROM player_rounds WHERE match_id = ?", (match_id,))

            # Delete matches where map is null
            self.cursor.execute("DELETE FROM matches WHERE map IS NULL")

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
            'trackingMatchStatistics',
            'statistics'
        ]
        for cog in cogs_list:
            await bot.load_extension(f'cogs.{cog}')

        if IS_DEBUG:
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='the development build'))
        else:
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='!startMatch here | !help'))

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handles reactions being added to messages."""
        ctx: commands.Context = await self.get_context(reaction.message)
        match, discordMessage, canContinue = await self.getMatchData(ctx, False)

        if discordMessage is None or discordMessage['matchMessageId'] != reaction.message.id or user == bot.user:
            return     
        if user.mention not in [player['mention'] for player in match.players] or reaction.emoji not in discordMessage['reactions'] or not canContinue:
            await reaction.message.remove_reaction(reaction, user)
            return

        await reaction.message.remove_reaction(reaction, user)

        # During a match
        if reaction.emoji == '🇼': # Round was won
            await self.get_cog('Ongoing Match')._won(ctx)
        elif reaction.emoji == '🇱': # Round was lost
            await self.get_cog('Ongoing Match')._lost(ctx)
        elif reaction.emoji == '⚔️': # Starting (overtime) on attack
            if match.currRound == 0:
                await self.get_cog('Ongoing Match')._startAttack(ctx)
            elif (match.currRound == 6 and match.scores["red"] == 3):
                await self.get_cog('Ongoing Match')._won(ctx, 'attack')
            elif (match.currRound == 6 and match.scores["blue"] == 3):
                await self.get_cog('Ongoing Match')._lost(ctx, 'attack')
            else:
                print('Unknown reaction/match state combination: ⚔️', match.currRound, match.scores)
        elif reaction.emoji == '🛡️': # Starting (overtime) on defense
            if match.currRound == 0:
                await self.get_cog('Ongoing Match')._startDefense(ctx)
            elif (match.currRound == 6 and match.scores["red"] == 3):
                await self.get_cog('Ongoing Match')._won(ctx, 'defense')
            elif (match.currRound == 6 and match.scores["blue"] == 3):
                await self.get_cog('Ongoing Match')._lost(ctx, 'defense')
            else:
                print('Unknown reaction/match state combination: 🛡️', match.currRound, match.scores)

        # End of match
        elif reaction.emoji == '👍': # Play another match with the same players
            await self.get_cog('Match Management')._another(ctx)
        elif reaction.emoji == '🎤': # Play another match with players in the current voice channel
            member = reaction.message.guild.get_member(user.id)
            ctx.author = member if member.voice else ctx.author
            await self.get_cog('Match Management')._another(ctx, 'here')
        elif reaction.emoji == '👎': # End the session
            await self.get_cog('Match Management')._goodnight(ctx)
        elif reaction.emoji == '✋': # End the session without saving statistics
            await self.get_cog('Match Management')._goodnight(ctx, 'delete')

        # Statistics
        elif reaction.emoji == '🗡️': # Player got an interrogation
            await self.get_cog('Tracking Match Statistics')._interrogation(ctx, user)
        else:
            print('Unknown reaction:', reaction.emoji)
            return

    def resetDiscordMessage(self, serverId: int):
        self.cursor.execute("DELETE FROM ongoing_matches WHERE server_id = ?", (serverId,))
        self.conn.commit()
        return {
            'matchMessageId': None,
            'messageContent': {
                'playersBanner': '',
                'matchScore': '',
                'banMetadata': '',
                'roundMetadata': '',
                'roundLineup': '',
                'statsBanner': '',
                'actionPrompt': ''
            },
            'reactions': []
        }

    async def sendMatchMessage(self, ctx: commands.Context, discordMessage, forgetMatch=False):
        message = '\n'.join([v for v in discordMessage['messageContent'].values() if v != ''])

        if discordMessage['matchMessageId']:
            matchMessage = await ctx.channel.fetch_message(discordMessage['matchMessageId'])
            await matchMessage.edit(content=message)
        else:
            matchMessage = (await ctx.send(message))
            discordMessage['matchMessageId'] = matchMessage.id

        if forgetMatch:
            await matchMessage.clear_reactions()
            self.resetDiscordMessage(ctx.guild.id)
            self.saveDiscordMessage(ctx, discordMessage)
        else:
            self.saveDiscordMessage(ctx, discordMessage)
            await self._manageReactions(matchMessage, discordMessage)
    
    async def _manageReactions(self, message: discord.Message, discordMessage):
        currentReactions = [r.emoji for r in message.reactions]

        if not any(reaction in discordMessage['reactions'] for reaction in currentReactions):
            await message.clear_reactions()
        else:
            # Remove extra reactions from right to left
            for reaction in reversed(currentReactions):
                if reaction not in discordMessage['reactions']:
                    await message.clear_reaction(reaction)

        # Make sure the reactions are in the correct order and remove user-added reaction counts
        for i, (current, expected) in enumerate(zip_longest(currentReactions, discordMessage['reactions'])):
            if current != expected:
                for reaction in currentReactions[i:]:
                    await message.clear_reaction(reaction)
                for reaction in discordMessage['reactions'][i:]:
                    await message.add_reaction(reaction)
                break
            elif next((r for r in message.reactions if r.emoji == current), None).count > 1:
                users = [user async for user in current.users()]
                for user in users[1:]:
                    await message.remove_reaction(current, user)
    
    def saveOngoingMatch(self, ctx: commands.Context, match):
        serverId = ctx.guild.id
        matchData = json.dumps(match.__dict__)
        self.cursor.execute("UPDATE ongoing_matches SET match_data = ? WHERE server_id = ?", (matchData, serverId))
        self.conn.commit()

    def saveCompletedMatch(self, ctx: commands.Context, match: RainbowMatch):
        matchMap = match.map
        # Proper matches will have a map name set, so we only save those to the database
        if not IS_DEBUG and matchMap is None:
            return
        matchId = match.matchId
        serverId = ctx.guild.id
        didWin = match.scores['blue'] > match.scores['red']

        self.cursor.execute("INSERT INTO matches (match_id, server_id, map, result) VALUES (?, ?, ?, ?)", (matchId, serverId, matchMap, didWin))
        self.conn.commit()

        for player in match.players:
            self.cursor.execute("INSERT OR IGNORE INTO players (player_id) VALUES (?)", (player['id'],))
            self.cursor.execute("INSERT INTO player_matches (player_id, match_id) VALUES (?, ?)", (player['id'], matchId))
            self.conn.commit()

        for roundNumber, round in enumerate(match.rounds):
            site = round['site']
            roundResult = round['result']
            self.cursor.execute("INSERT INTO rounds (round_num, match_id, site, result) VALUES (?, ?, ?, ?)", (roundNumber, matchId, site, roundResult))
            self.conn.commit()

            for playerIndex, player in enumerate(match.players):
                playerId = player['id']
                operator = round['operators'][playerIndex]
                self.cursor.execute("INSERT INTO player_rounds (player_id, match_id, round_num, operator) VALUES (?, ?, ?, ?)", (playerId, matchId, roundNumber, operator))
                self.conn.commit()

        for stat in match.playerStats:
            playerId = stat['playerId']
            statType = stat['statType']
            # Increase the counter of this stat by one, or create it if it doesn't exist.
            self.cursor.execute("""
                INSERT OR REPLACE INTO player_additional_stats (player_id, stat_type, value)
                VALUES (?, ?, COALESCE((SELECT value FROM player_additional_stats WHERE player_id = ? AND stat_type = ?), 0) + 1)
            """, (playerId, statType, playerId, statType))
            self.conn.commit()

    def removeMatchData(self, matchId):
        """Removes all data associated with a match from the database."""
        self.cursor.execute("DELETE FROM matches WHERE match_id = ?", (matchId,))
        self.cursor.execute("DELETE FROM player_matches WHERE match_id = ?", (matchId,))
        self.cursor.execute("DELETE FROM rounds WHERE match_id = ?", (matchId,))
        self.cursor.execute("DELETE FROM player_rounds WHERE match_id = ?", (matchId,))
        self.conn.commit()

    def saveDiscordMessage(self, ctx: commands.Context, discordMessage):
        serverId = ctx.guild.id
        discordMessage = json.dumps(discordMessage)
        self.cursor.execute("UPDATE ongoing_matches SET discord_message = ? WHERE server_id = ?", (discordMessage, serverId))
        self.conn.commit()

    async def getMatchData(self, ctx: commands.Context, shouldAlertOnNoMatch=True):
        """Gets the match data and discord message from the database. If there is no match in progress, it will send a message to the user."""
        serverId = ctx.guild.id
        matchData, discordMessage = None, None
        result = self.cursor.execute("SELECT match_data, discord_message FROM ongoing_matches WHERE server_id = ?", (serverId,)).fetchone()

        if result is not None:
            matchData, discordMessage = result
            matchData = json.loads(matchData) if matchData is not None else None
            discordMessage = json.loads(discordMessage) if discordMessage is not None else self.resetDiscordMessage(ctx.guild.id)
        else:
            discordMessage = self.resetDiscordMessage(ctx.guild.id)

        if matchData is None and shouldAlertOnNoMatch:
            discordMessage['messageContent']['playersBanner'] = 'No match in progress. Use "**!startMatch @player1 @player2...**" to start a new match.'
            await bot.sendMatchMessage(ctx, discordMessage, True)
            return None, None, False

        match = RainbowMatch(matchData)
        return match, discordMessage, True

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    bot = RainbowBot()
    bot.run(TOKEN)
