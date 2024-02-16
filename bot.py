import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from rainbow import RainbowMatch

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')


class RainbowBot(commands.Bot):
    stateActivityMapping = {
        "idle": "for !startMatch",
        "matchInProgress": "you play Siege!",
        "overtime": "you clutch overtime!",
        "matchEnded": "for another round!"
    }

    def __init__(self):
        self.match = None

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        commands.Bot.__init__(self, command_prefix='!', intents=intents)
        self.setup_bot_commands()

    async def on_ready(self):
        print(f'We have logged in as {bot.user}')
        await self.setBotActivity('idle')

    def setup_bot_commands(self):
        @self.command(name='startMatch')
        async def _startMatch(ctx, *playerNames: discord.Member):
            message = ''
            self.match = RainbowMatch()

            if len(playerNames) > 0:
                if self.validatePlayerNames(ctx, playerNames):
                    self.match.setPlayerNames(playerNames)
                    message += f"Starting a new match with {', '.join([player.mention for player in playerNames])}.\n"
                else:
                    message += 'At least one of the players you mentioned is not on this server, please try again.'
                    await ctx.send(message)
                    return
            else:
                message += 'No players set. Use "**!startMatch @player1 @player2...**" to set players.'
                await ctx.send(message)
                return

            message += f'Ban the **{self.match.getMapBan()}** map in rotation, and these operators:\n'
            attBans, defBans = self.match.getOperatorBanChoices()
            att1, att2 = attBans
            def1, def2 = defBans
            message += f'Attack:  **{att1}** or if banned **{att2}**\n'
            message += f'Defense: **{def1}** or if banned **{def2}**\n'

            message += '\nNext, tell me the "**!bans firstOp secondOp...**":'

            await ctx.send(message)
            await bot.setBotActivity('matchInProgress')

        @_startMatch.error
        async def startMatch_error(ctx, error):
            if isinstance(error, commands.BadArgument):
                await bot.setBotActivity('idle')
                await ctx.send('All players must be mentioned directly using the @ syntax and be users on this server, please try again.')

        @self.command(name='bans')
        async def _bans(ctx, *args):
            if self.match == None:
                await ctx.send('No match in progress. Use "**!startMatch**" to start a new match.')
                return

            message = ''
            bans = ' '.join(args[0:4])
            sanitized_bans = self.match.banOperators(bans)

            if len(sanitized_bans) == 0:
                message += 'No operators are banned in this match.\n'
            else:
                bans = ', '.join(
                    f'**{ban}**' for ban in sanitized_bans if ban is not None)
                message = f'The following operators are banned in this match:\n{bans}\n'
                unrecognized_bans = [ban for ban in zip(
                    sanitized_bans, args) if ban[0] is None]
                if len(unrecognized_bans) > 0:
                    message += f'The following operators you passed were not recognized:\n{", ".join([f"**{ban[1]}**" for ban in unrecognized_bans])}\n'

            message += 'Use "**!addBans**" to add new bans.\n'
            message += 'Use "**!startAttack**" or "**!startDefense**" to start the match.'
            await ctx.send(message)

        @self.command(name='addBans')
        async def _bans(ctx, *args):
            if self.match == None:
                await ctx.send('No match in progress. Use "**!startMatch**" to start a new match.')
                return

            message = ''
            bans = ' '.join(args[0:4])
            sanitized_bans = self.match.banOperators(bans)

            if len(sanitized_bans) == 0:
                message += 'No operators were passed with the command.\n'
            else:
                bans = ', '.join(
                    f'**{ban}**' for ban in sanitized_bans if ban is not None)
                message = f'The following operators are now **also** banned in this match:\n{bans}\n'
                unrecognized_bans = [ban for ban in zip(
                    sanitized_bans, args) if ban[0] is None]
                if len(unrecognized_bans) > 0:
                    message += f'The following operators you passed were not recognized:\n{", ".join([f"**{ban[1]}**" for ban in unrecognized_bans])}\n'

            message += 'Use "**!startAttack**" or "**!startDefense**" to start the match.'
            await ctx.send(message)

        @self.command(name='startAttack')
        async def startAttack(ctx):
            await self.playMatch(ctx, 'attack')

        @self.command(name='startDefense')
        async def startDefense(ctx):
            await self.playMatch(ctx, 'defense')

        @self.command(name='won')
        async def startAttack(ctx, overtimeSide=None):
            if (self.match.currRound == 6 and self.match.scores["red"] == 3):
                await bot.setBotActivity('overtime')
                if not overtimeSide:
                    await ctx.send('You must specify what side you start overtime on. Use **!won attack** or **!won defense**.')
                    return
            if self.match.resolveRound('won', overtimeSide):
                await self.playRound(ctx)
            else:
                await bot.setBotActivity('matchEnded')
                await self.endMatch(ctx)

        @self.command(name='lost')
        async def startDefense(ctx, overtimeSide=None):
            if (self.match.currRound == 6 and self.match.scores["blue"] == 3):
                await bot.setBotActivity('overtime')
                if not overtimeSide:
                    await ctx.send('You must specify what side you start overtime on. Use **!lost attack** or **!lost defense**.')
                    return
            if self.match.resolveRound('lost', overtimeSide):
                await self.playRound(ctx)
            else:
                await bot.setBotActivity('matchEnded')
                await self.endMatch(ctx)

        @self.command(name='another')
        async def anotherMatch(ctx):
            message = 'Starting another match with the same players.\n'
            await ctx.send(message)
            await _startMatch(ctx, *self.match.players)

        @self.command(name='goodnight')
        async def goodnight(ctx):
            message = 'Ending the session here... '
            # If we lost or won, add to the message
            if self.match.scores["blue"] > self.match.scores["red"]:
                message += 'better to end on a high note!'
            else:
                message += 'it\'s not going anywhere, let\'s call it a night.'
            await ctx.send(message)
            await bot.setBotActivity('idle')

    async def setBotActivity(self, state):
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=self.stateActivityMapping[state]))

    async def playMatch(self, ctx, side):
        if self.match == None:
            await ctx.send('No match in progress. Use "**!startMatch**" to start a new match.')
            return

        if side == 'attack':
            self.match.playingOnSide = 'attack'
        else:
            self.match.playingOnSide = 'defense'

        message = f'You are starting on **{side}**.'
        await ctx.send(message)

        await self.playRound(ctx)

    async def playRound(self, ctx):
        message = f'The current score is **{self.match.scores["blue"]}**:**{self.match.scores["red"]}**.\n'
        message += f'Here is your lineup for round {self.match.currRound}:\n'

        if self.match.playingOnSide == 'attack':
            operators = self.match.getAttackers()
        else:
            site = self.match.getPlayedSite()
            message += f'Choose the **{site}** site.\n'
            operators = self.match.getDefenders()

        for player, operator in zip(self.match.players, operators):
            message += f'{player.display_name} plays **{operator}**\n'

        if self.match.currRound != 6:
            message += 'Use "**!won**" or "**!lost**" to continue.'
        elif self.match.scores["red"] == 3:
            message += 'If you won, use "**!won attack**" (or "**!won defense**") to start overtime on the specified side, otherwise use **!lost** to end the match.'
        elif self.match.scores["blue"] == 3:
            message += 'If you lost, use "**!lost attack**" (or "**!lost defense**") to start overtime on the specified side, otherwise use **!won** to end the match.'

        await ctx.send(message)

    async def endMatch(self, ctx):
        message = f'The match is over! The final score was **{self.match.scores["blue"]}**:**{self.match.scores["red"]}**. '
        message += 'Use "**!another**" to start a new match with the same players or "**!goodnight**" to end the session.'
        await ctx.send(message)

    def validatePlayerNames(self, ctx, playerNames):
        members = ctx.guild.members

        # Validate that the given players are members of the server
        for player in playerNames:
            if player not in members:
                print(f"{player.name} is not a member of this server.")
                return False

        return True


if __name__ == "__main__":
    bot = RainbowBot()
    bot.run(TOKEN)
