#!/usr/bin/env python3
"""
SERVER AND CONTAINER MONITORING SCRIPT
- Monitors server and container resource usage.
- Displays container ports and inactive containers in a table.
- Requires: root permissions, Linux, docker, psutil, tabulate.
"""

import os
import time
import socket
import psutil
import docker
import logging
import pandas as pd

# =======================
# Logging configuration
# =======================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =======================
# Docker client setup
# =======================
try:
    docker_client = docker.from_env()
except Exception as e:
    logging.warning(f"Could not initialize Docker client: {e}")
    docker_client = None

# =======================
# Helper functions
# =======================

def collect_container_stats(all_containers=False):
    """
    Collect detailed stats and metadata for all (or running) Docker containers.
    Returns a list of dictionaries, each with container details and resource usage.
    """
    containers_details = []
    if not docker_client:
        logging.info("Docker client not initialized. Skipping container stats collection.")
        return containers_details
    containers = docker_client.containers.list(all=all_containers)
    for c in containers:
        try:
            if c.status == 'running':
                stats = c.stats(stream=False)
                 # Calculate CPU %
                cpu_percent = 0.0
                cpu_stats = stats.get("cpu_stats", {})
                precpu_stats = stats.get("precpu_stats", {})
                if cpu_stats and precpu_stats:
                    cpu_delta = cpu_stats["cpu_usage"]["total_usage"] - precpu_stats["cpu_usage"]["total_usage"]
                    system_cpu_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
                    online_cpus = cpu_stats.get("online_cpus") or len(cpu_stats["cpu_usage"].get("percpu_usage", [])) or 1
                    if system_cpu_delta > 0 and online_cpus > 0:
                        cpu_percent = (cpu_delta / system_cpu_delta) * online_cpus * 100
                mem_usage = stats.get("memory_stats", {}).get("usage", 0)
                mem_limit = stats.get("memory_stats", {}).get("limit", 1)
                mem_percent = (mem_usage / mem_limit) * 100 if mem_limit else 0
            else:
                # For non-running containers, set resource usage to 0
                cpu_percent = 0.0
                mem_percent = 0.0
                mem_usage = 0
                mem_limit = 0


            # Container metadata
            ports = []
            if c.attrs.get("NetworkSettings", {}).get("Ports"):
                for port_name, port_binding in c.attrs["NetworkSettings"]["Ports"].items():
                    if port_binding:
                        try:
                            host_port = int(port_binding[0]["HostPort"])
                            ports.append(f"{port_name}->{host_port}")
                        except Exception:
                            pass # Silently ignore invalid port bindings
            else:
                ports.append("N/A")


            containers_details.append({
                "container_id": c.id[:12],
                "container_name": c.name,
                "status": c.status,
                "container_cpu_%": round(cpu_percent, 2),
                "container_mem_%": round(mem_percent, 2),
                "container_mem_usage_bytes": mem_usage,
                "container_mem_limit_bytes": mem_limit,
                "ports": ", ".join(ports),

            })
        except Exception as e:
            logging.error(f"Error collecting stats for container {c.id[:12]}: {e}")
    return containers_details

# =======================
# Main execution logic
# =======================

if __name__ == "__main__":
    try:
        print("="*30)
        print("=== SERVER AND CONTAINER MONITORING ===")
        print("="*30)

        # System Stats
        sys_cpu = psutil.cpu_percent(interval=1) # Interval for CPU percentage over 1 second
        sys_mem = psutil.virtual_memory().percent
        sys_disk = psutil.disk_usage('/').percent
        sys_net_io = psutil.net_io_counters()
        hostname = os.getenv("HOSTNAME", socket.gethostname())

        print(f"\nServer: {hostname}")
        print(f"  CPU Usage: {sys_cpu}%")
        print(f"  Memory Usage: {sys_mem}%")
        print(f"  Disk Usage ('/'): {sys_disk}%")
        print(f"  Network Sent: {sys_net_io.bytes_sent} bytes")
        print(f"  Network Received: {sys_net_io.bytes_recv} bytes")

        # Container Stats (including inactive)
        print("\nContainer Status and Usage:")
        container_data = collect_container_stats(all_containers=True)
        if container_data:
            df_containers = pd.DataFrame(container_data)
            print(df_containers.to_markdown(index=False))
        else:
            print("No Docker containers found or Docker client not initialized.")


    except Exception as e:
        logging.exception(f"Unexpected error during monitoring: {e}")
        print(f"Unexpected error during monitoring: {e}")
