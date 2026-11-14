"""Exercise the real SDK over loopback; no real API key or provider calls."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from backend.provider import (
    GENERATION_INSTRUCTIONS,
    MAX_GENERATION_TOKENS,
    MAX_VERIFICATION_TOKENS,
    MODEL,
    VERIFICATION_INSTRUCTIONS,
    OpenAIProvider,
)


@pytest.fixture
def provider_server(monkeypatch):
    requests = []
    replies = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            requests.append((self.path, json.loads(self.rfile.read(length))))
            status, body = replies.pop(0)
            encoded = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("OPENAI_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    try:
        yield OpenAIProvider(api_key="test-only-not-a-real-key"), requests, replies
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def response(output, *, status="completed"):
    return {
        "id": "resp_test", "object": "response", "created_at": 1,
        "model": MODEL, "status": status,
        "output": [{"id": "msg_test", "type": "message", "role": "assistant",
                    "status": "completed", "content": output}],
        "usage": {"input_tokens": 23, "output_tokens": 7, "total_tokens": 30,
                  "input_tokens_details": {"cached_tokens": 0},
                  "output_tokens_details": {"reasoning_tokens": 0}},
        "parallel_tool_calls": False, "tool_choice": "none", "tools": [],
    }


def output_text(value):
    return [{"type": "output_text", "text": json.dumps(value), "annotations": []}]


def test_sdk_generation_and_verification_round_trip(provider_server):
    provider, requests, replies = provider_server
    replies.extend([
        (200, response(output_text({"sections": [{
            "id": "notes", "kind": "notes", "title": "Notes", "body": "A fact.",
            "answer": None, "explanation": None, "evidence_ids": ["e0001"],
        }]}))),
        (200, response(output_text({"results": [{"section_id": "notes",
                                                    "status": "supported", "reason": "Matches."}]}))),
    ])
    course, generated_usage = provider.generate({"passages": [{"id": "p1", "text": "A fact."}]})
    verified, verified_usage = provider.verify({"sections": [{"id": "notes"}], "passages": []})
    assert course.sections[0].evidence[0].model_dump() == {"passage_id": "p1", "quote": "A fact."}
    assert verified.results[0].status == "supported"
    assert (generated_usage.input_tokens, generated_usage.output_tokens) == (23, 7)
    assert (verified_usage.input_tokens, verified_usage.output_tokens) == (23, 7)
    assert len(requests) == 2
    for (path, body), instructions, limit in zip(
        requests, (GENERATION_INSTRUCTIONS, VERIFICATION_INSTRUCTIONS),
        (MAX_GENERATION_TOKENS, MAX_VERIFICATION_TOKENS), strict=True,
    ):
        assert path == "/v1/responses"
        assert body["model"] == MODEL
        assert body["instructions"] == instructions
        assert body["store"] is False
        assert body["max_output_tokens"] == limit
        assert body["text"]["format"]["type"] == "json_schema"
        assert body["text"]["format"]["strict"] is True
    assert json.loads(requests[0][1]["input"])["evidence_catalog"][0]["quote"] == "A fact."


@pytest.mark.parametrize("body", [
    response(output_text({"results": []}), status="incomplete"),
    response([{"type": "refusal", "refusal": "Unable to comply."}]),
])
def test_sdk_incomplete_or_refusal_is_not_accepted(provider_server, body):
    provider, requests, replies = provider_server
    replies.append((200, body))
    with pytest.raises(RuntimeError, match="incomplete.*refused"):
        provider.verify({"sections": [], "passages": []})
    assert len(requests) == 1


def test_sdk_does_not_retry_failed_request(provider_server):
    from openai import InternalServerError

    provider, requests, replies = provider_server
    replies.append((500, {"error": {"message": "synthetic failure", "type": "server_error"}}))
    with pytest.raises(InternalServerError):
        provider.verify({"sections": [], "passages": []})
    assert len(requests) == 1
