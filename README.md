# memlish

## Pull:

```git clone https://github.com/memlish/memlish.git --recurse-submodules```

## What should be up and run:

To run bot you should run such services:

1) Run jina server: `docker-compose.jina.server.yml`
2) Run bot: `docker-compose.tgbot.yml`

## How to run server:

`docker-compose --env-file ~/memlish.env -f docker-compose.jina.server.yml up --build -d`

## How to run bot:

`docker-compose -f docker-compose.tgbot.yml up --build -d`

## memlish.env

```
MONGODB_CONNECTION_STRING=<mongo_connection_string>
BOT_TOKEN=<telegram_bot_token>
USE_POLLING=True
SERVER_NAME=<public_dns_domain>
JINA_FLOW_PORT=7070
AWS_ACCESS_KEY_ID=<>
AWS_SECRET_ACCESS_KEY=<>
```
