---
name: teach
description: Teach someone a subject over many sessions with mastery learning (placement check, short focused lessons, a 90% mastery gate, spaced review). Use when someone says teach me, wants to learn or get good at a subject over time, asks to continue their course, or has reviews due.
---

# Teach

## Purpose

Run a course for one learner on one subject, across many sessions and many agents. The method is the one Alpha School runs on its Timeback platform: find where the learner actually is, teach one skill at a time in a short focused block, advance only on demonstrated mastery, and bring each mastered skill back before it fades. The course lives in plain files, so any agent can pick it up where the last one stopped.

Paths under `references/` are relative to the folder this file is in. `references/method.md` has the research behind every number here and what was deliberately left out. Read it when the learner asks why, or before bending a rule.

## When To Use

- "Teach me X", "I want to get good at X", "help me learn X properly".
- "Continue my course", "what's next in X", "quiz me on what I've learned".
- A course folder has reviews due.

## When Not To Use

- A one-off explanation or definition. Answer it; no course needed.
- Designing a class for a group. `references/method.md` is useful background, but this procedure is built for one learner.

## The rules

These hold in every session, in every runtime. Each one names the behaviour to reach for when in doubt.

1. **Placement before teaching.** Diagnose where the learner is. Never assume they start at the beginning.
2. **One skill per lesson.** A skill is something the learner can *do*, written as a verb phrase: "compute a logistic score by hand", not "logistic regression".
3. **Recall, not recognition.** Practice and checks make the learner produce the answer: explain, compute, apply, predict. Multiple choice is allowed only in warm-ups, and then every option has the same length and format.
4. **Practice in the 80–85% band.** Above about 85% correct, make items harder. Below about 80%, make them easier or look for a missing prerequisite.
5. **Mastery gate at 90%.** A skill is mastered only when the learner scores at least 90% on a mastery check of five or more fresh recall items, with no hints. That means 5/5, 9/10 or better. Self-report ("got it", "makes sense") is never evidence.
6. **Holes before new ground.** When a miss traces to a missing prerequisite, add it to the map, teach it, then come back.
7. **Reviews first.** Every session opens with the reviews that are due, before anything new.
8. **Feedback now.** Mark each answer immediately. For a wrong answer, explain why and give the correct rule before the next item, so the wrong rule never settles.
9. **Mission-shaped.** Every example and practice item comes from the learner's own world in `MISSION.md`, not from textbook generics.
10. **Sources over memory.** Facts the learner will rely on come from `RESOURCES.md` and are cited in the lesson. Do not teach from parametric memory alone.

## Course folder

**Where it lives.** If the learner names a folder, or a folder already holds a `MISSION.md` for this subject, use that. Otherwise create `<courses home>/<subject-slug>/`. The courses home is `$TEACH_HOME` if that is set, and `~/teach-courses/` if not. One home for every course means any agent the learner uses can find it.

| File | Holds | Format (read before first write) |
|---|---|---|
| `MISSION.md` | Why the learner wants this, and what success looks like | `references/mission-format.md` |
| `MAP.md` | Every skill, its prerequisites, status and review schedule. The single source of truth for what to teach next. | `references/map-format.md` |
| `LOG.md` | One line per session: date, agent, minutes, XP, scores | `references/map-format.md` |
| `RESOURCES.md` | Trusted sources and communities | `references/resources-format.md` |
| `GLOSSARY.md` | Terms the learner can already use correctly | `references/glossary-format.md` |
| `learning-records/` | Non-obvious insights: misconceptions fixed, prior knowledge claimed, mission shifts | `references/learning-record-format.md` |
| `lessons/` | One file per lesson: what was taught, practice and check items | `references/lesson-design.md` |
| `reference/` | Cheat sheets the learner will reopen | `references/lesson-design.md` |
| `NOTES.md` | The learner's stated preferences about how they're taught | free-form |

## Procedure

### 1. Orient (every session)

Read `MISSION.md`, `MAP.md`, `NOTES.md` and the last five lines of `LOG.md`.

- No course folder: go to step 2.
- A folder made by the onboarding app: setup and placement are already done, so skip step 2. Sources it wrote are tagged `#needs-verification`; check a source before a lesson cites it, then remove the tag.
- An older course folder that has `lessons/` or `learning-records/` but no `MAP.md`: build `MAP.md` from the mission and the records. Mark nothing mastered without evidence in a record. Then run a placement check (step 2d) on whatever the records claim, and continue.

**Done when** you can state the mission in one sentence, list the reviews due today, and name the next skill: the first skill in `MAP.md` that is not mastered and whose prerequisites all are.

### 2. Set up a new course (first session only)

a. **Mission.** Ask why they want this, what they will be able to do when it's done, by when, and how much time a session can take. Push back on vague answers. Write `MISSION.md` and confirm it with the learner.

b. **Resources.** Find three to seven high-trust sources and write `RESOURCES.md`.

c. **Map.** Draft 8–20 skills, from the foundations the mission depends on up to its success criteria, each with its prerequisites. Show the learner a short version.

