# AWS Setup and sync data

## AWS setup

```bash
sudo apt update
sudo apt install unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" 
unzip awscliv2.zip
sudo ./aws/install
aws configure
```
paste **aws_access_key_id** and **aws_secret_access_key**

## Sync data

```bash
sudo aws s3 sync s3://memlish.head.prod/imgflip/ ~/data/imgflip/
```
