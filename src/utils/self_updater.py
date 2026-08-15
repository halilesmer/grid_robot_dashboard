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


def check_for_updates(branch="test"):
    """
    Yerel (local) depo ile GitHub (origin) deposu arasındaki Git commit hash'lerini
    karşılaştırarak yeni bir güncelleme olup olmadığını %100 doğrulukla test eder.
    """
    try:
        # Önce GitHub'daki son bilgileri fetch ile çek (dosyaları değiştirmez, sadece bilgi alır)
        subprocess.run(
            ["git", "fetch", "origin", branch],
            check=True,
            capture_output=True,
            text=True,
        )

        # Yerel commit kimliği (hash)
        local_hash = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()

        # GitHub commit kimliği (hash)
        remote_hash = subprocess.run(
            ["git", "rev-parse", f"origin/{branch}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # Eğer hash'ler farklıysa yeni bir kod/güncelleme var demektir
        has_update = local_hash != remote_hash

        # Sürüm numaralarını (VERSION) arayüze göstermek için oku
        try:
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../..")
            )
            version_file = os.path.join(project_root, "VERSION")
            with open(version_file, "r", encoding="utf-8") as f:
                local_ver = f.read().strip()
        except Exception:
            local_ver = "v1.0.0"

        try:
            remote_ver = subprocess.run(
                ["git", "show", f"origin/{branch}:VERSION"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except Exception:
            remote_ver = "Bilinmiyor"

        return True, (has_update, local_ver, remote_ver)
    except Exception as e:
        return False, str(e)
