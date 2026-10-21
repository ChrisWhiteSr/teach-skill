"""Model providers. Every call asks for JSON that matches a schema (structured outputs).

- anthropic: the Claude API. Credentials come from the environment the usual way
  (ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an `ant auth login` profile).
  Requests opt into server-side refusal fallbacks (`fallbacks: "default"`).
- bedrock: Claude on Amazon Bedrock through AWS credentials (profile and region from the environment).
  Bedrock has no web search, so research() is unavailable there and callers fall back to json().
- fake: canned answers for tests and offline demos. It does not teach anything.

research() is the one call that uses tools: server-side web search and web fetch, then a strict
`submit` tool whose input is the result. It returns the result and every URL the web tools retrieved,
so callers can refuse citations that were never retrieved.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_BEDROCK_MODEL = "us.anthropic.claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMError(RuntimeError):
    pass


@dataclass
class Call:
    task: str
    ms: int
    input_tokens: int = 0
    output_tokens: int = 0


class Provider(Protocol):
    name: str
    model: str
    calls: list[Call]

    can_research: bool

    def json(self, *, task: str, system: str, user: str, schema: dict, effort: str) -> dict: ...

    def research(self, *, task: str, system: str, user: str, schema: dict, effort: str,
                 check: "Check | None" = None, max_searches: int = 8, max_fetches: int = 6) -> tuple[dict, set[str]]: ...


# A check gets the submitted result and the URLs retrieved so far, and returns problems to fix (empty: accept).
Check = Callable[[dict, set[str]], list[str]]


def _parse(resp, task: str) -> dict:
    if resp.stop_reason == "refusal":
        raise LLMError(f"the model declined the {task} request ({getattr(resp, 'stop_details', None)})")
    if resp.stop_reason == "max_tokens":
        raise LLMError(f"the {task} reply ran out of room before finishing")
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if text is None:
        raise LLMError(f"the {task} reply had no text (stop_reason={resp.stop_reason})")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError(f"the {task} reply was not valid JSON: {e}") from e


def norm_url(u: str) -> str:
    """Compare URLs loosely: scheme, case of the host, a leading www., trailing slash and fragment don't matter."""
    from urllib.parse import urlsplit, urlunsplit

    try:
        s = urlsplit(u.strip())
    except ValueError:
        return u.strip()
    host = s.netloc.lower().removeprefix("www.")
    return urlunsplit(("https", host, s.path.rstrip("/"), s.query, ""))


