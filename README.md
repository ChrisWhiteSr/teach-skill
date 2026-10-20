# teach

A teaching skill for AI agents, and a small web app that sets up your course. You pick a subject, say why you want it, shape a map of the skills it takes, and answer a few adaptive questions. The app saves a course folder of plain Markdown files. Any agent with the skill installed (Claude Code, Codex, pi, Hermes, OpenClaw) then teaches from that folder, one short session at a time, and any other agent can pick up where the last one stopped.

The method follows Alpha School and its Timeback platform: find where the learner actually is, teach one skill at a time, advance only on demonstrated mastery, and bring each skill back before it fades.

## How it teaches

- **Placement first.** An adaptive check finds what you already know, so lesson one starts at your edge, not at chapter one.
- **One skill per lesson.** A skill is something you can do ("compute a number needed to treat"), not a topic ("statistics").
- **Recall, not recognition.** You produce answers: explain, compute, predict. Multiple choice is for warm-ups only.
- **Practice at 80–85% correct.** Easier than that and you're coasting; harder and something underneath is missing.
- **A 90% mastery gate.** A skill counts as learned when you get at least 90% on five or more fresh questions with no hints. "Makes sense" doesn't count.
- **Reviews first.** Each mastered skill comes back after 1, 3, 7, 16, 35 and 90 days, and every session opens with the reviews that are due.
- **Built around your reason.** Examples and practice come from the situation you described, not from textbook generics.

The gate and the review schedule do most of the work. Plenty of tutoring feels productive because explanations are fluent in the moment. The gate refuses to count that feeling, and the reviews test whether the skill survived a week. Everything else (placement, small skills, practice difficulty) exists so you reach the gate quickly and pass it honestly.

## Quick start

You need Python 3.10 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/ChrisWhiteSr/teach-skill
cd teach-skill
export ANTHROPIC_API_KEY=...        # or run `ant auth login` once
uv run teach-onboard --open
```

The page opens at `http://localhost:8765`. When you finish, it shows the course folder it saved (by default `~/teach-courses/<subject>/`). Install the skill in your agent (below), open the agent in that folder, and say "continue my course".

To look around without an API key, run `uv run teach-onboard --provider fake --open`. The fake provider returns canned questions, so it only shows how the flow works.

## The onboarding app

| Option | Default | What it does |
|---|---|---|
| `--provider` | `anthropic` | `anthropic` (Claude API), `bedrock` (Claude on Amazon Bedrock) or `fake` |
| `--model` | `claude-opus-5-5` | Any Claude model id. On Bedrock the default is `us.anthropic.claude-opus-5-5`. |
| `--courses-dir` | `$TEACH_HOME`, else `~/teach-courses` | Where course folders are saved |
| `--packs-dir` | none | An extra folder of course packs |
| `--host`, `--port` | `127.0.0.1`, `8765` | Where the app listens |

