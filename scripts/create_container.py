#!/usr/bin/env python3
"""
create_container.py
===================
Creates a new Docker container from a plan-specific Dockerfile.
Features:
- Builds Docker image if not exists.
- Creates a Docker bridge network.
- Optionally creates a host dummy interface for subnet routing.
- Avoids container name conflicts.
"""

import os
import random
import subprocess


DOCKERFILES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dockerfiles")

PLANS = {
    "vStart": {"cpu": "1", "mem": "4g", "dockerfile": "Dockerfile.vStart"},
    "vProfessional": {"cpu": "2", "mem": "8g", "dockerfile": "Dockerfile.vProfessional"},
    "vPopular": {"cpu": "4", "mem": "16g", "dockerfile": "Dockerfile.vPopular"},
    "vStable": {"cpu": "8", "mem": "32g", "dockerfile": "Dockerfile.vStable"},
}


def random_port(start=20000, end=50000):
    """Generate a random port in the given range."""
    return random.randint(start, end)


def run_command(command):
    """ Helper to run a command and handle errors """
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip() # Return stripped stdout
    except subprocess.CalledCalledProcessError as e:
        print(f"Error occurred while running command: {command}")
        print(f"Exit Code: {e.returncode}")
        print(f"Error Output: {e.stderr}")
        raise  # Reraise the exception to stop execution


def build_image(plan):
    """Build Docker image if it doesn't exist."""
    image_tag = f"hosting:{plan.lower()}"
    dockerfile_path = os.path.join(DOCKERFILES_DIR, PLANS[plan]["dockerfile"])
    print(f"Building Docker image {image_tag} from {dockerfile_path} ...")
    run_command(f"docker build -t {image_tag} -f {dockerfile_path} {DOCKERFILES_DIR}")
    return image_tag


def create_host_interface(subnet_cidr, interface_name="docknet0"):
    """Creates a host dummy interface with the subnet gateway IP."""
    try:
        base_ip = subnet_cidr.split("/")[0].rsplit(".", 1)[0]
        gateway_ip = f"{base_ip}.1/28"

        # Check if interface exists
        result = subprocess.run(f"ip addr show {interface_name}", shell=True)
        if result.returncode != 0:
            print(f"Creating host interface {interface_name} with IP {gateway_ip} ...")
            run_command(f"sudo ip link add {interface_name} type dummy")
            run_command(f"sudo ip addr add {gateway_ip} dev {interface_name}")
            run_command(f"sudo ip link set {interface_name} up")
        else:
            print(f"Interface {interface_name} already exists.")
    except Exception as e:
        print(f"Error in creating host interface: {e}")
        raise


def create_docker_network(network_name, subnet_cidr=None):
    """Creates a Docker bridge network. Subnet is optional."""
    try:
        existing = subprocess.run(f"docker network ls --filter name=^{network_name}$ -q", shell=True, capture_output=True, text=True).stdout.strip()
        if not existing:
            print(f"Creating Docker network '{network_name}' ...")
            cmd = f"docker network create --driver=bridge {network_name}"
            if subnet_cidr:
                 cmd = f"docker network create --driver=bridge --subnet={subnet_cidr} {network_name}"
                 create_host_interface(subnet_cidr) # Create host interface if subnet is specified
            run_command(cmd)
        else:
            print(f"Docker network {network_name} already exists.")
    except Exception as e:
        print(f"Error in creating Docker network: {e}")
        raise


def remove_existing_container(name):
    """Remove existing container if exists."""
    try:
        existing = subprocess.run(f"docker ps -a --filter name=^{name}$ -q", shell=True, capture_output=True, text=True).stdout.strip()
        if existing:
            print(f"Removing existing container '{name}' ...")
            run_command(f"docker rm -f {name}")
        else:
            print(f"No existing container named {name} found.")
    except Exception as e:
        print(f"Error in removing existing container: {e}")
        raise


def create_container():
    try:
        print("=== Hosting Container Creation ===")
        plan = input("Plan (vStart/vProfessional/vPopular/vStable): ").strip()
        domain = input("Client Domain Name: ").strip()
        cname = input("Container Name (no spaces): ").strip()

        # Container OS user
        username = input("Container Username: ").strip()
        password = input("Container Password: ").strip()

        # Database credentials
        db_admin_user = input("Database Admin Username: ").strip()
        db_admin_pass = input("Database Admin Password: ").strip()
        db_user = input("Database Username: ").strip()
        db_pass = input("Database Password: ").strip()

        # Docker network details
        # Removed prompt for container_ip
        subnet = input("Optional: Docker subnet for containers (e.g., 45.59.132.208/28), leave empty for default bridge: ").strip()
        network_name = input("Docker network name (e.g., hosting_net): ").strip()


        if plan not in PLANS:
            print("Invalid plan. Please choose from vStart, vProfessional, vPopular, or vStable.")
            return

        # Build Docker image
        image_tag = build_image(plan)

        # Prepare website directory
        web_dir = f"/srv/{cname}/www"
        os.makedirs(web_dir, exist_ok=True)

        # Create Docker network (with optional subnet)
        create_docker_network(network_name, subnet if subnet else None)

        # Remove container if exists
        remove_existing_container(cname)

        # Generate random ports
        http_port = random_port(20000, 30000)
        https_port = random_port(30001, 40000)
        ssh_port = random_port(40001, 50000)
        mysql_port = random_port(50001, 60000)

        print(f"\nRunning container {cname} for domain {domain} ...")

        # Updated docker command without --ip flag
        docker_cmd = (
            f"docker run -d "
            f"--name {cname} "
            f"--hostname {domain} "
            f"--cpus=\"{PLANS[plan]['cpu']}\" "
            f"--memory=\"{PLANS[plan]['mem']}\" "
            f"--net {network_name} "
            f"-v {web_dir}:/home/{username}/www "
            f"-e USERNAME={username} "
            f"-e PASSWORD={password} "
            f"-e DB_ADMIN_USER={db_admin_user} "
            f"-e DB_ADMIN_PASS={db_admin_pass} "
            f"-e DB_USER={db_user} "
            f"-e DB_PASS={db_pass} "
            f"-p {http_port}:80 "
            f"-p {https_port}:443 "
            f"-p {ssh_port}:22 "
            f"-p {mysql_port}:3306 "
            f"{image_tag}"
        )

        # Capture container ID from the output of the docker run command
        container_id = run_command(docker_cmd)

        print(f"""
        Container Created Successfully!

        Container ID: {container_id}
        Domain: {domain}
        Plan: {plan}
        Container Name: {cname}
        Docker Network: {network_name}
        # Removed Container IP from the success message


        Username: {username}
        Password: {password}

        Database Admin Username: {db_admin_user}
        Database Admin Password: {db_admin_pass}
        Database Username: {db_user}
        Database Password: {db_pass}

        Website Directory: {web_dir}

        Ports (Accessible on Server IP):
          HTTP: {http_port}
          HTTPS: {https_port}
          SSH: {ssh_port}
          MySQL: {mysql_port}
        """)
    except Exception as e:
        print(f"Error: {e}")
        print("Please review the error message above to understand the issue and try again.")


if __name__ == "__main__":
    create_container()
