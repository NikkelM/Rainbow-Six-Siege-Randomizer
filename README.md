# Random Six Bot

A discord bot that randomizes bans, operator selections and more for Rainbow Six: Siege.

## Usage

The bot has the following commands, some of which can be invoked using a reaction instead of a message:

### Match Management

Commands related to setting up matches and managing players.

| Command | Argument | Description |
| ------- | -------- | ----------- |
| `!startMatch`, `!start`, `!play` | List of `@Player` mentions, or `here` | Starts a new match with up to five players. Use **!startMatch here** to start a match with everyone in your current voice channel, or **!startMatch @player1 @player2...** to start a match with the mentioned players. This command must be used first in order for any other match commands to work. |
| `!addPlayers`, `!addPlayer` | List of `@Player` mentions | Adds additional players to the match. Use **!addPlayers @player1 @player2...** to add the mentioned players to the match. The total number of players cannot exceed five, use **!removePlayers** first if you need to. |
| `!removePlayers`, `!removePlayer` | List of `@Player` mentions | Removes players from the match. Use **!removePlayers @player1 @player2...** to remove the mentioned players from the match. At least one player must remain in the match. |
| `!another`, `!again`, 👍 | `here` 🎤 | Starts a new match with the same players as the previous one, or with everyone in the current voice channel if the `here` argument was provided. |
| `!goodnight`, `!bye`, 👎 | `delete` ✋ | Ends the current match. Use the `delete` argument to delete the match from the database (i.e. if there were blatant cheaters and you do not want the data to skew statistics). |

### Ongoing Match

Commands to interact with an ongoing match, such as banning operators or playing rounds.

| Command | Argument | Description |
| ------- | -------- | ----------- |
| `!setMap`, `!map` | A valid `map` | Sets the map for the match. This will influence the sites displayed for defensive rounds. Use **!setMap map** to set the map. A map can be set at any point in the match. |
| `!ban` | List of operator names | Bans operators from the match. Use **!ban op1 op2...** to ban the mentioned operators from the match. You can ban as many operators as you like. |
| `!unban` | List of operator names | Unbans operators from the match. Use **!unban op1 op2...** to unban the mentioned operators from the match. |
| `!attack`, `!startAttack`, ⚔️ | | Starts the match on attack. |
| `!defense`, `!startDefense`, `!defend`, 🛡️ | | Starts the match on defense. |
| `!won`, `!w` | `attack` ⚔️ or `defense` 🛡️, if winning starts overtime | Marks the current round as won and starts a new round. If winning starts overtime, you must specify the side you start overtime on with **!won attack** ⚔️ or **!won defense** 🛡️. |
| `!lost`, `!l` | `attack` ⚔️ or `defense` 🛡️, if losing starts overtime | Marks the current round as lost and starts a new round. If losing starts overtime, you must specify the side you start overtime on with **!lost attack** ⚔️ or **!lost defense** 🛡️. |
| `!swap`, `!switch` | A `@Player` mention (optional) and a valid operator name | Swaps the operator the given player is playing in the current round with the given operator. If no `@Player` mention is given, the message author is assumed to be switching to the given operator. |
| `!site`, `!swapSite` | A site number between 1 and 4 | Changes the site the round is played on if playing on defense. Only sites that have not been won yet can be switched to. Use **!site <siteNumber>** to change the site for the current round. |

### Tracking Match Statistics

Commands to track additional statistics during an ongoing match.

| Command | Argument | Description |
| ------- | -------- | ----------- |
| `!interrogation` | A `@Player` mention (optional) | A player has interrogated someone as Caveira. If no `@Player` mention is provided, the message author is assumed to have gotten the interrogation. |
| `!ace` | A `@Player` mention (optional) | A player has gotten an ace. If no `@Player` mention is provided, the message author is assumed to have gotten the ace. |

### Statistics

Commands to view statistics for players and past matches.

| Command | Argument | Description |
| ------- | -------- | ----------- |
| `!stats` | A `statisticType` and optionally, a `@Player` mention. | View a specific statistic for yourself or another user. Available *statisticTypes* are: **overall**: General statistics for a player, such as win/loss ratios for maps and operators. **server**: The same as the **overall** statistic, but for matches played on the current server. If no *statisticType* is given, the **overall** statistics for mentioned player are displayed. If no player is mentioned, the message author's statistics are displayed. |

### General

Commands that allow you to manage the bot itself.

| Command | Argument | Description |
| ------- | -------- | ----------- |
| `!repeatMessage`, `!repeat`, `!sayAgain` | | Sends the last message sent by the bot again as a new message. |
| `!version` | | Displays the version of the bot. |
| `!help` | | Shows a list of all commands and their descriptions. Use `!help command` to view a description of a specific command, and `!help category` to view all commands from the given category. |

