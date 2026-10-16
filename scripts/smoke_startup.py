"""Exercise the built app on port 8000 with disposable data and no API key."""
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, ProxyHandler, build_opener
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8000"
HTTP = build_opener(ProxyHandler({}))


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def require_free_port():
    # Windows allows SO_REUSEADDR to bind beside an existing listener, so first
    # reject a successful TCP connection. No HTTP request reaches that app.
    try:
        connection = socket.create_connection(("127.0.0.1", 8000), timeout=3)
    except ConnectionRefusedError:
        pass
    except OSError as exc:
        raise RuntimeError("Cannot verify that port 8000 is free.") from exc
    else:
        connection.close()
        raise RuntimeError("Port 8000 is occupied. Stop your app before running this smoke test.")
    with socket.socket() as probe:
        # Closed listeners leave TIME_WAIT sockets on Windows and POSIX. Reuse
        # permits the same restart that uvicorn performs without treating those
        # old connections as a running app.
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", 8000))
        except OSError as exc:
            raise RuntimeError("Port 8000 is occupied. Stop your app before running this smoke test.") from exc


def request(path, data=None, content_type="application/json"):
    headers = {"Content-Type": content_type} if data is not None else {}
    if isinstance(data, dict):
        data = json.dumps(data).encode()
    with HTTP.open(Request(BASE + path, data=data, headers=headers), timeout=10) as response:
        body = response.read()
        return body, response.headers


def api(path, data=None):
    return json.loads(request(path, data)[0])


def upload(path):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{path.name}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode()
    body += path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    return json.loads(request("/api/documents", body, f"multipart/form-data; boundary={boundary}")[0])


