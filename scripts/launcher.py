# Dosya: scripts/launcher.py
import os
import sys
import socket
import subprocess
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


def ensure_venv_and_requirements():
    """Sanal ortam ve kütüphaneler eksikse otomatik kurar."""
    python_exe = sys.executable

    # 1. .venv var mı?
    if not VENV_DIR.exists():
        print("⚙️ .venv ortamı bulunamadı, oluşturuluyor...")
        subprocess.run([python_exe, "-m", "venv", str(VENV_DIR)], check=True)

    venv_python = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    # 2. Kütüphaneler yüklü mü? (Streamlit kontrolü)
    try:
        subprocess.run(
            [str(venv_python), "-c", "import streamlit"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("📦 Kütüphaneler yükleniyor (requirements.txt)...")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
            check=True,
        )

    return venv_python


def wait_for_server_and_open_browser(port, timeout=30):
    url = f"http://localhost:{port}"
    start_time = time.time()
    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", int(port))) == 0:
                time.sleep(0.5)
                webbrowser.open(url)
                return True
        time.sleep(0.5)
    webbrowser.open(url)
    return False


def main():
    venv_python = ensure_venv_and_requirements()

    # Portu çevre değişkeninden al (Statik PWA uyumluluğu için)
    port = os.getenv("STREAMLIT_PORT", "8501")

    # Tarayıcıyı sadece kullanıcı ilk tıkladığında aç (Güncellemelerde sekme spam'i yapmaz)
    open_browser = "--open-browser" in sys.argv

    print(f"🚀 Uygulama {port} portunda başlatılıyor...")

    cmd = [
        str(venv_python),
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]

    process = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))

    if open_browser:
        wait_for_server_and_open_browser(int(port))

    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()


if __name__ == "__main__":
    main()
