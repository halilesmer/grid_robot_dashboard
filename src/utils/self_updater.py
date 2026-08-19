import subprocess
import os
import sys


def get_project_root():
    """Projenin ana klasör yolunu güvenli bir şekilde döndürür."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def ensure_git_repo(branch, project_root):
    """
    Gizli .git klasörünü kontrol eder. Eğer yoksa (klasör taşınmış veya ZIP'ten
    çıkarılmışsa), github_token.txt dosyasını okuyarak Git'i sıfırdan otonom olarak inşa eder.
    """
    git_dir = os.path.join(project_root, ".git")
    if os.path.isdir(git_dir):
        return True, ""

    # Git klasörü yok, kendi kendini onarma (Self-Healing) sürecini başlat
    token_file = os.path.join(project_root, "github_token.txt")
    if not os.path.exists(token_file):
        return (
            False,
            "Klasör Git'e bağlı değil ve 'github_token.txt' dosyası bulunamadı. Lütfen repo URL'nizi (Token dahil) içeren bu dosyayı ana klasöre oluşturun.",
        )

    try:
        with open(token_file, "r", encoding="utf-8") as f:
            repo_url = f.read().strip()

        if not repo_url.startswith("http"):
            return (
                False,
                "github_token.txt içindeki URL geçersiz. 'https://...' ile başlamalı.",
            )

        # 1. Klasörü Git deposu yap
        subprocess.run(
            ["git", "init"], cwd=project_root, check=True, capture_output=True
        )

        # 2. Uzak sunucuyu (GitHub) Token ile birlikte ekle
        subprocess.run(
            ["git", "remote", "add", "origin", repo_url],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        # 3. Sunucudaki verileri çek
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        # 4. Dosyaları sunucudaki branch ile zorla eşitle
        subprocess.run(
            ["git", "reset", "--hard", f"origin/{branch}"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        # 5. Aktif dalı ayarla
        subprocess.run(
            ["git", "branch", "-M", branch],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        return True, "Git deposu başarıyla onarıldı ve eşitlendi."
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else e.stdout
        return False, f"Otomatik Git onarımı başarısız oldu: {error_msg}"
    except Exception as e:
        return False, f"Beklenmeyen onarım hatası: {str(e)}"


def execute_git_pull(branch="master"):
    """
    Belirtilen branch üzerinden güvenli ve çakışmasız 'git pull' çalıştırır.
    """
    project_root = get_project_root()

    # 🌟 OTONOM KALKAN: Önce Git'in sağlam olup olmadığına bak, değilse onar
    is_git_ok, error_message = ensure_git_repo(branch, project_root)
    if not is_git_ok:
        return False, error_message

    try:
        # 1. Yerel dosya çakışmalarını ve satır sonu farklarını zorla temizle
        subprocess.run(
            ["git", "reset", "--hard"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )

        # 2. Önce fetch yapalım
        subprocess.run(
            ["git", "fetch", "origin", branch],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )

        # 3. Sonra ilgili branch'e çekelim
        result = subprocess.run(
            ["git", "pull", "origin", branch],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else e.stdout
        return False, f"Git Kodu: {e.returncode} | Hata: {error_msg}"


def hard_restart_server():
    project_root = get_project_root()
    launcher_script = os.path.join(project_root, "scripts", "launcher.py")
    os.execl(sys.executable, sys.executable, launcher_script)


def check_for_updates(branch="test"):
    """
    Yerel (local) depo ile GitHub (origin) deposu arasındaki Git commit hash'lerini
    karşılaştırarak yeni bir güncelleme olup olmadığını %100 doğrulukla test eder.
    """
    project_root = get_project_root()

    # 🌟 OTONOM KALKAN: Önce Git'in sağlam olup olmadığına bak, değilse onar
    is_git_ok, error_message = ensure_git_repo(branch, project_root)
    if not is_git_ok:
        return False, error_message

    try:
        # Önce GitHub'daki son bilgileri fetch ile çek (dosyaları değiştirmez, sadece bilgi alır)
        subprocess.run(
            ["git", "fetch", "origin", branch],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )

        # Yerel commit kimliği (hash)
        local_hash = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # GitHub commit kimliği (hash)
        remote_hash = subprocess.run(
            ["git", "rev-parse", f"origin/{branch}"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # Eğer hash'ler farklıysa yeni bir kod/güncelleme var demektir
        has_update = local_hash != remote_hash

        # Sürüm numaralarını (VERSION) arayüze göstermek için oku
        try:
            version_file = os.path.join(project_root, "VERSION")
            with open(version_file, "r", encoding="utf-8") as f:
                local_ver = f.read().strip()
        except Exception:
            local_ver = "v1.0.0"

        try:
            remote_ver = subprocess.run(
                ["git", "show", f"origin/{branch}:VERSION"],
                cwd=project_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except Exception:
            remote_ver = "Bilinmiyor"

        return True, (has_update, local_ver, remote_ver)
    except Exception as e:
        return False, str(e)
