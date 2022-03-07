# VM setup

```bash
lsblk
```

![lsblk output](https://github.com/memlish/memlish/blob/main/docs/images/lsblk_output.png)


```bash
sudo mkdir /mnt/sdd
sudo mount -o discard /dev/nvme0n1p1 /mnt/sdd
sudo mkdir /mnt/sdd/data
ln -s /mnt/sdd/data data
sudo mkdir /mnt/sdd/src
ln -s /mnt/sdd/src src
```

![mount drive](https://github.com/memlish/memlish/blob/main/docs/images/after_mount_ls.png)

change '/mnt/sdd/src' permissions
```bash
sudo chown -R ubuntu /mnt/sdd/src/
```
