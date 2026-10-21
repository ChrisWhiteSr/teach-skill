# Answers file format

An HTML lesson can ask for free-text answers in the page. Each saved answer goes into a Markdown file in the course folder, and the teacher (any agent, or a person) writes feedback directly under it. The lesson page reads the same file back, so the learner sees the feedback under the box where they typed. One file per lesson, one format for every runtime.

## Where it lives

`answers/<lesson-file-stem>.md`. The lesson `lessons/0004-commit-chosen-changes.html` saves to `answers/0004-commit-chosen-changes.md`. Create the folder when the first answer is saved.

## Structure

```md
# Answers: 0004 · S3: commit only the changes you choose

Answers saved from `lessons/0004-commit-chosen-changes.html`, newest last.
Teachers: write feedback under an answer by replacing its waiting line. The format is in the teach skill's `references/answers-format.md`.

## Answer · check-1 · 2026-10-21 14:05

Skill: S3 · Kind: check

**Prompt**

> You changed app.py and notes.txt but only want app.py in the next commit. Which commands do you run?

**Answer**

> git add app.py
> git commit -m "Fix the login check"

*Waiting for teacher feedback.*

## Answer · check-2 · 2026-10-21 14:07

Skill: S3 · Kind: check

**Prompt**

> What makes a commit message useful to someone reading the history a year from now?

**Answer**

> It says what changed.

**Teacher feedback** (2026-10-21, claude-code): **Judgment: partial.**

What you got right: a summary of what changed is the first thing a reader needs.

What to add or fix: the reader a year from now also needs the reason. A body line saying why the change was made is what makes the history useful.

Smallest next step: rewrite "Fix the login check" as a message with a one-line summary and a one-sentence reason.
```

### The parts

- **Heading**: `## Answer · <prompt id> · <YYYY-MM-DD HH:MM>`. The prompt id comes from the box's `data-prompt` (lowercase letters, digits, hyphens). Prompt id and time together identify an entry. If a second answer to the same prompt lands in the same minute, the time gets seconds (`14:05:31`).
- **Item line**: `Skill: <ID> · Kind: <practice | check | review>`, copied from the box. It tells the teacher how the answer counts (below).
- **Prompt**: the question as the learner saw it, quoted with `> `.
- **Answer**: the learner's words exactly, quoted with `> `. Never edit them.
- **Waiting line**: `*Waiting for teacher feedback.*` until someone gives feedback.
- **Feedback**: replaces the waiting line. It opens with `**Teacher feedback** (<date>, <teacher>[, <model>]): **Judgment: <correct | partial | incorrect>.**`, then up to three paragraphs that start `What you got right:`, `What to add or fix:` and `Smallest next step:`. Leave out a paragraph that has nothing to say. Each paragraph stays one paragraph (no blank lines inside it), so the page can parse it back.

## Rules

- **Newest last.** A new answer is a new entry appended at the end, even for a prompt answered before. Earlier entries and their feedback stay as they were.
- **Feedback goes in place.** Replace only the waiting line of the entry you judged. Never move, merge or reword entries.
- **One judgment per entry.** `correct` means the answer shows the rule in the learner's own words. `partial` means part of it is right and at least one key point is missing or wrong. `incorrect` means the central point is missing. Name what is right specifically, name what is missing precisely, and give the smallest step that would close the gap.
- **Check before you write.** Other agents may write the same file. Follow "Writing shared files" in `map-format.md`: hash on read, compare before writing, and re-apply your edit to the newer text if it changed.
- **Pasted answers count too.** In a chat-only runtime the learner can press "Copy for your teacher" in the page and paste the block. It is already an entry in this format: append it to the answers file, then judge it.

## How answers count

A saved answer is a recall item, judged like an answer given in chat. The rules in `SKILL.md` decide what it is worth.

- **Partial is a miss when scoring.** A check of 5 with 4 correct and 1 partial scores 4/5.
- **Only a first answer is fresh.** For `check` and `review` items, the first answer to each prompt is the one that counts. An answer given after the learner has seen feedback on that prompt is practice.
- **Check items.** When every `check` box for a skill in the lesson has a judged first answer, and there are at least five of them, they form a mastery check. At 90% or above the skill is `mastered` and its first review is due tomorrow; below that it stays `learning` and each miss goes under Missed items in `MAP.md`. Fewer than five check boxes never make a mastery check, whatever the score.
- **Review items.** For a skill that is `mastered`, a judged `review` answer is a review: all correct moves it one step along the schedule; any miss sends it back to `learning` with the missed item recorded.
- **Practice items.** Evidence of learning only. A `new` skill becomes `learning`. Nothing becomes `mastered` from practice.
- **Quiz clicks are light evidence.** The page may log multiple-choice clicks (in `.teach/events.jsonl` when served). They are recognition, so under rule 3 they never change a status in `MAP.md`.
- **Learning records only for their triggers.** A judged answer earns a record only when it corrects a misconception, discloses prior knowledge or shifts the mission (`learning-record-format.md`). A correct answer on its own is a status change in `MAP.md`, not a record.
