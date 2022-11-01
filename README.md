# memlish
sudo docker-compose --env-file ~/memlish.env -f docker-compose.jupyter.yml up --build -d
## Pull:

```git clone https://github.com/memlish/memlish.git --recurse-submodules```


## Set up memlish infrastructure

Complete the following steps to configure and run bot on new VM:

1) [Configure VM](https://github.com/memlish/memlish/blob/main/docs/vm_setup.md)
2) [Env variables setup](https://github.com/memlish/memlish/blob/main/docs/env_variables_setup.md)
3) [AWS setup and sync data](https://github.com/memlish/memlish/blob/main/docs/aws_data_setup.md)
4) [Clone Repo](https://github.com/memlish/memlish/blob/main/docs/repo_setup.md)
5) [Docker setup](https://github.com/memlish/memlish/blob/main/docs/docker_setup.md) 
6) [Mongo setup](https://github.com/memlish/memlish/blob/main/docs/mongo_setup.md)
7) [Logger Anal-s setup](https://github.com/memlish/memlish/blob/main/docs/logs_setup.md)
8) In case of DNS mask change, generate new ssl certs (cert.pem, private.key) and put them into `infrastructure/nginx/certs/` folder. [Documentation](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#a-ssl-certificate)

## SSL certs generate command. 
Make sure you enter the correct FQDN - your public DNS domain.
```bash
openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem
```

## How to run server:

`docker-compose --env-file ~/memlish.env -f docker-compose.jina.server.yml up --build -d`

## How to run bot:

`docker-compose -f docker-compose.tgbot.yml up --build -d`

docker-compose --env-file ~/memlish.env -f docker-compose.jupyter.yml up --build -d