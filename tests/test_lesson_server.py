"""teach-onboard serve over HTTP with the fake provider: answers, feedback, MAP updates, drafting, and the guards."""
import http.client
import json
import threading
import time
import urllib.request

import pytest

from teach_onboard import answers as A
from teach_onboard.lesson_server import install_kit, serve_lessons
from teach_onboard.llm import FakeProvider
from teach_onboard.runner import LessonRunner

LESSON = "0001-the-three-areas"


@pytest.fixture
def served(course, method):
    runner = LessonRunner(course, FakeProvider(), method)
    httpd = serve_lessons(runner, {"provider": "fake", "model": "fake", "course": course.name}, "127.0.0.1", 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", runner
    httpd.shutdown()
    runner.close()


def call(base, path, body=None, headers=None):
    data = None if body is None else json.dumps(body).encode()
    h = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(base + path, data=data, headers={**h, **(headers or {})})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if r.headers.get_content_type() == "application/json" else raw)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def wait(base, job_id):
    for _ in range(100):
        j = call(base, f"/api/jobs/{job_id}")[1]
        if j["status"] not in ("queued", "running"):
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def save(base, prompt, answer):
    return call(base, "/api/answer", {"lesson": LESSON, "prompt": prompt, "answer": answer, "prompt_text": f"Q for {prompt}"})


def test_pages_and_kit(served):
    base, _ = served
    assert call(base, "/api/ping")[1]["teach"] is True
    code, page = call(base, "/")
    assert code == 200 and b"0001 \xc2\xb7 S2: the three areas" in page
    assert b"lesson-kit.js" in call(base, f"/lessons/{LESSON}.html")[1]
    assert b"teach lesson kit" in call(base, "/assets/lesson-kit.js")[1]        # bundled kit when the course has none
    assert b"Skill map: Git basics" in call(base, "/MAP.md")[1]
    for bad in ["/../etc/passwd", "/lessons/../MAP.md", "/.teach/jobs.json", "/lessons/%2e%2e/MAP.md", "/MISSION.txt", "/api/nope"]:
        assert call(base, bad)[0] == 404, bad


def test_save_answers_and_review_updates_map(served, course):
    base, runner = served
    code, out = save(base, "practice-1", "right: it sits in the staging area")
    assert code == 200 and out["path"] == f"answers/{LESSON}.md"
    for i in range(1, 6):
        assert save(base, f"check-{i}", "right answer" if i != 3 else "no idea")[0] == 200
    text = (course / "answers" / f"{LESSON}.md").read_text()
    assert text.count("## Answer · ") == 6 and text.count(A.WAITING) == 6
    assert "Skill: S2 · Kind: check" in text

    st = call(base, f"/api/lesson?lesson={LESSON}")[1]
    assert st["pending"] == 6 and st["status"] == "answered" and st["next"] is None
    assert [p["prompt"] for p in st["prompts"] if p["saved"]] == ["practice-1"] + [f"check-{i}" for i in range(1, 6)]

    job = call(base, "/api/review", {"lesson": LESSON})[1]["job"]
    done = wait(base, job["id"])
    assert done["status"] == "done", done
    entries = A.parse((course / "answers" / f"{LESSON}.md").read_text())
    assert all(e.feedback is not None for e in entries)
    assert {e.prompt: e.judgment for e in entries}["check-3"] == "incorrect"
    m = (course / "MAP.md").read_text()
    assert "| S2 | explain the working tree, the staging area and the repository | S1 | learning | 4/5 | " in m
    assert "- S2 (" in m and "no idea (incorrect)" in m
    assert "4/5" in (course / "LOG.md").read_text().splitlines()[-1]
    assert done["result"]["learning_record"] is None and not (course / "learning-records").exists()
    fb = call(base, f"/api/answers?lesson={LESSON}&prompt=check-1")[1]["answers"][0]
    assert fb["judgment"] == "correct" and fb["feedback_by"] == "teach-onboard serve, fake"
    assert call(base, "/api/review", {"lesson": LESSON})[0] == 400              # nothing waiting now


