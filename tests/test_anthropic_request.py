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
        if isinstance(payload, str):  # a server-sent event stream
            data = payload.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
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


def sse(blocks, stop_reason):
    """A streamed message: each block is (start block, optional input JSON for a tool_use)."""
    ev = [("message_start", {"type": "message_start", "message": {
        "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-opus-5-5", "content": [],
        "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 1}}})]
    for i, (block, partial) in enumerate(blocks):
        ev.append(("content_block_start", {"type": "content_block_start", "index": i, "content_block": block}))
        if partial is not None:
            ev.append(("content_block_delta", {"type": "content_block_delta", "index": i,
                                               "delta": {"type": "input_json_delta", "partial_json": partial}}))
        ev.append(("content_block_stop", {"type": "content_block_stop", "index": i}))
    ev.append(("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop_reason, "stop_sequence": None},
                                 "usage": {"output_tokens": 5}}))
    ev.append(("message_stop", {"type": "message_stop"}))
    return "".join(f"event: {n}\ndata: {json.dumps(d)}\n\n" for n, d in ev)


SEARCH = [({"type": "server_tool_use", "id": "srvtoolu_1", "name": "web_search", "input": {"query": "git staging"}}, None),
          ({"type": "web_search_tool_result", "tool_use_id": "srvtoolu_1", "content": [
              {"type": "web_search_result", "url": "https://www.Example.org/staging/", "title": "Staging",
               "encrypted_content": "x", "page_age": None}]}, None)]


def submit(tid, ok):
    return ({"type": "tool_use", "id": tid, "name": "submit", "input": {}}, json.dumps({"ok": ok}))


def test_research_request_and_check_loop(stub):
    stub.responses = [(200, sse(SEARCH + [submit("toolu_1", False)], "tool_use")),
                      (200, sse([submit("toolu_2", True)], "tool_use"))]
    seen = []

    def check(out, retrieved):
        seen.append(set(retrieved))
        return [] if out["ok"] else ["ok must be true"]

    p = AnthropicProvider()
    out, retrieved = p.research(task="draft", system="sys", user="u", schema=SCHEMA, effort="high", check=check,
                                max_searches=3, max_fetches=2)
    assert out == {"ok": True} and retrieved == {"https://example.org/staging"} and seen[0] == retrieved
    first, second = CAPTURED[0]["body"], CAPTURED[1]["body"]
    assert first["stream"] is True and first["fallbacks"] == "default"
    assert FALLBACK_BETA in CAPTURED[0]["headers"].get("anthropic-beta", "")
    tools = {t["name"]: t for t in first["tools"]}
    assert tools["web_search"] == {"type": "web_search_20260209", "name": "web_search", "max_uses": 3}
    assert tools["web_fetch"]["type"] == "web_fetch_20260209" and tools["web_fetch"]["max_uses"] == 2
    assert tools["submit"]["strict"] is True and tools["submit"]["input_schema"] == SCHEMA
    assert first["tool_choice"] == {"type": "auto"} and first["output_config"] == {"effort": "high"}
    assert "thinking" not in first and "temperature" not in first
    # The rejected submit goes back as a tool error, after the assistant turn echoed unchanged.
    assert [b["type"] for b in second["messages"][1]["content"]] == ["server_tool_use", "web_search_tool_result", "tool_use"]
    result = second["messages"][2]["content"][0]
    assert result["is_error"] is True and result["tool_use_id"] == "toolu_1" and "ok must be true" in result["content"]


def test_research_refusal_is_an_error(stub):
    stub.responses = [(200, sse([], "refusal"))]
    with pytest.raises(LLMError, match="declined"):
        AnthropicProvider().research(task="draft", system="s", user="u", schema=SCHEMA, effort="high")
