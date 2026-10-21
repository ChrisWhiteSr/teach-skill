import pytest

from teach_onboard.files import Conflict, CourseFiles, WriteRefused, sanitize_lesson_html, sha


def test_writes_are_confined(tmp_path):
    f = CourseFiles(tmp_path)
    for bad in ["../x.md", "/etc/passwd", "a/../../x.md", ".git/config", "answers/.hidden.md", ".teach/jobs.json"]:
        with pytest.raises(WriteRefused):
            f.update(bad, lambda t: "x")
    for not_allowed in ["lessons/0001-x.md", "script.js", "MISSION.md", "answers/sub/x.md", "assets/lesson-kit.js"]:
        with pytest.raises(WriteRefused):
            f.update(not_allowed, lambda t: "x")
    f.update(".teach/jobs.json", lambda t: "[]", internal=True)
    assert (tmp_path / ".teach" / "jobs.json").read_text() == "[]"


def test_symlink_escape(tmp_path):
    root, other = tmp_path / "course", tmp_path / "other"
    root.mkdir(); other.mkdir()
    (root / "answers").symlink_to(other)
    with pytest.raises(WriteRefused):
        CourseFiles(root).update("answers/0001-x.md", lambda t: "x")
    assert not (other / "0001-x.md").exists()


def test_stale_write_is_refused(tmp_path):
    f = CourseFiles(tmp_path)
    (tmp_path / "MAP.md").write_text("v1\n")
    _, base = f.read("MAP.md")
    (tmp_path / "MAP.md").write_text("v2 from another agent\n")
    with pytest.raises(Conflict):
        f.write("MAP.md", "mine\n", base)
    assert (tmp_path / "MAP.md").read_text() == "v2 from another agent\n"
    with pytest.raises(Conflict):
        f.write("LOG.md", "x", sha("something"))  # a file that does not exist has no hash
    f.write("LOG.md", "new\n", None)


def test_conflict_merges_instead_of_overwriting(tmp_path):
    f = CourseFiles(tmp_path)
    (tmp_path / "LOG.md").write_text("| row from onboarding |\n")
    calls = []

    def append_mine(text):
        calls.append(text)
        if len(calls) == 1:  # another teacher writes while this change is being made
            (tmp_path / "LOG.md").write_text(text + "| row from hermes |\n")
        return text + "| row from the runner |\n"

    new, changed = f.update("LOG.md", append_mine)
    assert changed and len(calls) == 2
    assert new == "| row from onboarding |\n| row from hermes |\n| row from the runner |\n"
    assert (tmp_path / "LOG.md").read_text() == new


def test_lesson_writes_are_new_html_only(tmp_path):
    f = CourseFiles(tmp_path)
    page = '<html><head></head><body><main>Hi</main></body></html>'
    for bad in ["lessons/1-x.html", "lessons/0002-X.html", "reference/0002-x.html", "lessons/0002-x.htm", "lessons/../0002-x.html"]:
        with pytest.raises(WriteRefused):
            f.write_lesson(bad, page)
    f.write_lesson("lessons/0002-next-step.html", page)
    with pytest.raises(WriteRefused):
        f.write_lesson("lessons/0002-next-step.html", page)
    with pytest.raises(WriteRefused):
        f.write_lesson("lessons/0003-no-main.html", "<html><body>x</body></html>")
    assert '<script defer src="../assets/lesson-kit.js"></script>' in (tmp_path / "lessons/0002-next-step.html").read_text()


def test_scripts_other_than_the_kit_are_stripped():
    html = ('<head><script>alert(1)</script><script defer src="../assets/lesson-kit.js"></script>'
            '<script src="https://cdn.example/x.js"></script>'
            '<meta http-equiv="refresh" content="0;url=https://e.x"><base href="https://e.x/"></head>'
            '<main><a href="javascript:alert(1)">a</a><a href="jav&#x61;script:x">b</a><img src="x.png" onerror="alert(1)">'
            '<iframe src="https://e.x"></iframe><svg><script>alert(2)</script></svg><a href="https://ok.example/">ok</a>'
            '<button onclick = "x()">c</button><object data="x"></object><embed src="y"></main><SCRIPT/src="evil.js">')
    out = sanitize_lesson_html(html)
    assert out.count("<script") == 1 and '<script defer src="../assets/lesson-kit.js"></script>' in out
    for gone in ["alert", "cdn.example", "evil.js", "http-equiv", "<base", "javascript", "jav&#x61;", "onerror", "onclick",
                 "<iframe", "<object", "<embed"]:
        assert gone not in out, gone
    assert 'href="https://ok.example/"' in out and '<img src="x.png">' in out
