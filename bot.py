import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from rainbow import Rainbow

match = None

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.command(name='startMatch')
async def _startMatch(ctx, *playerNames: discord.Member):
    # TODO: If a map is already running, ask if they really want to reset
    # TODO: Offer a flag that skips confirmation
    message = ''
    # TODO: Make this a class and use self.match
    global match
    match = Rainbow()

    # If any amount of players is given, validate and set in the match object
    # Else, tell the user to set the players using !startMatch @playerNames
    if len(playerNames) > 0:
        if validatePlayerNames(ctx, playerNames):
            match.setPlayerNames(playerNames)
            message += f"Starting a new match with {', '.join([player.mention for player in playerNames])}.\n"
        else:
            message += 'At least one of the players you mentioned is not on this server, please try again.'
            await ctx.send(message)
            return
    else:
        message += 'No players set. Use "**!startMatch @player1 @player2...**" to set players.'
        await ctx.send(message)
        return

    message += f'Ban the **{match.getMapBan()}** map in rotation, and these operators:\n'
    attBans, defBans = match.getOperatorBans()
    att1, att2 = attBans
    def1, def2 = defBans
    message += f'Attack: **{att1}** or alternatively **{att2}**\n'
    message += f'Defense: **{def1}** or alternatively **{def2}**\n'

    message += '\nNext, tell me the "**!bans firstOp secondOp...**":'

    await ctx.send(message)


@_startMatch.error
async def startMatch_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('All players must be mentioned directly using the @ syntax and be users on this server, please try again.')


@bot.command(name='bans')
async def _bans(ctx, *args):
    if match == None:
        await ctx.send('No match in progress. Use "**!startMatch**" to start a new match.')
        return

    bans = ' '.join(args[0:4])
    bans = ', '.join(f'**{ban}**' for ban in match.matchOperatorNames(bans))

    message = f'The following operators are banned in this match:\n{bans}\n'
    message += 'Use "**!startAttack**" or "**!startDefense**" to start the match.'
    await ctx.send(message)


@bot.command(name='startAttack')
async def startAttack(ctx):
    await playMatch(ctx, 'attack')


@bot.command(name='startDefense')
async def startDefense(ctx):
    await playMatch(ctx, 'defense')


@bot.command(name='won')
async def startAttack(ctx, overtimeSide = None):
    if(match.currRound == 6 and match.scores["red"] == 3 and not overtimeSide):
        await ctx.send('You must specify what side you start overtime on. Use **!won attack** or **!won defense**.')
        return
    if match.resolveRound('won', overtimeSide):
        await playRound(ctx)
    else:
        await endMatch(ctx)


@bot.command(name='lost')
async def startDefense(ctx, overtimeSide = None):
    if(match.currRound == 6 and match.scores["blue"] == 3 and not overtimeSide):
        await ctx.send('You must specify what side you start overtime on. Use **!lost attack** or **!lost defense**.')
        return
    if match.resolveRound('lost', overtimeSide):
        await playRound(ctx)
    else:
        await endMatch(ctx)


@bot.command(name='another')
async def anotherMatch(ctx):
    message = 'Starting another match with the same players.\n'
    await ctx.send(message)
    await _startMatch(ctx, *match.players)


@bot.command(name='goodnight')
async def goodnight(ctx):
    message = 'Ending the session here... '
    # If we lost or won, add to the message
    if match.scores["blue"] > match.scores["red"]:
        message += 'better to end on a high note!'
    else:
        message += 'it\'s not going anywhere, let\'s call it a night.'
    await ctx.send(message)


async def playMatch(ctx, side):
    if match == None:
        await ctx.send('No match in progress. Use "**!startMatch**" to start a new match.')
        return

    if side == 'attack':
        match.setSide('attack')
    else:
        match.setSide('defense')

    message = f'You are starting on **{side}**.'
    await ctx.send(message)

    await playRound(ctx)


async def playRound(ctx):
    message = f'The current score is **{match.scores["blue"]}**:**{match.scores["red"]}**.\n'
    message += f'Here is your lineup for round {match.currRound}:\n'

    if match.side == 'attack':
        operators = match.getAttackers()
    else:
        site = match.getPlayedSite()
        message += f'Choose site number **{site}**.\n'
        operators = match.getDefenders()

    for player, operator in zip(match.players, operators):
        message += f'{player.display_name} plays **{operator}**\n'

    if match.currRound != 6:
        message += 'Use "**!won**" or "**!lost**" to continue.'
    elif match.scores["red"] == 3:
        message += 'If you won, use "**!won attack**" (or "**!won defense**") to start overtime on the specified side, otherwise use **!lost** to end the match.'
    elif match.scores["blue"] == 3:
        message += 'If you lost, use "**!lost attack**" (or "**!lost defense**") to start overtime on the specified side, otherwise use **!won** to end the match.'

    await ctx.send(message)


async def endMatch(ctx):
    message = f'The match is over! The final score was **{match.scores["blue"]}**:**{match.scores["red"]}**. '
    message += 'Use "**!another**" to start a new match with the same players or "**!goodnight**" to end the session.'
    await ctx.send(message)


def validatePlayerNames(ctx, playerNames):
    members = ctx.guild.members

    # Validate that the given players are members of the server
    for player in playerNames:
        if player not in members:
            print(f"{player.name} is not a member of this server.")
            return False

    return True


if __name__ == "__main__":
    bot.run(TOKEN)
