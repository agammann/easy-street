"""Generate private judge-access environment values without printing credentials."""
from getpass import getpass, GetPassWarning
import os
from pathlib import Path
import secrets
import sys
import tempfile
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.judging import password_hash


def main():
    if not sys.stdin.isatty():
        raise SystemExit("Use an interactive private terminal. Redirected credential input is disabled.")
    target = ROOT/"deploy/.env.judging.local"
    if target.exists() or target.is_symlink():
        raise SystemExit("Private judge configuration already exists. Review it in your trusted local editor before changing it.")
    print("Create a private judge access code. It must be shared only in private testing instructions.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            password = getpass("Judge access code (hidden, at least 12 characters): ")
            confirmed = getpass("Confirm access code (hidden): ")
    except GetPassWarning:
        raise SystemExit("Masked input is unavailable in this terminal. Nothing was saved.") from None
    if password != confirmed:
        raise SystemExit("Access codes differ. Nothing was saved.")
    encoded = password_hash(password)
    descriptor, temporary = tempfile.mkstemp(prefix=".env-setup-",dir=target.parent)
    try:
        with os.fdopen(descriptor,"w",encoding="utf-8") as stream:
            stream.write("EASY_STREET_JUDGE_PASSWORD_HASH='"+encoded+"'\n")
            stream.write("EASY_STREET_OPERATOR_TOKEN="+secrets.token_urlsafe(40)+"\n")
            stream.write("EASY_STREET_DEMO_BUDGET_USD=0\n")
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("Private judge values saved in deploy/.env.judging.local. No credentials were printed.")
    print("After deployment approval, enter these values in the host's runtime secrets. The Nebius API key belongs there separately.")


if __name__ == "__main__":
    main()
