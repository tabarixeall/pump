import os
import sys
import subprocess

SERVICES = {
    "viking": {"name": "viking", "path": "/root/viking-bot", "script": "main.py"},
    "viking-bot": {
        "name": "viking-bot",
        "path": "/root/viking-bot",
        "script": "app.py",
    },
}


def print_header():
    print("========================================")
    print("Viking Services Manager")
    print("========================================")


def run_command(command, check=True):
    try:
        subprocess.run(command, check=check, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return False


def install_requirements(service_path):
    requirements_file = os.path.join(service_path, "requirements.txt")
    venv_path = os.path.join(service_path, "venv")
    python_bin = os.path.join(venv_path, "bin", "python")
    pip_bin = os.path.join(venv_path, "bin", "pip")

    # Create virtual environment if it doesn't exist
    if not os.path.exists(venv_path):
        print("Creating virtual environment...")
        if not run_command(["python3", "-m", "venv", venv_path]):
            return False

    # Upgrade pip
    print("Upgrading pip in virtual environment...")
    if not run_command([pip_bin, "install", "--upgrade", "pip"]):
        return False

    # Install requirements
    if os.path.exists(requirements_file):
        print("Installing requirements in virtual environment...")
        return run_command([pip_bin, "install", "-r", requirements_file])
    
    return True


def setup_service(service_key):
    service = SERVICES[service_key]
    if not os.path.exists(service["path"]):
        try:
            os.makedirs(service["path"], exist_ok=True)
            print(f"Created directory: {service['path']}")
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False

    venv_python = os.path.join(service["path"], "venv", "bin", "python")

    steps = [
        ("Installing requirements", lambda: install_requirements(service["path"])),
        (
            "Starting with pm2",
            lambda: run_command(
                [
                    "pm2",
                    "start",
                    os.path.join(service["path"], service["script"]),
                    "--name",
                    service["name"],
                    "--cwd",
                    service["path"],
                    "--interpreter",
                    venv_python,
                ]
            ),
        ),
    ]
    for step_name, step_func in steps:
        print(f"\nExecuting: {step_name}")
        if not step_func():
            print(f"Failed at: {step_name}")
            return False
    run_command(["pm2", "save"])
    return True


def undo_service(service_key):
    service = SERVICES[service_key]
    steps = [
        (
            "Stopping with pm2",
            lambda: run_command(["pm2", "stop", service["name"]], check=False),
        ),
        (
            "Deleting with pm2",
            lambda: run_command(["pm2", "delete", service["name"]], check=False),
        ),
    ]
    for step_name, step_func in steps:
        print(f"\nExecuting: {step_name}")
        step_func()
    run_command(["pm2", "save"])
    return True


def reload_services():
    names = [SERVICES[k]["name"] for k in SERVICES]
    for name in names:
        print(f"\nReloading {name} with pm2")
        run_command(["pm2", "reload", name])
    run_command(["pm2", "save"])
    return True


def restart_service(service_key):
    service = SERVICES[service_key]
    print(f"\nRestarting {service['name']} with pm2")
    run_command(["pm2", "restart", service["name"]])
    run_command(["pm2", "save"])
    return True


def main():
    if os.geteuid() != 0:
        print("This script must be run with sudo privileges.")
        print("Please run: sudo python3 setup_aio.py")
        sys.exit(1)
    print_header()
    while True:
        print(
            """
========================================
sudo pm2 logs viking
sudo pm2 logs viking-bot
----------------------------------------
              
        """
        )
        print("\nPlease select an option:")
        print("1. Setup Bot Service")
        print("2. Setup Bot API Service")
        print("3. Remove Bot Service")
        print("4. Remove API Service")
        print("5. Reload Both Services")
        print("6. Restart Bot Service")
        print("7. Restart API Service")
        print("8. Exit")
        choice = input("\nEnter your choice (1-8): ").strip()
        if choice == "1":
            if setup_service("viking"):
                print("\nViking Service setup completed successfully!")
                print("To check logs use: pm2 logs viking")
            break
        elif choice == "2":
            if setup_service("viking-bot"):
                print("\nViking Bot Service setup completed successfully!")
                print("To check logs use: pm2 logs viking-bot")
            break
        elif choice == "3":
            if undo_service("viking"):
                print("\nViking Service removal completed successfully!")
        elif choice == "4":
            if undo_service("viking-bot"):
                print("\nViking Bot Service removal completed successfully!")
            break
        elif choice == "5":
            if reload_services():
                print("\nBoth services reloaded successfully!")
            break
        elif choice == "6":
            if restart_service("viking"):
                print("\nViking Service restarted successfully!")
            break
        elif choice == "7":
            if restart_service("viking-bot"):
                print("\nViking Bot Service restarted successfully!")
            break
        elif choice == "8":
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    main()
