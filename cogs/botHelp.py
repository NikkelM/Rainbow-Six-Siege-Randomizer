import discord
from discord.ext import commands
import re
from version import __version__ as VERSION

class CustomHelpCommand(commands.HelpCommand):
    """Overwrites the default help command for a better looking help message."""
    def get_command_signature(self, command: commands.Command):
        return '%s%s %s' % (self.context.clean_prefix, command.qualified_name, command.signature)
    
    async def send_error_message(self, error):
        embed = discord.Embed(title="Error", description=f"{error} Use **!help** to view the list of commands.", color=discord.Color.red())
        channel = self.get_destination()

        await channel.send(embed=embed)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title=f"Help - RandomSixBot v{VERSION}", color=discord.Color.blurple())

        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [re.sub(r'!_', '!', self.get_command_signature(c)) for c in filtered]

            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)    
    
    async def send_help_embed(self, title, description, commands):
        embed = discord.Embed(title=title, description=description or "No help found...")

        if filtered_commands := await self.filter_commands(commands, sort=True):
            for command in filtered_commands:
                embed.add_field(name=re.sub(r'!_', '!', self.get_command_signature(command)), value=command.help or "No help found...")

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(title=re.sub(r'!_', '!', self.get_command_signature(command)), color=discord.Color.from_rgb(57, 255, 20))
        if command.help:
            embed.description = command.help
        if alias := command.aliases:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        title = self.get_command_signature(group)
        await self.send_help_embed(title, group.help, group.commands)

    async def send_cog_help(self, cog: commands.Cog):
        title = cog.qualified_name or "No Category"
        await self.send_help_embed(title, cog.description, cog.get_commands())