class Server:
    def __init__(self, root):
        self.root, self.process, self.log = root, None, None

    def start(self):
        require_free_port()
        # The disposable root contains no env files, and inherited provider settings
        # are removed. The app uses only the bundled offline sample in this test.
        env = {key: value for key, value in os.environ.items() if not key.upper().startswith("OPENAI_")}
        env.update(OPENAI_API_KEY="", EASY_STREET_BUDGET_USD="0",
                   EASY_STREET_DATA_DIR=str(self.root / "data"), PYTHONUNBUFFERED="1")
        self.log = (self.root / "server.log").open("ab")
        self.process = subprocess.Popen([sys.executable, str(self.root / "start.py")],
                                        cwd=self.root, env=env, stdout=self.log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            check(self.process.poll() is None, "Production server exited before becoming healthy.")
            try:
                if api("/api/health") == {"status": "ok"}:
                    return
            except (URLError, TimeoutError, ConnectionError):
                pass
            time.sleep(0.2)
        raise RuntimeError("Production server did not become healthy within 45 seconds.")

    def stop(self):
        had_process = self.process is not None
        if self.process and self.process.poll() is None:
            if os.name == "nt":
                # Stop only our launcher and its descendants, including the
                # interpreter process used by Windows virtual environments.
                subprocess.run(["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW, check=True)
            else:
                self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        self.process = None
        if self.log:
            self.log.close()
        if had_process:
            # Windows' virtual-environment launcher can finish before its child
            # closes the listening socket. Wait for shutdown before restarting.
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    connection = socket.create_connection(("127.0.0.1", 8000), timeout=3)
                except ConnectionRefusedError:
                    return
                except TimeoutError:
                    continue
                else:
                    connection.close()
                time.sleep(0.1)
            raise RuntimeError("Smoke server did not release port 8000 after shutdown.")


def verify_assets():
    body, headers = request("/")
    html = body.decode()
    check("text/html" in headers.get("Content-Type", "") and "Easy Street" in html,
          "Production entry HTML is missing.")
    assets = re.findall(r'(?:src|href)="(/assets/[^"?#]+\.(?:js|css))"', html)
    check(any(path.endswith(".js") for path in assets) and any(path.endswith(".css") for path in assets),
          "Production HTML must reference built JavaScript and CSS.")
    for path in assets:
        asset, headers = request(path)
        expected = "javascript" if path.endswith(".js") else "text/css"
        check(asset and expected in headers.get("Content-Type", ""), f"Broken production asset: {path}")
    artwork, headers = request("/learning-road.png")
    check(artwork.startswith(b"\x89PNG\r\n\x1a\n") and "image/png" in headers.get("Content-Type", ""),
          "Production artwork is missing.")


def verify_no_usage():
    check(api("/api/config")["key_configured"] is False, "Smoke server unexpectedly has an API key.")
    usage = api("/api/usage")
    check(not usage["records"] and usage["budget"]["spent_usd"] == 0
          and usage["budget"]["reserved_usd"] == 0, "Offline test recorded usage or reserved money.")


def verify_course(root):
    pdf = upload(root / "backend" / "sample" / "chapter.pdf")
    check(pdf["format"] == "pdf" and pdf["passages"] and pdf["passages"][0]["page"] == 1,
          "Bundled PDF did not extract with page references.")
    document = upload(root / "backend" / "sample" / "chapter.txt")
    check(document["format"] == "txt" and document["is_sample"] and len(document["passages"]) >= 3,
          "Bundled TXT did not extract as the offline sample.")
    course = api("/api/courses", {"document_id": document["id"], "title": "Startup smoke course",
                                 "mode": "demo", "questions_per_quiz": 3})
    course_path = "/api/courses/" + course["id"]
    check(course["status"] == "outline" and course["outline"]["selected_passage_ids"],
          "Course outline was not created from the sample.")
    check(api(course_path + "/approve", {"provider_disclosure_accepted": True})["outline_approved"],
          "Outline approval was not saved.")
    check(api(course_path + "/estimate")["estimated_max_usd"] == 0, "Offline estimate is not zero.")
    job = api(course_path + "/generate", {"idempotency_key": uuid.uuid4().hex})
    deadline = time.monotonic() + 30
    while job["status"] in ("queued", "running") and time.monotonic() < deadline:
        time.sleep(0.1)
        job = api("/api/jobs/" + job["id"])
    check(job["status"] == "complete", f"Offline generation ended with status {job['status']}.")
    course = api(course_path)
    check(len(course["sections"]) == 10 and sum(s["kind"] == "quiz" for s in course["sections"]) == 3,
          "Generated course does not contain the expected sections and questions.")
    for format_name, expected in (("html", "Learner course"), ("answers", "Answer key"), ("json", None)):
        body, headers = request(course_path + "/export?format=" + format_name)
        check("attachment" in headers.get("Content-Disposition", ""), "Export lacks a download filename.")
        if expected:
            check(expected in body.decode() and "text/html" in headers.get("Content-Type", ""),
                  f"Invalid {format_name} export.")
        else:
            backup = json.loads(body)
            check(backup["course"] == course and backup["source_text_included"] is False,
                  "JSON export does not preserve the course or excludes-source flag.")
    return course_path, course


def main():
    require_free_port()
    check((ROOT / "frontend" / "dist" / "index.html").is_file(), "Build the frontend before this smoke test.")
    with tempfile.TemporaryDirectory(prefix="easy-street-smoke-") as temporary:
        root = Path(temporary)
        shutil.copy2(ROOT / "start.py", root / "start.py")
        (root / "backend" / "sample").mkdir(parents=True)
        for source in (ROOT / "backend").glob("*.py"):
            shutil.copy2(source, root / "backend" / source.name)
        for name in ("chapter.txt", "chapter.pdf"):
            shutil.copy2(ROOT / "backend" / "sample" / name, root / "backend" / "sample" / name)
        shutil.copytree(ROOT / "frontend" / "dist", root / "frontend" / "dist")
        server = Server(root)
        try:
            server.start()
            verify_no_usage()
            verify_assets()
            course_path, course = verify_course(root)
            verify_no_usage()
            server.stop()
            server.start()
            check(api(course_path) == course, "Saved course changed or disappeared after restart.")
            check(api(course_path + "/job")["status"] == "complete", "Saved job was not restored.")
            verify_no_usage()
        except Exception:
            server.stop()
            if (root / "server.log").exists():
                print((root / "server.log").read_text(errors="replace")[-6000:], file=sys.stderr)
            raise
        finally:
            server.stop()
    print("PASS: production startup, built assets, PDF/TXT extraction, offline generation, three exports,")
    print("      restart persistence, no configured API key, and zero usage/reservations.")


if __name__ == "__main__":
    main()
