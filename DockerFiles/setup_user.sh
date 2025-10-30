#!/bin/bash
#######################################################################
# setup_user.sh
# ---------------------------------------------------------------------
# This script runs when the container starts.
# It creates the hosting user from $USERNAME and $PASSWORD
# and configures SSH to allow:
#   - root access (password: youstable@123)
#   - hosting user access
#######################################################################

set -e  # Stop on error

# Check for required environment variables
if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
  echo "❌ ERROR: USERNAME and PASSWORD environment variables are required."
  exit 1
fi

echo ">> Creating container user: $USERNAME"

# Create user if not exists
if ! id "$USERNAME" &>/dev/null; then
  useradd -m -s /bin/bash "$USERNAME"
  echo "$USERNAME:$PASSWORD" | chpasswd
  usermod -aG sudo "$USERNAME"
fi

# Configure root password for admin use
echo "root:youstable@123" | chpasswd

# Configure SSH
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
grep -q "AllowUsers" /etc/ssh/sshd_config && \
  sed -i "s/^AllowUsers.*/AllowUsers root $USERNAME/" /etc/ssh/sshd_config || \
  echo "AllowUsers root $USERNAME" >> /etc/ssh/sshd_config

# Create the user's web directory
mkdir -p /home/$USERNAME/www
chown -R $USERNAME:$USERNAME /home/$USERNAME/www

echo "✅ User $USERNAME created successfully"
echo "🔐 Root password: youstable@123"
echo "🚀 Starting Supervisor..."
/usr/bin/supervisord -n
