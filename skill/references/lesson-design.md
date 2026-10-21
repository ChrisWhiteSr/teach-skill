# Lesson and reference design

## The lesson file

The conversation is where teaching happens. The lesson file is the durable record of it, written at close (or before the session, if the runtime can show it). It lives at `lessons/NNNN-<skill-slug>.md`, where the number is the highest existing one plus one.

```md
# NNNN · {Skill ID}: {skill verb phrase}

Mission link: {one line on why this skill matters for MISSION.md}
Primary source: [{title}]({url}), {one line on what to read or watch and why it's the best}

## Worked example
{One complete example from the mission's world, solved step by step.}

## What you need to know
{Only the knowledge this skill needs. Short paragraphs, every claim cited inline: ([source](url)).}

## Practice
1. {item}
2. {item}

## Mastery check
1. {item}
…

## Answers
{Practice and check answers, kept at the bottom so the learner can work the items first.}

---
Stuck or curious? Ask your teacher agent. Follow-up questions are part of the lesson.
See also: [{related lesson}](NNNN-slug.md) · [{reference sheet}](../reference/slug.md)
```

Rules:

- **Small.** One skill and one tangible win, something the learner can do now that they couldn't before. Working memory is small; stay inside it.
- **Mission-shaped.** Examples and items come from the learner's world, not textbook generics.
- **Cited.** Every factual claim links to a source in `RESOURCES.md`. Citations are what make the lesson trustworthy enough to rely on later.
- **Linked.** Link to the lessons it builds on and to the reference sheets it feeds.

## Writing items

- **Recall, not recognition.** Prefer explain, compute, apply, predict, spot-the-error and "what would happen if…".
- **Multiple choice only in warm-ups.** Every option then has the same number of words, and characters where possible, and the same formatting. No clues in the shape of the answer.
- **The check is fresh.** Mastery-check items are new items, not practice items reworded. At least one transfers the skill to a case the learner hasn't seen.
- **Interleave in review.** Mix skills so the learner has to work out which one applies. Recognising the question type is part of the skill.

## Feedback

- **Fact-type item**: right or wrong, plus the correct answer.
- **Concept-type item**: why it's right or wrong, the rule it rests on, and if they missed it, one quick follow-up item on the same rule.

## HTML lessons

Use HTML when the runtime can open a browser and the skill benefits from interaction, or when `NOTES.md` says the learner prefers it. The content and rules above still apply.

- **Beautiful and printable.** Clean typography, generous whitespace, Tufte rather than dashboard. The learner will come back to these.
- **One course, one look.** The first HTML lesson creates `assets/course.css`, and every later lesson links it. Anything a second lesson could reuse (a quiz widget, a diagram helper, a simulator) goes into `assets/` as a component. Read `assets/` before writing a new lesson and build from what's there.
- **Feedback in the page.** Quiz widgets mark answers instantly and explain them. The same no-clues-in-format rule applies.
- **Open it for the learner** with `xdg-open` (Linux) or `open` (macOS) when the runtime has a shell and a display.

### The lesson kit

Every HTML lesson uses the lesson kit, a shared component that ships in this skill's `assets/` folder: `lesson-kit.js` and `lesson-kit.css`, plain files with no dependencies. With the first HTML lesson, copy both into the course's `assets/` folder (and `lesson-template.html` into `lessons/` as a starting point if the course has no HTML lesson yet). Later lessons link the course's copy. Read the kit's header comment before writing markup for it.

```html
<link rel="stylesheet" href="../assets/course.css">
<link rel="stylesheet" href="../assets/lesson-kit.css">
<script defer src="../assets/lesson-kit.js"></script>
<link rel="prev" href="0003-read-the-history.html">   <!-- previous lesson, if any -->
…
<main data-skill="S3">
```

The kit gives every lesson three things:

- **Answer boxes.** `<form data-answer data-prompt="check-1" data-kind="check">` with a `<label>` and a `<textarea>`. `data-kind` is `practice` (the default), `check` or `review`; `data-skill` on the form overrides the page's skill. Put the question in the same `<section>`, or in `data-prompt-text`. Use a box for every free-text recall item: practice, the mastery check (one box per item, at least five) and reviews.
- **Quizzes.** `<div data-quiz data-explanation="…">` holding `<button data-correct="true|false">` choices and a `<p role="status">`. Clicks are marked at once and logged as light evidence.
- **The finish panel**, added at the end of `<main>`: which answers are saved, "Finish and get feedback", the previous and next lessons, and a link to the course.

How it behaves depends on how the page is opened:

- **Served** by `teach-onboard serve <course folder>`: answers save to `answers/<lesson>.md` (`answers-format.md`), feedback appears under each box, and the finish panel runs the review and, when there is no next lesson yet, can draft one.
- **Opened as a file** (no server, or a chat-only runtime): the box keeps a draft in the browser, and "Copy for your teacher" copies the answer as an entry in the answers format. The learner pastes it into chat; the agent appends it to the answers file and judges it.

The kit never decides mastery. It collects answers and shows feedback; the rules in `SKILL.md` decide what they count for.

## Drafted lessons

When a model drafts the next lesson without a teacher in the conversation (the lesson runner's "Draft my next lesson", or an agent working ahead), the draft follows extra rules until a person has checked it.

- **Same template.** Copy the course's most recent lesson: its structure, classes, kit links and length. Teach the next skill in `MAP.md`, with the rules above.
- **Retrieved sources only.** Cite a page only if it was retrieved while drafting (a web search result or a fetched page) or is already in `RESOURCES.md`. Never cite from memory.
- **Tagged until checked.** Every source in the draft carries `#needs-verification`, and new sources are added to `RESOURCES.md` with the same tag. Whoever checks a source removes the tag in both places.
- **Labelled.** The header says `AI-drafted on <date>; sources not yet checked by a person`.
- **Stable facts only.** Leave out claims that go stale: current versions, prices, release status, rankings, "the latest". Teach what will still be true when the learner reviews it in 90 days.
- **New file only.** A draft is saved as a new `lessons/NNNN-<slug>.html`. It never replaces a lesson, and it has no scripts other than the kit.
- **Checking a draft.** Whoever checks it verifies each source against the claim it supports, removes the tags and the label, and adds `<link rel="next">` to the previous lesson (a drafter never edits an existing lesson).

## Reference sheets

Lessons are rarely reopened; reference sheets are. A sheet is the compressed essence of one or more lessons, built for a quick look up: syntax, formulas, procedures, decision trees, sequences, comparison tables. It lives in `reference/<slug>.md` (or `.html` alongside HTML lessons), stays to a page or two, and prints cleanly.

`GLOSSARY.md` is the one reference that every course gets. Once a term is in it, every lesson uses that term and no other.
