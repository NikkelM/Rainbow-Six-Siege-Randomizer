from discord.ext import commands
from bot import RainbowBot
from version import __version__ as VERSION

class General(commands.Cog, name='General'):
    """This category contains commands that are related to managing the bot itself."""
    def __init__(self, bot):
        self.bot: RainbowBot = bot

    @commands.command(aliases=['repeatMessage', 'repeat', 'sayAgain'])
    async def _repeatMessage(self, ctx):
        """Sends the last message sent by the bot again as a new message."""
        _, discordMessage, canContinue = await self.bot._getMatchData(ctx)
        if not canContinue:
            return

        discordMessage['matchMessageId'] = None
        await self.bot._sendMessage(ctx, discordMessage)

    @commands.command(name='version')
    async def _version(self, ctx):
        """Displays the version of the bot."""
        await ctx.send(f'RandomSixBot is running on v{VERSION}.')

async def setup(bot: RainbowBot):
    await bot.add_cog(General(bot))