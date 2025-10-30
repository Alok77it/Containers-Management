#!/bin/bash

# Variables
DATE=$(date +'%Y-%m-%d_%H-%M-%S')
BACKUP_DIR="/backups/$DATE"
REMOTE_SERVER="69.10.34.254"
REMOTE_DIR="/data/backup/test/"
SSH_KEY_PATH="/root/.ssh/id_rsa"  # Modify this path to your SSH private key
CONTAINER_VOLUMES_DIR="/srv/"
MYSQL_USER="root"  # Modify as per your DB credentials
MYSQL_PASSWORD="password"  # Modify as per your DB credentials
PGSQL_USER="postgres"  # Modify as per your DB credentials
PGSQL_PASSWORD="password"  # Modify as per your DB credentials

# Create backup directory
mkdir -p $BACKUP_DIR

# ============================
# 1. Backup Container Volumes
# ============================
echo "Backing up container volumes..."
tar -czf $BACKUP_DIR/container_volumes_backup.tar.gz -C $CONTAINER_VOLUMES_DIR .

# ============================
# 2. Backup MySQL Databases
# ============================
echo "Backing up MySQL databases..."
for container in $(docker ps -q); do
    container_name=$(docker inspect --format '{{.Name}}' $container | sed 's/\///g')
    echo "Backing up MySQL database from container $container_name..."
    docker exec -i $container mysqldump -u$MYSQL_USER -p$MYSQL_PASSWORD --all-databases > $BACKUP_DIR/mysql_${container_name}_all_databases.sql
done

# ============================
# 3. Backup PostgreSQL Databases
# ============================
echo "Backing up PostgreSQL databases..."
for container in $(docker ps -q); do
    container_name=$(docker inspect --format '{{.Name}}' $container | sed 's/\///g')
    echo "Backing up PostgreSQL database from container $container_name..."
    docker exec -i $container pg_dumpall -U $PGSQL_USER > $BACKUP_DIR/pgsql_${container_name}_all_databases.sql
done

# ============================
# 4. Transfer Backups to Remote Server
# ============================
echo "Transferring backups to remote server..."
scp -i $SSH_KEY_PATH -r $BACKUP_DIR $REMOTE_SERVER:$REMOTE_DIR

# ============================
# 5. Clean up old backups (Optional)
# ============================
# Delete backups older than 30 days
find /backups/* -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed and transferred successfully."