def _retrieved_urls(blocks, found: set[str]) -> None:
    """Every URL that a web_search or web_fetch result in these content blocks returned."""
    def walk(o):
        if isinstance(o, dict):
            if o.get("type") in ("web_search_result", "web_fetch_result") and o.get("url"):
                found.add(norm_url(o["url"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for b in blocks:
        d = b.model_dump() if hasattr(b, "model_dump") else b
        if isinstance(d, dict) and str(d.get("type", "")).endswith("_tool_result"):
            walk(d)


def _echo(content: list) -> list:
    """The assistant turn to send back. After a mid-output fallback, drop the declined partial's
    thinking, tool_use and unpaired server_tool_use blocks that sit before the last fallback block."""
    types = [getattr(b, "type", None) for b in content]
    if "fallback" not in types:
        return content
    cut = max(i for i, t in enumerate(types) if t == "fallback")
    paired = {getattr(b, "tool_use_id", None) for b in content if str(getattr(b, "type", "")).endswith("_tool_result")}
    keep = []
    for i, b in enumerate(content):
        t = types[i]
        if i < cut and (t in ("thinking", "redacted_thinking", "tool_use")
                        or (t == "server_tool_use" and getattr(b, "id", None) not in paired)):
            continue
        keep.append(b)
    return keep


class _ClaudeBase:
    name = "claude"
    can_research = True

    def __init__(self, model: str):
        self.model = model
        self.calls: list[Call] = []

    def _create(self, **kwargs):  # pragma: no cover - provided by subclasses
        raise NotImplementedError

    def _stream(self, **kwargs):  # pragma: no cover - provided by subclasses
        raise NotImplementedError

    def _record(self, task: str, t: float, resp) -> None:
        usage = getattr(resp, "usage", None)
        self.calls.append(Call(task, int((time.monotonic() - t) * 1000),
                               getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0))

    def _guarded(self, fn):
        import anthropic

        try:
            return fn()
        except anthropic.AuthenticationError as e:
            raise LLMError(f"{self.name}: credentials were rejected ({e.message})") from e
        except anthropic.NotFoundError as e:
            raise LLMError(f"{self.name}: model {self.model!r} not found ({e.message})") from e
        except anthropic.RateLimitError as e:
            raise LLMError(f"{self.name}: rate limited; wait a minute and retry") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"{self.name}: HTTP {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMError(f"{self.name}: could not connect ({e})") from e

    def json(self, *, task: str, system: str, user: str, schema: dict, effort: str) -> dict:
        t = time.monotonic()
        resp = self._guarded(lambda: self._create(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}, "effort": effort},
        ))
        self._record(task, t, resp)
        return _parse(resp, task)

    def research(self, *, task: str, system: str, user: str, schema: dict, effort: str,
                 check: Check | None = None, max_searches: int = 8, max_fetches: int = 6,
                 max_turns: int = 10) -> tuple[dict, set[str]]:
        """Search and fetch on the web, then submit a result through a strict tool. A failed check is sent
        back as a tool error so the model fixes the result; the loop is bounded by max_turns."""
        tools = [
            {"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches},
            {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": max_fetches, "max_content_tokens": 8000},
            {"name": "submit", "description": "Submit the finished result. Call it once your research is done, with the complete result.",
             "strict": True, "eager_input_streaming": True, "input_schema": schema},
        ]
        messages: list[dict] = [{"role": "user", "content": user}]
        retrieved: set[str] = set()
        nudged = False
        for _ in range(max_turns):
            t = time.monotonic()
            msg = self._guarded(lambda: self._stream(
                model=self.model, max_tokens=64000, system=system, messages=messages, tools=tools,
                tool_choice={"type": "auto"}, output_config={"effort": effort},
            ))
            self._record(task, t, msg)
            _retrieved_urls(msg.content, retrieved)
            if msg.stop_reason == "refusal":
                raise LLMError(f"the model declined the {task} request ({getattr(msg, 'stop_details', None)})")
            if msg.stop_reason == "max_tokens":
                raise LLMError(f"the {task} reply ran out of room before finishing")
            messages.append({"role": "assistant", "content": _echo(msg.content)})
            if msg.stop_reason == "pause_turn":
                continue                      # the server resumes its own tool loop when the turn is sent back
            calls = [b for b in msg.content if getattr(b, "type", None) == "tool_use"]
            if calls:
                results, accepted = [], None
                for c in calls:
                    if c.name != "submit" or not isinstance(c.input, dict):
                        results.append({"type": "tool_result", "tool_use_id": c.id, "is_error": True,
                                        "content": "Unknown tool. Call submit with the finished result."})
                        continue
                    missing = [k for k in schema.get("required", []) if k not in c.input]
                    problems = [f"INVALID_JSON: missing {', '.join(missing)}. Send the complete call again."] if missing else (
                        check(c.input, retrieved) if check else [])
                    if problems:
                        results.append({"type": "tool_result", "tool_use_id": c.id, "is_error": True,
                                        "content": "Not accepted yet. Fix these and call submit again:\n- " + "\n- ".join(problems)})
                    else:
                        accepted = c.input
                        results.append({"type": "tool_result", "tool_use_id": c.id, "content": "Accepted."})
                if accepted is not None:
                    return accepted, retrieved
                messages.append({"role": "user", "content": results})
                continue
            if nudged:
                break
            nudged = True
            messages.append({"role": "user", "content": "Call the submit tool now with the complete result."})
        raise LLMError(f"the {task} request did not end with a result that passed the checks")


class AnthropicProvider(_ClaudeBase):
    name = "anthropic"

    def __init__(self, model: str = DEFAULT_MODEL, fallbacks: bool = True):
        super().__init__(model)
        import anthropic

        has_env = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_PROFILE")
        has_profile = Path("~/.config/anthropic").expanduser().is_dir()
        if not (has_env or has_profile):
            raise LLMError("no Claude API credentials found. Set ANTHROPIC_API_KEY or run `ant auth login`; "
                           "use --provider bedrock for AWS, or --provider fake to look around offline")
        self.client = anthropic.Anthropic(timeout=240.0)
        self.fallbacks = fallbacks

    def _create(self, **kwargs):
        if not self.fallbacks:
            return self.client.messages.create(**kwargs)
        import anthropic

        try:
            return self.client.beta.messages.create(
                **kwargs, betas=[FALLBACK_BETA], extra_body={"fallbacks": "default"}
            )
        except anthropic.BadRequestError as e:
            # Some accounts or models reject the fallback opt-in. Retry once without it and stop sending it.
            if "fallback" not in str(e.message).lower():
                raise
            self.fallbacks = False
            return self.client.messages.create(**kwargs)

    def _stream(self, **kwargs):
        """Streaming, for long tool-using turns; same fallback opt-in and retry as _create."""
        if self.fallbacks:
            import anthropic

            try:
                with self.client.beta.messages.stream(
                    **kwargs, betas=[FALLBACK_BETA], extra_body={"fallbacks": "default"}
                ) as s:
                    return s.get_final_message()
            except anthropic.BadRequestError as e:
                if "fallback" not in str(e.message).lower():
                    raise
                self.fallbacks = False
        with self.client.messages.stream(**kwargs) as s:
            return s.get_final_message()


class BedrockProvider(_ClaudeBase):
    name = "bedrock"
    can_research = False  # no web search or web fetch on Bedrock

    def __init__(self, model: str = DEFAULT_BEDROCK_MODEL, region: str | None = None, profile: str | None = None):
        super().__init__(model)
        from anthropic import AnthropicBedrock

        region = region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
        profile = profile or os.environ.get("TEACH_AWS_PROFILE") or os.environ.get("AWS_PROFILE")
        kwargs = {"aws_region": region, "timeout": 240.0}
        if profile:
            kwargs["aws_profile"] = profile
        self.client = AnthropicBedrock(**kwargs)

    def _create(self, **kwargs):
        return self.client.messages.create(**kwargs)

    def research(self, **kwargs):
        raise LLMError("web research is not available on Bedrock")


class FakeProvider:
    """Deterministic stand-in for tests and offline demos. Answers starting with "right" are graded correct."""

    name = "fake"
    can_research = True
    SOURCE = "https://example.com/fake-source"

    def __init__(self, model: str = "fake"):
        self.model = model
        self.calls: list[Call] = []

    def research(self, *, task: str, system: str, user: str, schema: dict, effort: str,
                 check: Check | None = None, max_searches: int = 8, max_fetches: int = 6) -> tuple[dict, set[str]]:
        retrieved = {norm_url(self.SOURCE)}
        out = self.json(task=task, system=system, user=user, schema=schema, effort=effort)
        problems = check(out, retrieved) if check else []
        if problems:
            raise LLMError("fake draft failed its checks: " + "; ".join(problems))
        return out, retrieved

    def json(self, *, task: str, system: str, user: str, schema: dict, effort: str) -> dict:
        self.calls.append(Call(task, 0))
        if task == "mission":
            force = "FORCE: yes" in user
            why = re.search(r"Why: (.*)", user)
            why_text = why.group(1).strip() if why else ""
            if len(why_text) < 15 and not force:
                return {"acceptable": False, "follow_up": "What will you be able to do once you've learned this?",
                        "mission": {"title": "", "why": "", "success": [], "deadline": "", "constraints": [], "out_of_scope": []}}
            return {"acceptable": True, "follow_up": "", "mission": {
                "title": "Demo course", "why": why_text or "Demo learner wants to try the app.",
                "success": ["Explain the core idea to a colleague", "Apply it to one real case"],
                "deadline": "", "constraints": [], "out_of_scope": []}}
        if task == "map":
            needs = {1: [], 2: ["S1"], 3: ["S1"], 4: ["S2", "S3"], 5: ["S4"], 6: ["S4"], 7: ["S5", "S6"], 8: ["S7"]}
            return {"skills": [{"id": f"S{i}", "skill": f"do demo step {i}", "needs": needs[i]} for i in range(1, 9)],
                    "resources": [{"title": f"Demo source {i}", "url": f"https://example.com/{i}", "kind": "article",
                                   "use": "Placeholder from the fake provider."} for i in range(1, 4)]}
        if task == "item":
            n = len(self.calls)
            skill = re.search(r"Skill to test: (.*)", user)
            return {"question": f"Demo question {n}: {skill.group(1) if skill else ''}?",
                    "answer": "right", "rubric": ["Starts with the word right"]}
        if task == "grade":
            ans = re.search(r"<learner_answer>\n(.*?)\n</learner_answer>", user, re.S)
            ok = bool(ans and ans.group(1).strip().lower().startswith("right"))
            return {"correct": ok, "feedback": "Matches the key." if ok else "The key answer was: right."}
        if task == "review":
            items = re.findall(r'<saved_answer prompt="([^"]+)" when="([^"]+)"[^>]*>\n(.*?)\n</saved_answer>', user, re.S)
            answers = []
            for prompt, when, body in items:
                said = re.search(r"<learner_answer>\n(.*?)\n</learner_answer>", body, re.S)
                ok = bool(said and said.group(1).strip().lower().startswith("right"))
                answers.append({"prompt": prompt, "when": when, "judgment": "correct" if ok else "incorrect",
                                "right": "You named the key step." if ok else "",
                                "fix": "" if ok else "The key answer starts with the word right.",
                                "next_step": "Try one more item tomorrow." if ok else "Answer again, starting with right."})
            return {"answers": answers, "summary": "Demo review from the fake provider.",
                    "learning_record": {"trigger": "none", "title": "", "slug": "", "body": ""}}
        if task == "draft":
            num = re.search(r"Lesson number: (\d{4})", user)
            skill = re.search(r"Skill to teach: (S\d+[a-z]?): (.*)", user)
            label = re.search(r"Label: (.*)", user)
            n = num.group(1) if num else "0002"
            sid, stext = (skill.group(1), skill.group(2).strip()) if skill else ("S1", "demo skill")
            html = (
                "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Demo</title>"
                "<link rel=\"stylesheet\" href=\"../assets/course.css\"><link rel=\"stylesheet\" href=\"../assets/lesson-kit.css\">"
                "<script defer src=\"../assets/lesson-kit.js\"></script><script>alert('stripped')</script></head>\n"
                f"<body><main data-skill=\"{sid}\"><header><h1>{n} · {sid}: {stext}</h1>"
                f"<p class=\"meta\">{label.group(1).strip() if label else ''}</p></header>"
                f"<section><h2>Practice</h2><ol><li>Explain {stext} in one sentence.</li></ol>"
                "<form data-answer data-prompt=\"practice-1\" data-kind=\"practice\"><label for=\"a1\">Your answer</label>"
                "<textarea id=\"a1\"></textarea></form></section>"
                f"<section class=\"sources\"><h2>Sources</h2><ol><li id=\"s1\"><a href=\"{self.SOURCE}\">Fake source</a> #needs-verification</li></ol></section>"
                "</main></body></html>"
            )
            return {"slug": "demo-next-lesson", "title": f"{n} · {sid}: {stext}", "html": html,
                    "sources": [{"title": "Fake source", "url": self.SOURCE, "use": "Placeholder from the fake provider."}]}
        raise LLMError(f"fake provider has no canned reply for {task}")


def make_provider(name: str | None = None, model: str | None = None) -> Provider:
    name = (name or os.environ.get("TEACH_PROVIDER") or "anthropic").lower()
    model = model or os.environ.get("TEACH_MODEL")
    if name == "anthropic":
        return AnthropicProvider(model or DEFAULT_MODEL)
    if name == "bedrock":
        return BedrockProvider(model or DEFAULT_BEDROCK_MODEL)
    if name == "fake":
        return FakeProvider()
    raise LLMError(f"unknown provider {name!r}; use anthropic, bedrock or fake")
