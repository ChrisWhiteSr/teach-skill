"""Model providers. Every call asks for JSON that matches a schema (structured outputs).

- anthropic: the Claude API. Credentials come from the environment the usual way
  (ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an `ant auth login` profile).
  Requests opt into server-side refusal fallbacks (`fallbacks: "default"`).
- bedrock: Claude on Amazon Bedrock through AWS credentials (profile and region from the environment).
- fake: canned answers for tests and offline demos. It does not teach anything.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

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

    def json(self, *, task: str, system: str, user: str, schema: dict, effort: str) -> dict: ...


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


class _ClaudeBase:
    name = "claude"

    def __init__(self, model: str):
        self.model = model
        self.calls: list[Call] = []

    def _create(self, **kwargs):  # pragma: no cover - provided by subclasses
        raise NotImplementedError

    def json(self, *, task: str, system: str, user: str, schema: dict, effort: str) -> dict:
        import anthropic

        t = time.monotonic()
        try:
            resp = self._create(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"format": {"type": "json_schema", "schema": schema}, "effort": effort},
            )
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
        usage = getattr(resp, "usage", None)
        self.calls.append(Call(task, int((time.monotonic() - t) * 1000),
                               getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0))
        return _parse(resp, task)


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


class BedrockProvider(_ClaudeBase):
    name = "bedrock"

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


class FakeProvider:
    """Deterministic stand-in for tests and offline demos. Answers starting with "right" are graded correct."""

    name = "fake"

    def __init__(self, model: str = "fake"):
        self.model = model
        self.calls: list[Call] = []

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
