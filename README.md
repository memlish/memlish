# memlish

To run bot you should run such services:

1) Run jina server: `docker-compose.jina.server.yml`
2) Run bot: `docker-compose.tgbot.yml`

## How to run server:

`docker-compose --env-file ~/memlish.env -f docker-compose.jina.server.yml up --build`

## memlish.env

```
MONGODB_CONNECTION_STRING=<mongo_connection_string>
BOT_TOKEN=<telegram_bot_token>
USE_POLLING=True
SERVER_NAME=<public_dns_domain>
JINA_FLOW_PORT=7070
```