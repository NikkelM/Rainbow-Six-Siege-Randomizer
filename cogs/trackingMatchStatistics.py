import discord
from discord.ext import commands
from bot import RainbowBot

class TrackingMatchStatistics(commands.Cog, name='Tracking Match Statistics'):
    """Commands to track additional statistics during an ongoing match."""
    def __init__(self, bot: RainbowBot):
        self.bot = bot

    @commands.command(aliases=['interrogation'])
    async def _interrogation(self, ctx: commands.Context, player: discord.User = None):
        """A player has interrogated someone as Caveira. If no **@Player** mention is provided, the message author is assumed to have gotten the interrogation."""
        match, discordMessage, canContinue = await self.bot.getMatchData(ctx)
        if not canContinue:
            return
        if ctx.message.id != discordMessage['matchMessageId'] or not discordMessage['matchMessageId']:
            await ctx.message.delete()
        
        if player is None:
            player = ctx.author

        # If the mentioned player is not a player in the match, return an error message.
        if player.id not in [matchPlayer['id'] for matchPlayer in match.players]:
            discordMessage['messageContent']['statsBanner'] = f'{player.mention} is not playing in the current match, so they cannot have interrogated someone.'
        else:
            match.addPlayerStat(player.id, 'interrogation')
            # TODO: Track how many interrogations in this match for this player
            discordMessage['messageContent']['statsBanner'] = f'{player.mention} has interrogated someone!'

        self.bot.saveOngoingMatch(ctx, match)
        await self.bot.sendMessage(ctx, discordMessage)

async def setup(bot: RainbowBot):
    await bot.add_cog(TrackingMatchStatistics(bot))