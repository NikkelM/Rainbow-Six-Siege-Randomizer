# Rainbow Six: Siege Randomizer

A discord bot that randomizes bans, operator selection and more for Rainbow Six: Siege.

## Setup

Install the dependencies with the following command:

```bash
pip install -r requirements.txt
```

Then, create a Discord bot. You can follow the [discord.py documentation](https://discordpy.readthedocs.io/en/latest/discord.html) to learn how to do so.
The bot needs the `Server Members` and `Messages` intents to work properly, and the following permissions (to be configured under OAuth2 -> URL Generator -> bot):

- Read Messages/View Channels
- Send Messages
<!-- TODO -->
<!-- - Add Reactions -->
<!-- - Manage Messages -->

After selecting the given intents and permissions, an invite link is generated that you can use to add the bot to your server.

Create a `.env` file and add the generated token:

```env
DISCORD_BOT_TOKEN=your_token_here
```

You can now run the Discord bot with the following command, which will log it in and allow you to use the commands to interact with it:

```bash
python bot.py
```

<!-- TODO -->
<!-- ## Usage

The bot has the following commands: -->
