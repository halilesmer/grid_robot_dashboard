import subprocess
import os
import sys


def execute_git_pull(branch="test"):
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

        result = subprocess.run(
            ["git", "pull", "origin", branch],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, f"Git Kodu: {result.returncode} | Hata: {result.stderr}"
    except Exception as e:
        return False, str(e)


def hard_restart_server():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    launcher_script = os.path.join(project_root, "scripts", "launcher.py")
    os.execl(sys.executable, sys.executable, launcher_script)