## Setup

Install the dependencies with the following command:

```bash
pip install -r requirements.txt
```

Then, create a Discord bot. You can follow the [discord.py documentation](https://discordpy.readthedocs.io/en/latest/discord.html) to learn how to do so.
The bot needs the `Server Members` and `Messages` intents to work properly, and the following permissions (to be configured under `OAuth2` -> `URL Generator` -> `bot`):

- Read Messages/View Channels
- Send Messages
- Manage Messages

After selecting the given intents and permissions, an invite link is generated that you can use to add the bot to your server.

Create a `.env` file and add your bot's token (which you can generate on the `Bot` page):

```env
DISCORD_BOT_TOKEN=your_token_here
IS_DEBUG=1
```

You can now run the Discord bot with the following command, which will log it in and allow you to use the commands to interact with it:

```bash
python bot.py
```

If you want to host the bot on a VM, follow the instructions below.

## Hosting

This section details how to set up the bot to run on Google Cloud Compute, using Docker.

First, create a new project on the [Google Cloud Console](https://console.cloud.google.com/) and follow the steps to create a billing account.
Then, on your machine, install the [gcloud CLI](https://cloud.google.com/sdk/docs/install), authenticate with your account and configure Docker to use the `gcloud` credentials with the following commands:

```bash
gcloud auth login
gcloud auth configure-docker
```

You can then build the Docker image with the following command, make sure to replace `<TOKEN>` with your bot's token and `<projectId>` with your project's ID:

```bash
docker build --build-arg DISCORD_BOT_TOKEN=<TOKEN> --build-arg IS_DEBUG=0 -t gcr.io/<projectId>/rainbow-six-siege-discord-bot .
docker push gcr.io/<projectId>/rainbow-six-siege-discord-bot
```

### Creating the VM

This first section will detail the settings to use when creating the VM on Google Cloud Compute, using the always free tier for all components.

Name: `rainbow-six-siege-discord-bot` - If you choose a different name, make sure to replace it in all of the commands below.

Region: Choose one of the following to stay within always free usage limits:
- Oregon: `us-west1`
- Iowa: `us-central1`
- South Carolina: `us-east1`

Machine type: `e2-micro`

VM provisioning model: `Standard`

Boot disk: `Standard persistent disk` with `10GB` storage.

Firewall: Enable `Allow HTTPS traffic`

Network interfaces: Set `Network Service Tier` to `Standard`

Management: Under `Automation`, set the following as the startup script for the VM:

```bash
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
gcloud auth configure-docker
docker pull gcr.io/<projectId>/rainbow-six-siege-discord-bot
docker image prune -f
docker run -d -p 80:80 -v rainbow-six-siege-discord-bot-database:/app/data gcr.io/<projectId>/rainbow-six-siege-discord-bot
```

This script will stop and remove all running Docker containers, pull the latest version of the image, and run it.

Then, hit `Create` to create the VM.

### Setting up & Running the bot

Once you have a VM set up, SSH into it, either directly through the Google Cloud Console or using the following command:

```bash
gcloud compute ssh rainbow-six-siege-discord-bot
```

First, use the following commands to set up Docker and authenticate with `gcloud`:

```bash
sudo apt-get update
sudo apt-get install docker.io
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update && sudo apt-get install google-cloud-cli
gcloud auth login
gcloud auth configure-docker
```

Docker has now been set up, and you should be authenticated with your GCP account.
Before running the next commands, make sure to first copy the database file (`rainbowDiscordBot.db`) to the VM.
You can create a new database file by shortly starting the bot locally and then copying it out from the `data` folder.

Then, set up a new Docker volume and copy the database file into it:

```bash
docker volume create rainbow-six-siege-discord-bot-database
docker run -d --name temp-container -v rainbow-six-siege-discord-bot-database:/data busybox sleep infinity
docker cp ./rainbowDiscordBot.db temp-container:/data/rainbowDiscordBot.db
docker stop temp-container
docker rm temp-container
docker rmi busybox
rm ./rainbowDiscordBot.db
```

Now, pull and run the image you previously built:

```bash
docker pull gcr.io/<projectId>/rainbow-six-siege-discord-bot
docker run -d -p 80:80 -v rainbow-six-siege-discord-bot-database:/app/data gcr.io/<projectId>/rainbow-six-siege-discord-bot
```

If you've followed all steps correctly, the bot should now be logged in and respond to commands.

Whenever you update the bot, you should rebuild the image and push it to the container registry, then simply restart the VM to have it run the startup script and pull and run the new image.

---

If you enjoy the app and want to say thanks, consider buying me a [coffee](https://ko-fi.com/nikkelm) or [sponsoring](https://github.com/sponsors/NikkelM) this project.
