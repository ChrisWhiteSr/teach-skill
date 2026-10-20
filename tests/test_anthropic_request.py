"""Check the request the Claude API provider sends, against a local stub instead of the real API."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from teach_onboard.llm import FALLBACK_BETA, AnthropicProvider, LLMError

CAPTURED = []


def reply(stop_reason="end_turn", text='{"ok": true}'):
    return {"id": "msg_1", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
            "content": [{"type": "text", "text": text}], "stop_reason": stop_reason, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5}}


class Stub(BaseHTTPRequestHandler):
    responses: list = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        CAPTURED.append({"path": self.path, "headers": dict(self.headers), "body": body})
        status, payload = self.responses.pop(0) if self.responses else (200, reply())
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def stub(monkeypatch):
    CAPTURED.clear()
    Stub.responses = []
    httpd = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"http://127.0.0.1:{httpd.server_address[1]}")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    yield Stub
    httpd.shutdown()


SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}


def test_request_shape(stub):
    p = AnthropicProvider()
    assert p.json(task="t", system="sys", user="hi", schema=SCHEMA, effort="low") == {"ok": True}
    req = CAPTURED[0]
    assert req["path"].startswith("/v1/messages")
    assert FALLBACK_BETA in req["headers"].get("anthropic-beta", "")
    b = req["body"]
    assert b["model"] == "claude-opus-5-5" and b["fallbacks"] == "default"
    assert b["output_config"] == {"format": {"type": "json_schema", "schema": SCHEMA}, "effort": "low"}
    assert b["system"] == "sys" and "thinking" not in b and "temperature" not in b


def test_drops_fallbacks_when_rejected(stub):
    stub.responses = [(400, {"type": "error", "error": {"type": "invalid_request_error", "message": "fallbacks: not supported"}})]
    p = AnthropicProvider()
    assert p.json(task="t", system="s", user="u", schema=SCHEMA, effort="low") == {"ok": True}
    assert "fallbacks" not in CAPTURED[-1]["body"] and p.fallbacks is False


def test_refusal_is_an_error(stub):
    stub.responses = [(200, reply(stop_reason="refusal", text=""))]
    with pytest.raises(LLMError, match="declined"):
        AnthropicProvider().json(task="t", system="s", user="u", schema=SCHEMA, effort="low")
