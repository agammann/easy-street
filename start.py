"""Run the local Easy Street application after building the frontend."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent


def main():
    os.chdir(ROOT)
    if not (ROOT / "frontend" / "dist" / "index.html").exists():
        raise SystemExit("Build the frontend first: cd frontend && npm install && npm run build")
    import uvicorn
    print("Easy Street is opening at http://127.0.0.1:8000")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, access_log=False)


if __name__ == "__main__":
    main()
