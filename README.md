# teach

A teaching skill for AI agents, a small web app that sets up your course, and a local lesson runner for its HTML lessons. You pick a subject, say why you want it, shape a map of the skills it takes, and answer a few adaptive questions. The app saves a course folder of plain Markdown files. Any agent with the skill installed (Claude Code, Codex, pi, Hermes, OpenClaw) then teaches from that folder, one short session at a time, and any other agent can pick up where the last one stopped.

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
| `answers/` | Answers you saved in an HTML lesson, with the teacher's feedback under each one |
| `assets/` | Shared lesson components, including the lesson kit |
| `.teach/` | `placement.json` (every placement question, answer and grade), and the lesson runner's `jobs.json` and `events.jsonl` |

Formats are specified in [`skill/references/`](skill/references/), so anything that writes them correctly can take part. Another app, a script or a person editing by hand would all work.

## The lesson runner

HTML lessons use the **lesson kit** (`skill/assets/lesson-kit.js` and `lesson-kit.css`, no dependencies). The skill copies it into the course's `assets/` folder with the first HTML lesson, and `skill/assets/lesson-template.html` is a starting point. The kit gives every lesson answer boxes for free-text recall items, warm-up quizzes and a finish panel. The markup is described in [`skill/references/lesson-design.md`](skill/references/lesson-design.md).

Serve a course folder to save answers and get feedback in the page:

```bash
uv run teach-onboard serve ~/teach-courses/git-version-control --install-kit --open
```

The course page opens at `http://localhost:8766/` and lists the lessons. In a lesson:

- **Save my answer** files the answer in `answers/<lesson>.md`, in the format of [`skill/references/answers-format.md`](skill/references/answers-format.md).
- **Finish and get feedback** runs a review in the background. The model judges each waiting answer (correct, partial or incorrect) and writes feedback under it, which then appears under the box. Code, not the model, applies the skill's rules to those judgments: a skill becomes mastered only through a full check of five or more first answers at 90% or better, quiz clicks never change `MAP.md`, and a learning record is written only for a corrected misconception, disclosed prior knowledge or a mission shift. `MAP.md` and `LOG.md` are updated as the skill's procedure says.
- **Draft my next lesson** appears on the last lesson once it has feedback. A model writes the next lesson for the next skill in `MAP.md`, from the latest lesson as its template, after web research. It may cite only pages it retrieved or sources already in `RESOURCES.md`; every source is tagged `#needs-verification` (new ones are added to `RESOURCES.md` the same way) and the page is labelled AI-drafted until a person checks it.

Jobs are kept in `.teach/jobs.json`, so closing the tab or restarting the server loses nothing. Run without a key using `--provider fake`. On Bedrock there is no web search, so drafts cite only `RESOURCES.md`.

Opened as a plain file, or in a runtime with no browser, the kit still works: drafts stay in the browser, and **Copy for your teacher** copies the answer as an entry in the answers format. Paste it to any agent with the skill; the agent files it and writes the feedback.

**Any agent can be the teacher.** The runner, a chat agent and a coding agent can all work on one course. Every writer hashes a shared file when it reads it and checks the hash before writing; if the file changed, it re-applies its change to the newer text instead of overwriting it (`skill/references/map-format.md`, "Writing shared files").

| Option | Default | What it does |
|---|---|---|
| `course` | required | The course folder (the one with `MAP.md`) |
| `--provider`, `--model` | `anthropic`, `claude-opus-5-5` | As for the onboarding app |
| `--host`, `--port` | `127.0.0.1`, `8766` | Where the runner listens |
| `--install-kit` | off | Copy the lesson kit into the course's `assets/` first |
| `--open` | off | Open the course page in your browser |

**Safety.** The runner listens only on localhost by default and has no login. It writes only inside the course folder and only to known files: `MAP.md`, `LOG.md`, `NOTES.md`, `RESOURCES.md`, `answers/*.md`, new numbered learning records, and its own `.teach/` state. It never edits an existing lesson. A drafted lesson is saved only as a new `lessons/NNNN-<slug>.html`, with every script except the kit removed, along with inline event handlers, frames and `javascript:` links. API requests must be JSON from a page the runner served (Host and Origin checks), so another website open in your browser cannot post answers or start model calls. A review is one model call; a draft is a few calls plus a handful of web searches and fetches.

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
| `skill/` | The agent skill: `SKILL.md`, `method.yaml`, reference formats, runtime adapters, and the lesson kit in `assets/` |
| `src/teach_onboard/` | The onboarding app (engine, course writer, model providers, prompts, server, static page) and the lesson runner (`runner.py`, `lesson_server.py`, `tutor.py`, `mastery.py`, `answers.py`, `files.py`, `jobs.py`) |
| `packs/` | Course packs |
| `tests/` | Engine, course files, rule sync, full flow, HTTP, the shape of the Claude API requests, and the lesson runner: answers format, confined and merged writes, script stripping, the mastery mapping, and its endpoints |

## License

MIT. See [LICENSE](LICENSE).
