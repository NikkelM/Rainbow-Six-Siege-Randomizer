from discord.ext import commands
from bot import RainbowBot
from botHelp import CustomHelpCommand
from version import __version__ as VERSION

class General(commands.Cog, name='General'):
    """This category contains commands that are related to managing the bot itself."""
    def __init__(self, bot):
        self.bot: RainbowBot = bot
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    @commands.command(aliases=['repeatMessage', 'repeat', 'sayAgain'])
    async def _repeatMessage(self, ctx: commands.Context):
        """Sends the last message sent by the bot again as a new message."""
        _, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return

        discordMessage['matchMessageId'] = None
        await self.bot.sendMessage(ctx, discordMessage)

    @commands.command(name='version')
    async def _version(self, ctx: commands.Context):
        """Displays the version of the bot."""
        await ctx.send(f'RandomSixBot is running on v{VERSION}.')

async def setup(bot: RainbowBot):
    await bot.add_cog(General(bot))