def test_quiz_clicks_are_light_evidence(served, course):
    base, _ = served
    before = (course / "MAP.md").read_text()
    for _ in range(3):
        assert call(base, "/api/event", {"type": "quiz", "lesson": LESSON, "quiz": "1", "choice": "A", "correct": True})[0] == 200
    assert (course / "MAP.md").read_text() == before
    assert len((course / ".teach" / "events.jsonl").read_text().splitlines()) == 3


def test_draft_next_lesson(served, course):
    base, runner = served
    assert call(base, "/api/draft", {"lesson": LESSON})[0] == 400              # needs feedback first
    save(base, "practice-1", "right")
    wait(base, call(base, "/api/review", {"lesson": LESSON})[1]["job"]["id"])
    job = call(base, "/api/draft", {"lesson": LESSON})[1]["job"]
    done = wait(base, job["id"])
    assert done["status"] == "done", done
    rel = done["result"]["path"]
    assert rel == "lessons/0002-demo-next-lesson.html"
    html = (course / rel).read_text()
    assert "alert(" not in html and html.count("<script") == 1
    assert "AI-drafted on " in html and "#needs-verification" in html and 'data-skill="S2"' in html
    assert f'<link rel="prev" href="{LESSON}.html"' in html
    res = (course / "RESOURCES.md").read_text()
    assert "## Sources from drafted lessons" in res and "https://example.com/fake-source) #needs-verification" in res
    st = call(base, f"/api/lesson?lesson={LESSON}")[1]
    assert st["next"]["lesson"] == "0002-demo-next-lesson"
    assert call(base, "/api/draft", {"lesson": LESSON})[0] == 400              # the next lesson exists now


def test_unknown_lesson_and_prompt(served):
    base, _ = served
    assert call(base, "/api/answer", {"lesson": "../MAP", "prompt": "p", "answer": "x"})[0] == 400
    assert call(base, "/api/answer", {"lesson": LESSON, "prompt": "not-a-box", "answer": "x"})[0] == 400
    assert call(base, "/api/answer", {"lesson": LESSON, "prompt": "check-1", "answer": "  "})[0] == 400


def test_cross_site_posts_are_refused(served, course):
    base, _ = served
    host, port = base.removeprefix("http://").split(":")
    body = json.dumps({"lesson": LESSON, "prompt": "check-1", "answer": "x"})

    def raw(headers):
        c = http.client.HTTPConnection(host, int(port))
        c.request("POST", "/api/answer", body=body, headers=headers)
        return c.getresponse().status

    assert raw({"Content-Type": "text/plain"}) == 400                           # a simple form post
    assert raw({"Content-Type": "application/json", "Origin": "https://evil.example"}) == 403
    assert raw({"Content-Type": "application/json", "Host": "evil.example"}) == 421   # DNS rebinding
    assert not (course / "answers").exists()


def test_jobs_survive_a_restart(course, method):
    r1 = LessonRunner(course, FakeProvider(), method, start_worker=False)
    r1.save_answer(LESSON, "practice-1", "right")
    job = r1.start_review(LESSON)
    r1.jobs.jobs[-1]["status"] = "running"                                     # stopped mid-run
    r1.jobs._save()
    r2 = LessonRunner(course, FakeProvider(), method, start_worker=False)
    assert r2.job(job["id"])["status"] == "queued"
    r2.jobs.run_pending()
    assert r2.job(job["id"])["status"] == "done"


def test_install_kit(tmp_path):
    written = install_kit(tmp_path)
    assert sorted(p.name for p in written) == ["lesson-kit.css", "lesson-kit.js"]
    assert install_kit(tmp_path) == []                                         # never overwrites unless asked


class NoWebFake(FakeProvider):
    can_research = False


def test_draft_without_web_refuses_unretrieved_sources(course, method):
    """Without web research a draft may cite only RESOURCES.md; the fake cites another page, so nothing is saved."""
    r = LessonRunner(course, NoWebFake(), method, start_worker=False)
    r.save_answer(LESSON, "practice-1", "right")
    r.start_review(LESSON)
    r.jobs.run_pending()
    job = r.start_draft(LESSON)
    r.jobs.run_pending()
    j = r.job(job["id"])
    assert j["status"] == "failed" and "neither retrieved" in j["error"]
    assert r.lesson_ids() == [LESSON]