**Claude API.** Credentials come from `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or an `ant auth login` profile. Requests opt into server-side refusal fallbacks, so if a safety classifier declines a request the API retries it on a fallback model instead of failing.

**Amazon Bedrock.** Install the extra and point it at your AWS profile and region:

```bash
AWS_PROFILE=my-profile AWS_REGION=us-east-1 uv run --extra bedrock teach-onboard --provider bedrock
```

`TEACH_AWS_PROFILE` overrides `AWS_PROFILE` if you keep a separate profile for model access.

**What a session costs.** Expect about 30 model calls: one to review your mission, one to draft the map, and one each to write and grade every placement question. While you answer, the app writes the next question for both outcomes (right or wrong) so you aren't kept waiting. That makes about 1.5 times as many question-writing calls as questions asked.

**Privacy.** The app runs on your machine and listens only on localhost. It has no login, so think before you pass `--host`. Your answers go to the model provider you chose, and the course is written only inside the courses folder. It never overwrites a folder that already has files in it.

## Install the skill

Copy the whole `skill/` folder into your agent's skills folder and name it `teach`. `SKILL.md` reads its reference files from the same folder.

| Agent | Folder |
|---|---|
| Claude Code | `~/.claude/skills/teach/` |
| Codex | `~/.agents/skills/teach/` (older versions: `~/.codex/skills/teach/`) |
| pi | `~/.pi/agent/skills/teach/` |
| Hermes | `~/.hermes/skills/teach/` |
| OpenClaw | `~/.openclaw/skills/teach/` |

For example, `cp -r skill ~/.claude/skills/teach`. Notes for each runtime are in [`skill/adapters/`](skill/adapters/). The skill also works without the app: say "teach me X" and the agent runs the mission interview and placement in chat.

## The course folder

| File | Holds |
|---|---|
| `MISSION.md` | Why you're learning this and what success looks like |
| `MAP.md` | Every skill, its prerequisites, your status and the next review date. This is the file every agent reads first. |
| `LOG.md` | One line per session: date, agent, minutes, XP, scores |
| `RESOURCES.md` | Sources and communities. Sources the model suggested are tagged `#needs-verification` until a lesson checks them. |
| `lessons/`, `reference/`, `GLOSSARY.md`, `learning-records/` | Written by the agent as you go |
| `.teach/placement.json` | Every placement question, answer and grade |

Formats are specified in [`skill/references/`](skill/references/), so anything that writes them correctly can take part. Another app, a script or a person editing by hand would all work.

## How placement works

Placement starts in the middle of the map. A correct answer is confirmed with a second question on the same skill, and then placement jumps up the map. A miss steps down toward that skill's prerequisites. Two correct answers place a skill as mastered, and its prerequisites count as known by inference; their first review, the next day, confirms or demotes them. A skill above a gap stays "to learn". Placement stops after 12 questions, or sooner once every skill is settled.

At the end you see every question, your answer, the model answer and the grade. If the grader got one wrong you can ask for a regrade before saving.

The placement rules live in code ([`src/teach_onboard/engine.py`](src/teach_onboard/engine.py)), not in a prompt. The model writes questions and grades answers, and code decides where you start. The numbers come from [`skill/method.yaml`](skill/method.yaml), which the skill states in prose too; a test fails if the two disagree.

## Course packs

A pack fixes the skill map and sources for a known course, and can include a question bank so placement doesn't rely on generated questions. [`packs/git-basics/pack.yaml`](packs/git-basics/pack.yaml) is a complete example. Put your own packs in a folder and pass `--packs-dir`.

## Where the method comes from

- [Timeback principles](https://docs.timeback.com/beta/about-timeback/principles): the 90% mastery gate, 1 XP per focused minute, no XP below 80% accuracy, recall over recognition.
- [Alpha School on AI and gamification](https://alpha.school/blog/how-ai-and-gamification-transform-learning-at-alpha-school/): 25-minute focus blocks, the 80–85% difficulty band, the "waste meter" for unproductive habits.
- [Math Academy](https://mathacademy.com/how-it-works) and Justin Skycak's [Fractional Implicit Repetition](https://justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/): the skill map with prerequisites, and counting practice on advanced skills as review of their foundations.

Alpha School's outcome claims come from the school itself; I haven't found an independent evaluation. The design choices here are reasoned from published principles, not proven by a trial. [`skill/references/method.md`](skill/references/method.md) maps each mechanism to its source and lists what was left out on purpose: camera-based attention tracking, cash rewards, and the fixed two-hour day.

This skill began as Matt Pocock's `teach` skill in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). The knowledge, skills and wisdom framing, and the course-file formats, come from there.

## Development

```bash
uv run pytest
```

| Path | Contents |
|---|---|
| `skill/` | The agent skill: `SKILL.md`, `method.yaml`, reference formats, runtime adapters |
| `src/teach_onboard/` | The onboarding app: engine, course writer, model providers, prompts, server, static page |
| `packs/` | Course packs |
| `tests/` | Engine, course files, rule sync, full flow, HTTP, and the shape of the Claude API request |

## License

MIT. See [LICENSE](LICENSE).
