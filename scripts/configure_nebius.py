"""Masked local development-key setup; never display a key or use a browser form."""
from getpass import getpass, GetPassWarning
import os
from pathlib import Path
import re
import sys
import tempfile
import warnings

ROOT = Path(__file__).resolve().parents[1]


def save_key(key, target=None):
    target = target or ROOT/".env.local"
    if target.is_symlink():
        raise ValueError("Refusing a configuration symbolic link.")
    if not 12 <= len(key) <= 5000 or any(ord(ch) < 33 or ord(ch) > 126 or ch in "\"'\\#$" for ch in key):
        raise ValueError("Invalid key text. Nothing was saved.")
    previous = target.read_text(encoding="utf-8") if target.exists() else ""
    lines = [line for line in previous.splitlines() if not re.match(r"^\s*(?:export\s+)?NEBIUS_API_KEY\s*=",line)]
    descriptor, temporary = tempfile.mkstemp(prefix=".env-setup-",dir=target.parent)
    try:
        with os.fdopen(descriptor,"w",encoding="utf-8") as stream:
            stream.write("\n".join(lines+["NEBIUS_API_KEY="+key])+"\n")
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    if not sys.stdin.isatty():
        raise SystemExit("Open an interactive private terminal for masked key setup. Redirected input is disabled.")
    print("Local Nebius BYO development setup. Your key is hidden and saved only to this app's ignored .env.local.")
    print("Hosting uses its own runtime secret manager. No key is copied into a deployment or browser.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            key = getpass("Nebius API key (hidden; Enter cancels): ").strip()
    except GetPassWarning:
        raise SystemExit("Masked input is unavailable in this terminal. Nothing was saved.") from None
    if not key:
        print("No changes."); return
    save_key(key)
    print("Nebius key saved privately. No API request was made and no key was displayed.")


if __name__ == "__main__":
    main()
