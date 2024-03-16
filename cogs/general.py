from discord.ext import commands
from bot import RainbowBot
from cogs.botHelp import CustomHelpCommand
from version import __version__ as VERSION

class General(commands.Cog, name='General'):
    """Commands that allow you to manage the bot itself."""
    def __init__(self, bot: RainbowBot):
        self.bot = bot
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    @commands.command(aliases=['repeatMessage', 'repeat', 'sayAgain'])
    async def _repeatMessage(self, ctx: commands.Context):
        """Sends the last message sent by the bot again as a new message."""
        _, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return

        discordMessage['matchMessageId'] = None
        await self.bot.sendMatchMessage(ctx, discordMessage)

    @commands.command(aliases=['about', 'version'])
    async def _about(self, ctx: commands.Context):
        """Displays useful information concerning the bot."""
        message = 'The RandomSixBot allows you to randomly select bans, operators and more for *Rainbow Six: Siege*.\n\n'
        message += 'You can view a list of available commands using **!help**, and learn more about a specific command with **!help <command>**.\n\n'
        message += f'The bot is currently running on **v{VERSION}**.\n\n'
        message += 'The bot is created and maintained by [@NikkelM](<https://github.com/NikkelM>), you can find it on [GitHub](<https://github.com/NikkelM/RainbowSixSiegeRandomizer>).\n'
        message += 'Do you want to say thank you and support the bot? You can do so by [buying me a coffee](<https://ko-fi.com/nikkelm>)!\n\n'
        await ctx.send(message)

async def setup(bot: RainbowBot):
    await bot.add_cog(General(bot))