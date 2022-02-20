# Logger Anal-s setup

## clone logger repo

[Anal-s documentation](https://github.com/memlish/anal-s)
```bash 
sudo git clone https://github.com/memlish/anal-s.git
sudo mkdir ~/data/esdata/

sudo chmod 777 ~/data/esdata/

cd ~/src/anal-s/
```

## Fix for the runtime error 

```bash
sudo sysctl -w vm.max_map_count=262144
```

## Run logger docker

```bash
sudo docker-compose up
```

check logs http://<YOUR_PUBLIC_IP>:<YOUR_PORT>/app/kibana