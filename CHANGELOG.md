# Changelog

## 0.3.0 (2026-10-21)

- **Answers in the lesson page.** New `skill/references/answers-format.md`: answers saved from an HTML lesson go to `answers/<lesson>.md`, newest last, and the teacher writes feedback under each answer with a fixed `**Teacher feedback** (...): **Judgment: correct|partial|incorrect.**` marker that the page reads back.
- **Lesson kit.** `skill/assets/lesson-kit.js` and `lesson-kit.css`: answer boxes, quiz capture and a finish panel for every HTML lesson. Works served by the lesson runner and as a plain file ("Copy for your teacher"). `lesson-template.html` is a starter lesson.
- **Lesson runner.** `teach-onboard serve <course folder>` serves a course's lessons on localhost, saves answers, and runs the review and the next-lesson draft as background jobs that survive a restart.
- **Mastery rules hold.** A review's judgments are evidence under the existing rules: the 90% gate needs a full check of five or more first answers, partial counts as a miss, quiz clicks never change `MAP.md`, and learning records are written only for their existing triggers.
- **Drafted lessons with provenance.** A drafted lesson copies the latest lesson's template, cites only retrieved pages or `RESOURCES.md`, tags every source `#needs-verification`, avoids current-status claims, and is labelled AI-drafted until a person checks it.
- **Any agent can be the teacher.** `map-format.md` and `SKILL.md` now say to hash shared files on read and, if one changed before writing, re-read and merge instead of overwriting. The runner does the same in code.
- `SKILL.md` gains test scenarios 9 to 14 and records its version in its frontmatter. Runtime adapters note serving lessons and filing pasted answers.

## 0.2.0

- Rebuilt the skill on mastery learning (placement, one skill per lesson, the 90% gate, spaced review) and added the browser onboarding app.

## 0.1.0

- First public version of the teach skill and its course-file formats.
