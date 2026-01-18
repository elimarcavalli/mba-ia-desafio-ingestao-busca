import os
import sys
import subprocess
import time
from pathlib import Path

# Configuration
VENV_DIR = Path("venv")
REQUIREMENTS_FILE = Path("requirements.txt")
DOCKER_COMPOSE_FILE = Path("docker-compose.yml")
APP_PATH = Path("src/presentation/web/chainlit_app.py")
CHAINLIT_PORT = 8000

COLORS = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
}

def print_color(text, color):
    print(f"{COLORS.get(color, '')}{text}{COLORS['ENDC']}")

def run_command(command, check=True, capture_output=False):
    """Run a shell command."""
    try:
        result = subprocess.run(
            command,
            check=check,
            shell=True,
            text=True,
            capture_output=capture_output
        )
        return result
    except subprocess.CalledProcessError as e:
        print_color(f"Error executing command: {command}", "FAIL")
        if e.stdout: print(f"Stdout: {e.stdout}")
        if e.stderr: print(f"Stderr: {e.stderr}")
        sys.exit(1)

def get_venv_python():
    """Get the path to the python executable in the venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def get_venv_pip():
    """Get the path to the pip executable in the venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def get_venv_chainlit():
    """Get the path to the chainlit executable in the venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "chainlit.exe"
    return VENV_DIR / "bin" / "chainlit"

def step_1_create_venv():
    print_color("\n[1/4] Checking Virtual Environment...", "HEADER")
    if not VENV_DIR.exists():
        print_color("Creating virtual environment...", "BLUE")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        print_color("Virtual environment created successfully!", "GREEN")
    else:
        print_color("Virtual environment already exists.", "GREEN")

def step_2_install_requirements():
    print_color("\n[2/4] Installing/Updating Components...", "HEADER")
    pip_cmd = get_venv_pip()
    
    if not REQUIREMENTS_FILE.exists():
        print_color("requirements.txt not found!", "FAIL")
        sys.exit(1)

    print_color("Installing requirements (this may take a moment)...", "BLUE")
    # Upgrade pip first
    run_command(f'"{pip_cmd}" install --upgrade pip', check=False)
    # Install reqs
    run_command(f'"{pip_cmd}" install -r "{REQUIREMENTS_FILE}"')
    print_color("Dependencies installed successfully!", "GREEN")

def step_3_docker_compose():
    print_color("\n[3/4] Starting Infrastructure (Docker)...", "HEADER")
    if not DOCKER_COMPOSE_FILE.exists():
        print_color("docker-compose.yml not found!", "FAIL")
        sys.exit(1)

    print_color("Checking Docker status...", "BLUE")
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_color("Docker is not running or not installed. Please start Docker Desktop.", "FAIL")
        sys.exit(1)

    print_color("Starting services with Docker Compose...", "BLUE")
    run_command("docker compose up -d")
    print_color("Infrastructure started!", "GREEN")

def step_4_run_app():
    print_color("\n[4/4] Launching Application...", "HEADER")
    chainlit_cmd = get_venv_chainlit()
    
    if not APP_PATH.exists():
        print_color(f"Application file {APP_PATH} not found!", "FAIL")
        sys.exit(1)

    print_color(f"Starting Chainlit server on port {CHAINLIT_PORT}...", "GREEN")
    print_color("Press Ctrl+C to stop the server.", "WARNING")
    
    try:
        # We replace the current process with the chainlit process
        # This keeps the interactive shell alive for the logs
        if sys.platform == "win32":
            subprocess.run([str(chainlit_cmd), "run", str(APP_PATH), "-w", "--port", str(CHAINLIT_PORT)])
        else:
            os.execv(str(chainlit_cmd), [str(chainlit_cmd), "run", str(APP_PATH), "-w", "--port", str(CHAINLIT_PORT)])
    except KeyboardInterrupt:
        print_color("\nServer stopped by user.", "WARNING")

def main():
    print_color("=== MBA Software Engineering with AI - Project Launcher ===", "HEADER")
    
    try:
        step_1_create_venv()
        step_2_install_requirements()
        step_3_docker_compose()
        step_4_run_app()
    except KeyboardInterrupt:
        print_color("\nSetup aborted by user.", "FAIL")
    except Exception as e:
        print_color(f"\nAn unexpected error occurred: {e}", "FAIL")

if __name__ == "__main__":
    main()
