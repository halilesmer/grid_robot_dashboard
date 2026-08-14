import subprocess
import os
import sys


def execute_git_pull(branch="master"):
    """
    Belirtilen branch üzerinden güvenli ve çakışmasız 'git pull' çalıştırır.
    """
    try:
        # 1. Yerel dosya çakışmalarını ve satır sonu farklarını zorla temizle
        subprocess.run(
            ["git", "reset", "--hard"], check=True, capture_output=True, text=True
        )

        # 2. Önce fetch yapalım
        subprocess.run(
            ["git", "fetch", "origin", branch],
            check=True,
            capture_output=True,
            text=True,
        )

        # 3. Sonra ilgili branch'e çekelim
        result = subprocess.run(
            ["git", "pull", "origin", branch],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else e.stdout
        return False, f"Git Kodu: {e.returncode} | Hata: {error_msg}"


def hard_restart_server():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    launcher_script = os.path.join(project_root, "scripts", "launcher.py")
    os.execl(sys.executable, sys.executable, launcher_script)
