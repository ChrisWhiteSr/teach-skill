import json
import threading
import urllib.request

import pytest

from teach_onboard.llm import FakeProvider
from teach_onboard.onboarding import Onboarding
from teach_onboard.server import serve


@pytest.fixture
def base(tmp_path, method):
    app = Onboarding(FakeProvider(), method, tmp_path)
    httpd = serve(app, {"provider": "fake", "model": "fake", "courses_home": str(tmp_path), "packs": [],
                        "placement_max_items": 12, "session_minutes": 25}, "127.0.0.1", 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def call(base, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_static_and_config(base):
    with urllib.request.urlopen(base + "/") as r:
        assert b"<title>Teach" in r.read()
    assert call(base, "/api/config")[1]["provider"] == "fake"
    assert call(base, "/../etc/passwd")[0] == 404


def test_full_flow_over_http(base, tmp_path):
    _, s = call(base, "/api/session", {"subject": "Sourdough baking"})
    sid = s["id"]
    p = f"/api/session/{sid}"
    assert call(base, p + "/mission", {"answers": {"why": "Bake a reliable loaf for my family every weekend"}})[1]["mission"]
    m = call(base, p + "/map", {})[1]
    assert call(base, p + "/map/confirm", {"skills": m["skills"], "drop": [], "flagged": []})[0] == 200
    while not (item := call(base, p + "/placement/next", {})[1])["done"]:
        call(base, p + "/placement/answer", {"answer": "right", "dont_know": False})
    assert call(base, p + "/summary")[1]["counts"]["mastered_tested"] >= 1
    out = call(base, p + "/finish", {})[1]
    assert out["path"].endswith("sourdough-baking") and (tmp_path / "sourdough-baking" / "LOG.md").is_file()


def test_errors_are_json(base):
    code, body = call(base, "/api/session/nope/map", {})
    assert code == 400 and "unknown session" in body["error"]
    code, body = call(base, "/api/session", {"subject": "  "})
    assert code == 400
