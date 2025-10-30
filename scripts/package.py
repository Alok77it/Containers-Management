import subprocess
import sys
import time

def run_in_container(container_id, command):
    """
    Run a command inside a Docker container and return the output.
    Includes basic error handling and progress indication.
    """
    try:
        process = subprocess.Popen(
            ['docker', 'exec', container_id] + command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        return stdout, stderr, process.returncode
    except Exception as e:
        return str(e), None, 1 # Return an error code

def install_package(container_id, package_name):
    """
    Install a package inside the container by package name.
    Includes progress bar, checks if package is already installed, and suggests alternatives.
    """
    print(f"Checking if {package_name} is already installed...")
    check_command = ['dpkg', '-s', package_name]
    stdout, stderr, returncode = run_in_container(container_id, check_command)

    if returncode == 0:
        print(f"Package {package_name} is already installed.")
        return

    print(f"Updating package lists for {container_id}...")
    command_update = ['apt-get', 'update']
    stdout, stderr, returncode = run_in_container(container_id, command_update)
    if returncode != 0:
        print(f"Error updating package lists: {stderr}")
        return

    print(f"Installing package {package_name} in {container_id}...")
    command_install = ['apt-get', 'install', '-y', package_name]
    process = subprocess.Popen(
        ['docker', 'exec', container_id] + command_install,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Simple progress indication
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            sys.stdout.write(output)
            sys.stdout.flush()

    stdout, stderr = process.communicate()
    returncode = process.returncode

    if returncode != 0:
        print(f"Error installing package {package_name}: {stderr}")
        # Suggest alternatives if package not found (basic check)
        if "Unable to locate package" in stderr or "Package '" in stderr and "' has no installation candidate" in stderr:
             print(f"Package '{package_name}' not found. Did you mean?")
             search_command = ['apt-cache', 'search', package_name]
             stdout, stderr, returncode = run_in_container(container_id, search_command)
             if returncode == 0:
                 print(stdout)
             else:
                 print("Could not search for similar packages.")
    else:
        print(f"Package {package_name} installed successfully!")

def install_package_from_url(container_id, package_url):
    """
    Install a package inside the container from a URL (assumed .deb file).
    Includes progress bar for download and installation.
    """
    print(f"Downloading package from URL {package_url} to {container_id}...")
    command_download = ['wget', '--quiet', '--show-progress', package_url, '-O', '/tmp/package.deb']

    process_download = subprocess.Popen(
        ['docker', 'exec', container_id] + command_download,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Simple progress indication for download
    while True:
        output = process_download.stderr.readline() # wget often prints progress to stderr
        if output == '' and process_download.poll() is not None:
            break
        if output:
            sys.stderr.write(output)
            sys.stderr.flush()


    stdout_download, stderr_download = process_download.communicate()
    returncode_download = process_download.returncode

    if returncode_download != 0:
        print(f"Error downloading package from URL {package_url}: {stderr_download}")
        return

    print(f"Installing package from /tmp/package.deb in {container_id}...")
    # Correcting the command to use separate calls or a single command string with shell=True
    command_install = ['/bin/bash', '-c', 'dpkg -i /tmp/package.deb && apt-get install -f -y']


    process_install = subprocess.Popen(
        ['docker', 'exec', container_id] + command_install,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Simple progress indication for installation
    while True:
        output = process_install.stdout.readline()
        if output == '' and process_install.poll() is not None:
            break
        if output:
            sys.stdout.write(output)
            sys.stdout.flush()

    stdout_install, stderr_install = process_install.communicate()
    returncode_install = process_install.returncode


    if returncode_install != 0:
        print(f"Error installing package from URL {package_url}: {stderr_install}")
    else:
        print(f"Package installed from URL: {package_url}")

def download_file(container_id, file_url, container_path):
    """
    Download a file from a URL and save it to the specified container path.
    Includes progress bar for download.
    """
    print(f"Downloading file from {file_url} to {container_id}:{container_path}...")
    # Use wget with quiet mode and show progress
    command_download = ['wget', '--quiet', '--show-progress', file_url, '-P', container_path]

    process_download = subprocess.Popen(
        ['docker', 'exec', container_id] + command_download,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Simple progress indication for download
    while True:
        output = process_download.stderr.readline() # wget often prints progress to stderr
        if output == '' and process_download.poll() is not None:
            break
        if output:
            sys.stderr.write(output)
            sys.stderr.flush()

    stdout_download, stderr_download = process_download.communicate()
    returncode_download = process_download.returncode

    if returncode_download != 0:
        print(f"Error downloading file from {file_url}: {stderr_download}")
    else:
        print(f"File downloaded successfully to {container_path}")


def main():
    # Get container ID from user
    container_id = input("Enter the container ID: ")

    while True:
        print("\nSelect an option:")
        print("1. Install package by name")
        print("2. Install package from URL (e.g., .deb file)")
        print("3. Download file from URL")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            package_name = input("Enter the package name to install: ")
            install_package(container_id, package_name)

        elif choice == '2':
            package_url = input("Enter the URL of the package (.deb file): ")
            confirm = input(f"Do you want to install the package from {package_url}? (yes/no): ").lower()
            if confirm == 'yes':
                install_package_from_url(container_id, package_url)
            else:
                print("Package installation cancelled.")

        elif choice == '3':
            file_url = input("Enter the URL of the file to download: ")
            container_path = input("Enter the path inside the container to save the file: ")
            confirm = input(f"Do you want to download the file from {file_url} to {container_path}? (yes/no): ").lower()
            if confirm == 'yes':
                download_file(container_id, file_url, container_path)
            else:
                print("File download cancelled.")


        elif choice == '4':
            print("Exiting...")
            break

        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
