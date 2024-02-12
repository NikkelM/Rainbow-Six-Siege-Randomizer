import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

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
  await ctx.send('Starting a new match!')

if __name__ == "__main__":
  bot.run(TOKEN)