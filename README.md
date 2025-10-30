# 🚀 YouStable Container Hosting

![Container Automation](https://media.giphy.com/media/SWoSkN6DxTszqIKEqv/giphy.gif)

A fully automated, scriptable Docker container hosting solution for modern web hosting providers. Designed for reliability, scalability, and ease of use—with a clear upgrade path for advanced auto-scaling, AI healing, and alerting integrations.

---

## 📝 Overview

YouStable’s system enables seamless creation, management, and backup of Docker containers for multiple hosting plans:

- **Ubuntu 22.04**
- **Nginx + PHP + MySQL**
- **SSH access** (root & user)
- **Supervisor** for service orchestration
- **Persistent Volumes** for web files & databases
- **Random Ports:** Containers are assigned random SSH ports for security and traffic isolation.
- **Nginx DNS & Reverse Proxy:** Nginx maps domain names and routes HTTP/HTTPS traffic to the correct container and port.
- **Basic Monitoring:** Python scripts monitor container health, resource usage, and service status.
- **Package Installation:** Install packages in containers using name and URL for flexibility and automation.

---

## 🗂️ Directory Structure

```
DockerFiles/
├── Dockerfile.vPopular
├── Dockerfile.vProfessional
├── Dockerfile.vStable
├── Dockerfile.vStart
├── setup_user.sh           # Dynamic user creation script
├── supervisord.conf        # Supervisor config for services

scripts/
├── backup.sh               # Backup script for web files and databases
├── create_container.py     # Main container creation script
├── monitor.py              # Python-based monitoring script
├── package.py              # Script for installing packages by name & URL
```

---

## 💡 Hosting Plan Matrix

| Plan           | CPU | RAM  | Dockerfile              | Notes       |
|----------------|-----|------|-------------------------|-------------|
| **vStart**     | 1   | 4GB  | Dockerfile.vStart       | Entry-level |
| **vProfessional** | 2 | 8GB  | Dockerfile.vProfessional| Medium      |
| **vPopular**   | 4   | 16GB | Dockerfile.vPopular     | Popular     |
| **vStable**    | 8   | 32GB | Dockerfile.vStable      | High-end    |

---

## 🛠️ Container Build Example

**Dockerfile.vStart**
```Dockerfile
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y \
    nginx mysql-server php php-fpm php-mysql php-cli php-curl php-zip \
    php-gd php-mbstring php-xml php-bcmath unzip curl sudo supervisor \
    openssh-server && \
    apt clean && rm -rf /var/lib/apt/lists/*
RUN mkdir /var/run/sshd
COPY supervisord.conf /etc/supervisor/conf.d/supervisor.conf
COPY setup_user.sh /usr/local/bin/setup_user.sh
RUN chmod +x /usr/local/bin/setup_user.sh
RUN echo "root:youstable@123" | chpasswd
EXPOSE 22 80 443 3306
```
- **setup_user.sh:** Dynamically creates users.
- **supervisord.conf:** Ensures services auto-start.

---

## 🐍 Python Automation & Scripts

- **create_container.py:**  
  Accepts plan, domain, container name, username, and password.
  - Builds Docker image if absent.
  - Creates persistent volumes for website files and MySQL data.
  - Runs containers with CPU/memory limits and assigns a **random SSH port**.
  - Outputs credentials and endpoints for users.

- **monitor.py:**  
  Monitors container health, resource usage, and service status using Python.

- **package.py:**  
  Installs additional packages inside containers using their name and URL.

- **backup.sh:**  
  Backs up web files and databases.

### **Docker Run Template**
```bash
docker volume create {cname}_mysql_data
docker run -d \
  --name {cname} \
  --hostname {domain} \
  --cpus="{CPU}" \
  --memory="{RAM}" \
  -p {public_ip}:80:80 \
  -p {public_ip}:443:443 \
  -p {public_ip}:{ssh_port}:22 \
  -v /srv/{cname}/www:/home/{username}/www \
  -v {cname}_mysql_data:/var/lib/mysql \
  -e USERNAME={username} \
  -e PASSWORD={password} \
  hosting:{plan}
```

---

## 🌐 Nginx DNS & Reverse Proxy

- **DNS Management:** Automated updates map domains to the correct container endpoints.
- **Reverse Proxy:** Nginx routes incoming traffic to the correct container and port, supporting random port assignment.

---

## 🗄️ Backup Strategy

- **Web Files:**  
  `tar -czvf /backups/{cname}_www.tar.gz /srv/{cname}/www`
- **Databases:**  
  `docker exec {cname} /usr/bin/mysqldump -u root -p'youstable@123' --all-databases > /backups/{cname}_db.sql`
- **Volumes:**  
  `docker run --rm -v {cname}_mysql_data:/volume -v /backups:/backup alpine sh -c "cd /volume && tar czf /backup/{cname}_mysql_data.tar.gz ."`

---

## 🚧 Future Roadmap

### 1️⃣ AI Auto-Healing
- Integrate AI for real-time health checks and automatic recovery actions.

### 2️⃣ n8n + Slack + Python Alert System
- Event-driven alerts via n8n, Slack notifications, and Python-powered custom actions.

### 3️⃣ Custom Auto-Scaling (Option 2)
- Build your own auto-scaling with Docker API and metrics (no Traefik required!).
- **Architecture:**
  - Docker Engine/Swarm
  - Metrics Collector (Prometheus + cAdvisor)
  - Scaling Controller (Python/Go/Node.js)
  - Optional: HAProxy/Nginx/Redis/SQLite

**Scaling Flow:**
> Metrics → Controller → Docker API (create/start/delete container) → Update registry/load balancer → Repeat!

---

## 🤝 Contributing

We welcome pull requests and ideas. Please open issues for features, bugs, or suggestions!

---

## 💬 Contact

Questions or feedback?  
Open a GitHub Issue or chat with us via Slack!
