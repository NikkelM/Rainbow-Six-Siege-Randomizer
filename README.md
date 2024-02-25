# Random Six Bot

A discord bot that randomizes bans, operator selections and more for Rainbow Six: Siege.

## Usage

The bot has the following commands:

| Command | Argument | Description |
| ------- | -------- | ----------- |
| `!startMatch` | List of `@Player` mentions | Starts a new match with the given players. Must be used in order for any other command to work. |
| `!addPlayers` | List of `@Player` mentions | Adds the given players to the match. |
| `!removePlayers` | List of `@Player` mentions | Removes the given players from the match. At least one player must remain in the match. |
| `!setMap` | A valid `map` | Sets the map that is being played. |
| `!ban` | List of operator names | Bans the given operators from the match. |
| `!unban` | List of operator names | Unbans the given operators from the match. |
| `!startAttack` | | Starts the match on the attacking side. If called during an ongoing match, shuffles a new attack phase without changing the score. |
| `!startDefense` | | Starts the match on the defending side. If called during an ongoing match, shuffles a new defense phase without changing the score. |
| `!won` | `attack` or `defense`, if winning starts overtime | Resolves the ongoing round as won, updating the scores and starting a new round. If winning started overtime, `attack` must be supplied if starting overtime on attack, otherwise `defense`. |
| `!lost` | `attack` or `defense`, if losing starts overtime | Resolves the ongoing round as lost, updating the scores and starting a new round. If losing started overtime, `attack` must be supplied if starting overtime on attack, otherwise `defense`. |
| `!another` | | Starts a new match with the same players. |
| `!goodnight` | | Ends the session. |

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
<!-- TODO -->
<!-- - Add Reactions -->

After selecting the given intents and permissions, an invite link is generated that you can use to add the bot to your server.

Create a `.env` file and add your bot's token (which you can generate on the `Bot` page):

```env
DISCORD_BOT_TOKEN=your_token_here
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
docker build --build-arg DISCORD_BOT_TOKEN=<TOKEN> -t gcr.io/<projectId>/rainbow-six-siege-discord-bot .
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
You can create a new database file by shortly starting the bot locally and then copying out from the `data` folder.

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
