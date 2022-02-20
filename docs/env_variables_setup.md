# Environment variables

```bash
cd ~/

nano memlish.env
```

write env variables to **memlish.env**
```bash
MONGODB_CONNECTION_STRING=mongodb://<user>:<pass>@<vm_public_ip>:<exposed_port>/admin
MONGO_INITDB_ROOT_USERNAME=<user>
MONGO_INITDB_ROOT_PASSWORD=<pass>
BOT_TOKEN=<token>
USE_POLLING=False
SERVER_NAME=<vm_public_domain> #not IP!
JINA_FLOW_PORT=7070
DEBUG_MODE=True
AWS_ACCESS_KEY_ID=<>
AWS_SECRET_ACCESS_KEY=<>
```
