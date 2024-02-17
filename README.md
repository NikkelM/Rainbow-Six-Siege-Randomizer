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
- Manage Messages
<!-- TODO -->
<!-- - Add Reactions -->

After selecting the given intents and permissions, an invite link is generated that you can use to add the bot to your server.

Create a `.env` file and add the generated token:

```env
DISCORD_BOT_TOKEN=your_token_here
```

You can now run the Discord bot with the following command, which will log it in and allow you to use the commands to interact with it:

```bash
python bot.py
```

## Usage

The bot has the following commands:

| Command | Argument | Description |
| ------- | -------- | ----------- |
| `!startMatch` | List of `@Player` mentions | Starts a new match with the given players. Must be used in order for any other command to work. |
| `!addPlayers` | List of `@Player` mentions | Adds the given players to the match. |
| `!removePlayers` | List of `@Player` mentions | Removes the given players from the match. At least one player must remain in the match. |
| `!ban` | List of operator names | Bans the given operators from the match. |
| `!unban` | List of operator names | Unbans the given operators from the match. |
| `!startAttack` | | Starts the match on the attacking side. If called during an ongoing match, shuffles a new attack phase without changing the score. |
| `!startDefense` | | Starts the match on the defending side. If called during an ongoing match, shuffles a new defense phase without changing the score. |
| `!won` | `attack` or `defense`, if winning starts overtime | Resolves the ongoing round as won, updating the scores and starting a new round. If winning started overtime, `attack` must be supplied if starting overtime on attack, otherwise `defense`. |
| `!lost` | `attack` or `defense`, if winning starts overtime | Resolves the ongoing round as lost, updating the scores and starting a new round. If losing started overtime, `attack` must be supplied if starting overtime on attack, otherwise `defense`. |
| `!another` | | Starts a new match with the same players. |
| `!goodnight` | | Ends the session. |