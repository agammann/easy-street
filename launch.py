"""First-run setup and local launcher for the downloadable Easy Street app."""
import argparse
import hashlib
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent


def environment_python():
    return ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def setup():
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Easy Street requires Python 3.12. Install it from python.org, then run this launcher again.")
    if not (ROOT / "frontend" / "dist" / "index.html").is_file():
        raise SystemExit("This source checkout needs a frontend build. Follow README.md, or download the ready-to-run release ZIP.")
    python = environment_python()
    if not python.is_file():
        print("Preparing Easy Street's private Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(ROOT / ".venv")
    lock = ROOT / "backend" / "requirements-lock.txt"
    fingerprint = hashlib.sha256(lock.read_bytes()).hexdigest()
    marker = ROOT / ".venv" / ".easy-street-dependencies"
    if not marker.exists() or marker.read_text().strip() != fingerprint:
        print("Installing the pinned Python dependencies. This first run needs internet access.", flush=True)
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(lock)], check=True, cwd=ROOT)
        marker.write_text(fingerprint, encoding="utf-8")
    subprocess.run([str(python), "-c", "import fastapi, uvicorn, pypdf, openai"], check=True, cwd=ROOT)
    return python


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup-only", action="store_true", help="Install dependencies without starting the app")
    parser.add_argument("--configure", action="store_true", help="Set your own key and budget in a private terminal prompt")
    parser.add_argument("--no-browser", action="store_true", help="Start without opening a browser")
    args = parser.parse_args()
    python = setup()
    if args.configure:
        subprocess.run([str(python), str(ROOT / "configure.py")], check=True, cwd=ROOT)
        return
    if args.setup_only:
        print("Setup complete. Run launch.py again to open Easy Street.")
        return
    with socket.socket() as probe:
        probe.settimeout(3)
        if probe.connect_ex(("127.0.0.1", 8000)) == 0:
            raise SystemExit("Port 8000 is already in use. Stop the running server before starting another Easy Street instance.")
    print("Easy Street: http://127.0.0.1:8000\nKeep this terminal open. Press Ctrl+C to stop.", flush=True)
    process = subprocess.Popen([str(python), str(ROOT / "start.py")], cwd=ROOT)
    timer = None
    if not args.no_browser:
        def open_when_ready():
            import time
            from urllib.request import ProxyHandler, build_opener
            client = build_opener(ProxyHandler({}))
            for _ in range(40):
                if process.poll() is not None:
                    return
                try:
                    with client.open("http://127.0.0.1:8000/api/health", timeout=1) as response:
                        if response.status == 200:
                            webbrowser.open("http://127.0.0.1:8000")
                            return
                except OSError:
                    time.sleep(0.25)
        timer = threading.Thread(target=open_when_ready, daemon=True)
        timer.start()
    try:
        return_code = process.wait()
    except KeyboardInterrupt:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                process.terminate()
            process.wait(timeout=10)
        return_code = 0
    raise SystemExit(return_code)


if __name__ == "__main__":
    main()
