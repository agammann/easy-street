"""Default server entry point; importing the app factory alone has no runtime side effects."""
from dotenv import load_dotenv
from .main import ROOT, create_app

load_dotenv(ROOT / ".env.local",override=False)
load_dotenv(ROOT / ".env",override=False)
app = create_app()

__all__ = ["app", "create_app"]
