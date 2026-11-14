"""Read-only diagnostic. No inference, automatic retries, alerts, or scheduler."""
import argparse
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def origin(value):
    parsed = urlsplit(value)
    if (not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ("", "/")
            or parsed.scheme not in ("http", "https")):
        raise ValueError("Use an HTTPS origin without credentials, path, or query.")
    if parsed.scheme == "http" and parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Plain HTTP is allowed only for local diagnostics.")
    return value.rstrip("/")


def read_json(base, path, token=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(base + path, headers=headers, method="GET")
    try:
        with build_opener(NoRedirect).open(request, timeout=5) as response:
            if response.status != 200:
                raise ValueError("Unexpected status.")
            raw = response.read(65537)
            if len(raw) > 65536:
                raise ValueError("Response too large.")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("Expected an object.")
            return result
    except (HTTPError, URLError, OSError, ValueError, UnicodeError):
        # Do not print provider errors, response bodies, request headers or tokens.
        return None


def check(base, operator_token=None, expect_generation=False):
    live = read_json(base, "/health/live")
    ready = read_json(base, "/health/ready")
    summary = {"live": live is not None, "ready": ready is not None}
    if live is None or ready is None:
        return 1, {**summary, "needs_attention": True}
    available = ready.get("generation_available") is True
    summary["generation_available"] = available
    attention = expect_generation and not available
    if operator_token:
        status = read_json(base, "/api/operator/status", operator_token)
        if status is None or not isinstance(status.get("needs_attention"), bool):
            return 1, {**summary, "operator_status": False, "needs_attention": True}
        summary["operator_status"] = True
        attention = attention or status["needs_attention"]
    summary["needs_attention"] = attention
    return int(attention), summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Demo origin; no credentials or query.")
    parser.add_argument("--operator", action="store_true", help="Read protected status using EASY_STREET_OPERATOR_TOKEN from environment.")
    parser.add_argument("--expect-generation", action="store_true", help="Fail when generation is unavailable, including an exhausted allowance.")
    args = parser.parse_args()
    try:
        base = origin(args.url)
    except ValueError:
        print(json.dumps({"configuration_valid": False}))
        return 2
    token = os.environ.get("EASY_STREET_OPERATOR_TOKEN") if args.operator else None
    if args.operator and (not token or len(token) < 32):
        print(json.dumps({"operator_token_configured": False}))
        return 2
    code, summary = check(base, token, args.expect_generation)
    print(json.dumps(summary, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
