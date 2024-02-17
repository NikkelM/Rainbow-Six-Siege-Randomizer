FROM python:3.9-bullseye

ARG DISCORD_BOT_TOKEN
ENV DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]