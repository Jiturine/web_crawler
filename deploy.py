import os
import sys
import shutil
import venv
import subprocess
from pathlib import Path

VENV_DIR = os.path.abspath(__file__).parent / "venv"  
SERVER_SOURCE = os.path.abspath(__file__).parent / "server"  

def create_venv():
    
    if VENV_DIR.exists():
        print(f"V-ENV EXISTS")
        return

    print(f"Creating V-ENV")
    venv.create(VENV_DIR, with_pip=True)
    print("V-ENV Created")

def copy_project():
    target_dir = VENV_DIR / "server"
    if target_dir.exists():
        print(f"Already deployed")
        return

    print(f"Mounting to V-ENV")
    try:
        shutil.copytree(
            SERVER_SOURCE,
            target_dir,
            ignore=shutil.ignore_patterns("__pycache__")
        )
    except Exception as e:
        print(f"Mounting Failed: {str(e)}")
        sys.exit(1)

def install_dependencies():
    pip_path = VENV_DIR / "bin" / "pip"
    req_file = VENV_DIR / "server" / "requirements.txt"

    if not req_file.exists():
        print(f"Requirements.txt missing")
        return

    print(f"Installing Dependencies")
    try:
        subprocess.run([str(pip_path), "install", "-r", str(req_file)], check=True)
        print("Dependencied Installed")
    except subprocess.CalledProcessError as e:
        print(f"Failed to Install Dependencies: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_venv()
    copy_project()
    install_dependencies()
    print("\nServer Deployed")
    print(f"Path to Server Directory: {VENV_DIR / 'server'}")
    print(f"Please read the README.md at{VENV_DIR / 'server'/'README.md'} for mysql configuration and other details.")