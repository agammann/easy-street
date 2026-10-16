"""Verify a release ZIP installs without Node.js and passes the production smoke."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
import zipfile

try:
    from .smoke_startup import api, check, require_free_port, verify_assets, verify_no_usage
except ImportError:
    from smoke_startup import api, check, require_free_port, verify_assets, verify_no_usage


def stop_launcher(process):
    """Stop only the launcher we created and its descendants, then verify shutdown."""
    if os.name == "nt":
        if process.poll() is None:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW, check=True)
    else:
        # The launcher starts start.py, so terminating only the parent leaves the
        # server alive. Its new session gives this test its own process group.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=10)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            require_free_port()
            return
        except RuntimeError:
            time.sleep(0.1)
    raise RuntimeError("The release launcher did not release port 8000 after shutdown.")


def verify_launcher(root, environment):
    require_free_port()
    env = {**environment, "OPENAI_API_KEY":"", "EASY_STREET_BUDGET_USD":"0",
           "EASY_STREET_DATA_DIR":str(root / "launcher-data"),
           "PYTHON_DOTENV_DISABLED":"1", "PYTHONUNBUFFERED":"1"}
    options = ({"creationflags":subprocess.CREATE_NO_WINDOW} if os.name == "nt"
               else {"start_new_session":True})
    log_path = root / "launcher-smoke.log"
    with log_path.open("wb") as log:
        process = subprocess.Popen([sys.executable, "launch.py", "--no-browser"],
                                   cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, **options)
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                check(process.poll() is None, "The release launcher exited before the app became healthy.")
                try:
                    if api("/api/health") == {"status":"ok"}:
                        break
                except (URLError, TimeoutError, ConnectionError):
                    pass
                time.sleep(0.2)
            else:
                raise RuntimeError("The release launcher did not become healthy within 45 seconds.")
            verify_no_usage()
            check(api("/api/config")["budget"]["limit_usd"] == 0,
                  "The release launcher did not preserve the isolated zero-budget configuration.")
            verify_assets()
        except Exception:
            log.flush()
            print(log_path.read_text(errors="replace")[-6000:], file=sys.stderr)
            raise
        finally:
            stop_launcher(process)
    require_free_port()
    print("PASS: launch.py --no-browser served the built app without a key or budget, and stopped cleanly.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith(("OPENAI_", "EASY_STREET_"))}
    with tempfile.TemporaryDirectory(prefix="easy-street-release-") as directory:
        temporary = Path(directory)
        with zipfile.ZipFile(args.archive) as archive:
            if sum(info.file_size for info in archive.infolist()) > 100 * 1024 * 1024:
                raise SystemExit("Release ZIP exceeds the expected size bound.")
            for info in archive.infolist():
                target = (temporary / info.filename).resolve()
                if not target.is_relative_to(temporary.resolve()) or not info.filename.startswith("easy-street/"):
                    raise SystemExit("Release ZIP contains an unexpected path.")
                if any(part in (".env.local", ".env", ".venv", "node_modules", "data") for part in Path(info.filename).parts):
                    raise SystemExit("Release ZIP contains private runtime files.")
            archive.extractall(temporary)
        root = temporary / "easy-street"
        subprocess.run([sys.executable, "launch.py", "--setup-only"], cwd=root, env=env, check=True, timeout=300)
        verify_launcher(root,env)
        python = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "scripts/smoke_startup.py"], cwd=root, env=env, check=True, timeout=120)
    print("PASS: release ZIP installed with Python only; production workflow passed.")


if __name__ == "__main__":
    main()
