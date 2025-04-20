import platform
import subprocess
from prompts import get_cmd_prompt  # uses the correct prompt for OS


def get_cmd(instruction):
    command, error = get_cmd_prompt(instruction)
    if command:
        print(f"Generated command: {command}")
        return command, None
    else:
        print(f"Error generating command: {error}")
        return None, error

def execute_cmd(command):
    try:
        # Auto-detect platform
        current_os = platform.system().lower()
        if current_os == "windows":
            shell_cmd = ['cmd', '/c', command]
        elif current_os in ["linux", "darwin"]:
            shell_cmd = ['bash', '-c', command]
        else:
            raise EnvironmentError(f"Unsupported OS: {current_os}")

        process = subprocess.run(
            shell_cmd,
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8',
            errors='replace'
        )

        if process.stdout:
            print("Output:")
            print(process.stdout)
        if process.stderr:
            print("Error Output:")
            print(process.stderr)
        print(f"\nCommand finished with exit code: {process.returncode}")

        success = process.returncode == 0
        error_msg = process.stderr.strip() if process.stderr else ""

        return success, error_msg

    except Exception as e:
        print(f"An exception occurred: {e}")
        return False, str(e)