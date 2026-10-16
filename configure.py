"""Configure your own backend key without displaying it or putting it in shell history."""
from decimal import Decimal, InvalidOperation
from getpass import getpass
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parent


def main():
    target = ROOT / ".env.local"
    if target.is_symlink():
        raise SystemExit("Refusing to write configuration through a symbolic link.")
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    print("Easy Street is free software. Your own OpenAI account pays for generation.")
    print("This saves configuration only to .env.local in this app folder. Keep that file private.")
    key = getpass("OpenAI API key (hidden; Enter keeps the current value): ").strip()
    if key and (not key.startswith("sk-") or any(ch.isspace() for ch in key) or any(ch in key for ch in "\"'\\#")):
        raise SystemExit("That does not look like an OpenAI API key. Nothing was saved.")
    budget = input("Cumulative local budget in USD (Enter keeps the current value; default $1): ").strip()
    if budget:
        try:
            amount = Decimal(budget)
            if not amount.is_finite() or not 0 <= amount <= 10000:
                raise InvalidOperation
        except InvalidOperation:
            raise SystemExit("Choose a budget between 0 and 10000 USD. Nothing was saved.")
        budget = format(amount, "f")
    updates = {name:value for name,value in (("OPENAI_API_KEY",key),("EASY_STREET_BUDGET_USD",budget)) if value}
    if not updates:
        print("No configuration changes.")
        return
    lines = [line for line in existing.splitlines() if not any(re.match(r"^\s*(?:export\s+)?" + re.escape(name) + r"\s*=",line) for name in updates)]
    lines.extend(f"{name}={value}" for name,value in updates.items())
    descriptor, temporary = tempfile.mkstemp(prefix=".env-setup-",dir=ROOT)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("Configuration saved. Restart Easy Street and check Settings. No key was displayed.")


if __name__ == "__main__":
    main()
