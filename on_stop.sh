#!/bin/bash

# This script runs every time you are reseting / redeploying the services
# e.g. server is being restarted, deploying new container, rotating secrets, updating models, back up logs, notify admin, dump metrics etc ~ cp logs/ app-logs/backup-"$(date +%F_%T)".log

echo "[!] Stopping services..."

docker-compose -p tarohub down

