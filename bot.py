import discord
import os
import re
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
        self.matchMessage = None
        self.resetMessageContent()

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
        async def _startMatch(ctx, *playerNames):
            self.match = RainbowMatch()

            if len(playerNames) > 0:
                playerObjects = self.validatePlayerNames(ctx, playerNames)
                if playerObjects is not None:
                    self.match.setPlayerNames(playerObjects)
                    self.messageContent['playersBanner'] = f"Starting a new match with {self.match.playersString}.\n"
                else:
                    self.messageContent['playersBanner'] = 'At least one of the players you mentioned is not on this server, please try again.'
                    await bot.sendMessage(ctx)
                    return
            else:
                self.messageContent['playersBanner'] = 'No players set. Use "**!startMatch @player1 @player2...**" to set players.'
                await bot.sendMessage(ctx)
                return

            self.messageContent['matchMetadata'] = f'Ban the **{self.match.getMapBan()}** map in rotation, and these operators:\n'
            attBans, defBans = self.match.getOperatorBanChoices()
            att1, att2 = attBans
            def1, def2 = defBans
            self.messageContent['matchMetadata'] += f'Attack:  **{att1}** or if banned **{att2}**\n'
            self.messageContent['matchMetadata'] += f'Defense: **{def1}** or if banned **{def2}**\n'

            self.messageContent['actionPrompt'] = 'Next, tell me the "**!bans op1 op2...**":'

            await bot.sendMessage(ctx)
            await bot.setBotActivity('matchInProgress')

        @_startMatch.error
        async def _startMatch_error(ctx, error):
            if isinstance(error, commands.BadArgument):
                await bot.setBotActivity('idle')
                self.messageContent['playersBanner'] = 'All players must be mentioned directly using the @ syntax and be users on this server (did you mention a role?), please try again.'
                await bot.sendMessage(ctx)


        @self.command(name='bans')
        async def _bans(ctx, *args):
            if self.match == None:
                self.messageContent['playersBanner'] = 'No match in progress. Use "**!startMatch**" to start a new match.'
                await bot.sendMessage(ctx)
                return

            self.messageContent['playersBanner'] = f"Paying a match with {self.match.playersString}.\n"

            bans = ' '.join(args[0:4])
            sanitized_bans = self.match.banOperators(bans)

            if len(sanitized_bans) == 0:
                self.messageContent['matchMetadata'] = 'No operators are banned in this match.\n'
            else:
                bans = ', '.join(f'**{ban}**' for ban in sanitized_bans if ban is not None)
                self.messageContent['matchMetadata'] = f'The following operators are banned in this match:\n{bans}\n'
                unrecognized_bans = [ban for ban in zip(sanitized_bans, args) if ban[0] is None]
                if len(unrecognized_bans) > 0:
                    self.messageContent['matchMetadata'] += f'The following operators you passed were not recognized:\n{", ".join([f"**{ban[1]}**" for ban in unrecognized_bans])}\n'

            self.messageContent['actionPrompt'] = 'Use "**!addBans**" to add new bans.\n'
            self.messageContent['actionPrompt'] += 'Use "**!startAttack**" or "**!startDefense**" to start the match.'
            await bot.sendMessage(ctx)

        @self.command(name='addBans')
        async def _bans(ctx, *args):
            if self.match == None:
                message = 'No match in progress. Use "**!startMatch**" to start a new match.'
                await bot.sendMessage(ctx, message)
                return

            message = ''
            bans = ' '.join(args[0:4])
            sanitized_bans = self.match.banOperators(bans)

            if len(sanitized_bans) == 0:
                message += 'No operators were passed with the command.\n'
            else:
                bans = ', '.join(f'**{ban}**' for ban in sanitized_bans if ban is not None)
                message = f'The following operators are now **also** banned in this match:\n{bans}\n'
                unrecognized_bans = [ban for ban in zip(sanitized_bans, args) if ban[0] is None]
                if len(unrecognized_bans) > 0:
                    message += f'The following operators you passed were not recognized:\n{", ".join([f"**{ban[1]}**" for ban in unrecognized_bans])}\n'

            message += 'Use "**!startAttack**" or "**!startDefense**" to start the match.'
            await bot.sendMessage(ctx, message)

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
                    message = 'You must specify what side you start overtime on. Use **!won attack** or **!won defense**.'
                    await bot.sendMessage(ctx, message)
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
                    message = 'You must specify what side you start overtime on. Use **!lost attack** or **!lost defense**.'
                    await bot.sendMessage(ctx, message)
                    return
            if self.match.resolveRound('lost', overtimeSide):
                await self.playRound(ctx)
            else:
                await bot.setBotActivity('matchEnded')
                await self.endMatch(ctx)

        @self.command(name='another')
        async def anotherMatch(ctx):
            # TODO: Validate that the players object here works as intended
            await _startMatch(ctx, *self.match.players)

        @self.command(name='goodnight')
        async def goodnight(ctx):
            message = 'Ending the session here... '
            # If we lost or won, add to the message
            if self.match.scores["blue"] > self.match.scores["red"]:
                message += 'better to end on a high note!'
            else:
                message += 'it\'s not going anywhere, let\'s call it a night.'
            await bot.sendMessage(ctx, message)
            bot.match = None
            bot.matchMessage = None
            await bot.setBotActivity('idle')

    async def setBotActivity(self, state):
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=self.stateActivityMapping[state]))

    async def playMatch(self, ctx, side):
        if self.match == None:
            message = 'No match in progress. Use "**!startMatch**" to start a new match.'
            await bot.sendMessage(ctx, message)
            return
        
        self.messageContent['playersBanner'] = f"Playing a match with {self.match.playersString}.\n"
        
        if side == 'attack':
            self.match.playingOnSide = 'attack'
        else:
            self.match.playingOnSide = 'defense'

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

        await bot.sendMessage(ctx, message)

    async def endMatch(self, ctx):
        message = f'The match is over! The final score was **{self.match.scores["blue"]}**:**{self.match.scores["red"]}**. '
        message += 'Use "**!another**" to start a new match with the same players or "**!goodnight**" to end the session.'
        await bot.sendMessage(ctx, message)
        self.matchMessage = None

    def validatePlayerNames(self, ctx, playerNames):
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

    def resetMessageContent(self):
        self.messageContent = {
            'playersBanner': '',
            'matchScore': '',
            'matchMetadata': '',
            'roundMetadata': '',
            'roundLineup': '',
            'actionPrompt': ''
        }

    async def sendMessage(self, ctx):
        message = '\n'.join([v for v in self.messageContent.values() if v != ''])

        if self.matchMessage:
            await self.matchMessage.edit(content=message)
        else:
            self.matchMessage = await ctx.send(message)


if __name__ == "__main__":
    bot = RainbowBot()
    bot.run(TOKEN)
