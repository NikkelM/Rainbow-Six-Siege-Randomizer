import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from rainbow import Rainbow

match = None

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.command(name='startMatch')
async def _startMatch(ctx):
    # TODO: If a map is already running, ask if they really want to reset
    # TODO: Offer a flag that skips confirmation
    message = 'Starting a new match...\n'
    # TODO: Make this a class and use self.match
    global match
    match = Rainbow()

    message += f'Ban the **{match.getMapBan()}** map in rotation, and these operators:\n'
    attBans, defBans = match.getOperatorBans()
    att1, att2 = attBans
    def1, def2 = defBans
    message += f'Attack: **{att1}** or alternatively **{att2}**\n'
    message += f'Defense: **{def1}** or alternatively **{def2}**\n'

    message += '\nTell me **all** banned operators using !bans'

    await ctx.send(message)


@bot.command(name='bans')
async def _bans(ctx, *args):
    if match == None:
        await ctx.send('No match in progress. Use !startMatch to start a new match.')
        return

    bans = ' '.join(args[0:4])
    bans = ', '.join(f'**{ban}**' for ban in match.matchOperatorName(bans))

    message = f'The following operators are banned in this match:\n{bans}\n'
    message += 'Are you starting on attack or defense? Use !startPlaying a or !startPlaying d'
    await ctx.send(message)

if __name__ == "__main__":
    bot.run(TOKEN)