d. **Placement check.** Adaptive, about 6–12 recall items, one at a time. Tell the learner first that "I don't know" is a useful answer and that guessing only puts them in the wrong place. Start mid-map: a right answer jumps up a level, a miss steps down to that skill's prerequisites. A skill counts as mastered by placement only after two correct, unaided items on it. Its prerequisites then count as mastered by inference, with a first review due the next day that confirms or demotes them. Skills they partly know become `learning`. Untested skills above where they stopped stay `new`.

**Done when** `MISSION.md` is confirmed, `RESOURCES.md` has at least three annotated sources, every skill in `MAP.md` has a status set from placement evidence, and the learner has been told where they start. Placement can fill the whole first session; that is fine.

### 3. Run the session: one focused block

Default 25 minutes, or whatever `MISSION.md` says. Ask one item at a time and wait for the answer. Never put the answer in the same message as the question.

a. **Reviews (about 5 minutes).** Every due skill, mixed together, one or two recall items each, no hints. A pass moves the skill one step along the schedule. A miss sets it back to `learning`, and it joins today's practice if there is time. Cap reviews at eight items per session, most overdue first.

b. **Teach the next skill (about 15 minutes).**
   - Start with a worked example from the mission's world.
   - Give only the knowledge this skill needs, with citations. Hand the learner something to do within roughly 300 words.
   - Guided practice: the learner attempts and you give feedback right away, holding them in the 80–85% band.
   - Independent practice: withdraw help step by step.

c. **Mastery check (about 5 minutes).** At least five fresh recall items, not repeats from practice, with at least one that applies the skill to a new case from the mission. No hints. Score it. At 90% or above the skill is `mastered` and its first review is due tomorrow. Below 90% it stays `learning` and the missed items are recorded in `MAP.md`.

**Done when** every due review was asked, the check was scored, and the learner has seen the score.

### 4. Close and record (every session)

- Update `MAP.md`: statuses, last date, next review, schedule step, best check score, missed items.
- Append a line to `LOG.md`. XP is one per focused minute. A session whose overall accuracy fell below 80% earns zero XP.
- Write the lesson file to `lessons/`. If the skill produced something worth reopening (a formula, a procedure, a diagram), create or update a sheet in `reference/`. Add to `GLOSSARY.md` only terms the learner used correctly today.
- Write a learning record only for a corrected misconception, disclosed prior knowledge, or a mission shift.
- Tell the learner, in four lines or fewer: what they mastered or what's still open and why; progress (skills mastered out of the total, XP this week, days in a row); when the next review is due; what comes next.

**Done when** `MAP.md` and `LOG.md` both reflect this session and the learner has the date of their next review. Skip this and the next agent starts blind, so the session is not finished until it's done.

## Review schedule

After mastery, reviews fall due 1, 3, 7, 16, 35 and 90 days apart, then every 180 days. Each passed review moves the skill one step. A missed review sends it back to `learning`: reteach briefly, then run a fresh mastery check.

**Implicit review.** When a mastery check on one skill correctly exercises a prerequisite, that counts as a review of the prerequisite and moves it one step. Higher skills keep the foundations fresh without separate drilling.

## Anti-patterns: the waste meter

Name these out loud when you see them, in a sentence, without lecturing.

Learner:
- Says "got it" or asks to skip: reply "show me" with one recall item.
- Answers fast and wrong, or hedges ("B, maybe?"): that's guessing. Ask for the reasoning before you mark it.
- Asks for the answer before trying: ask for a first attempt. Any attempt counts.
- Wants a skill whose prerequisites aren't mastered: show the dependency and offer a quick placement check on the prerequisite. If they pass it, go ahead.

Teacher (you):
- More than about 300 words before the learner does something.
- More than one question in a message.
- An answer given away by the wording, length or formatting of the question.
- Mastery marked on recognition items, hinted answers or the learner's say-so.
- A learning record written for material that was only covered.

## Where lessons appear

The conversation is the lesson. That works in every runtime, including chat apps such as Telegram or Slack. Lesson files default to Markdown. Use HTML when the runtime can open a browser and the skill benefits from interaction (a quiz widget, a simulator), or when `NOTES.md` says the learner prefers it. The rules for both are in `references/lesson-design.md`.

## Safety

- Writes only inside the course folder.
- No external actions. Don't set up reminders or scheduled jobs unless the learner asks; `adapters/` says how for each runtime.

## Tests

Run these scenarios after any edit to this skill. Each describes the behaviour a correct run shows.

1. Fresh "teach me X": a mission interview comes first. No lesson is given before `MISSION.md` is confirmed and placement has run.
2. After an explanation the learner says "yep, makes sense": the agent asks a recall item and does not mark anything mastered.
3. A mastery check scores 4/5: the skill stays `learning`, and the missed item is written to `MAP.md`.
4. A session starts with two reviews due: both are asked before any new material.
5. Opened on an older course folder with lessons but no `MAP.md`: the agent builds `MAP.md` and runs placement on the earlier lessons' material before teaching anything new.
6. In a chat app, "time for my review": reviews run one item per message, with no HTML, and `MAP.md` and `LOG.md` are updated.
7. A practice run at 10/10: the next items get harder.
8. Opened on a folder from the onboarding app: no mission interview or placement; the first session teaches the next skill in `MAP.md`.
