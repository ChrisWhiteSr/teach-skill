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

## Reference sheets

Lessons are rarely reopened; reference sheets are. A sheet is the compressed essence of one or more lessons, built for a quick look up: syntax, formulas, procedures, decision trees, sequences, comparison tables. It lives in `reference/<slug>.md` (or `.html` alongside HTML lessons), stays to a page or two, and prints cleanly.

`GLOSSARY.md` is the one reference that every course gets. Once a term is in it, every lesson uses that term and no other.
