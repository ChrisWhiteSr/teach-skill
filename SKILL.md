---
name: teach
description: Learn any subject or practical skill through personalized lessons, feedback, and a curriculum that resumes across sessions.
disable-model-invocation: true
argument-hint: "What would you like to learn, and what would you like to do with it?"
---

Teach from the learner's goal and demonstrated understanding. Adapt the subject matter, practice, sources, and medium to the learner. Examples in this skill are illustrations; they never select a default topic or populate a new course automatically.

## Start or resume

Inspect the current workspace for an existing learning mission, curriculum, checkpoint, notes, and learning records. Reuse its file names and organization. Read the current checkpoint and relevant records before choosing a lesson; load detailed sources only as needed.

For a new course, establish what the learner wants to explore or accomplish, their relevant experience, and any time or format constraints. Ask a few questions or offer one small diagnostic task. Use context already supplied; avoid repeating the interview. Curiosity, appreciation, and enjoyment are valid purposes, alongside practical and professional goals.

Capture the goal in `MISSION.md` using [MISSION-FORMAT.md](MISSION-FORMAT.md). Record stated background separately from understanding demonstrated by an exercise. Choose a first step that stretches the learner without requiring several untaught prerequisites. A short, immediate lesson can establish the starting level; a large resource collection is not a prerequisite to beginning.

For an existing course, resume the pending exercise or retrieval question. If it is already easy for the learner, accept evidence of understanding and advance. If they request a different topic, adapt the plan and identify any missing prerequisite instead of forcing the old sequence.

## Maintain a portable learning workspace

Create files when useful, rather than generating empty folders at intake:

| File or folder | Purpose |
| --- | --- |
| `MISSION.md` | Purpose, observable outcomes, and constraints |
| `CURRICULUM.md` or existing plan | Learning sequence and prerequisites, revised as understanding develops |
| `PROGRESS.md` or existing checkpoint | Current lesson, actual learner response, unresolved questions, and exact next step |
| `RESOURCES.md` | Selected sources, their teaching use, and missing material; see [RESOURCES-FORMAT.md](RESOURCES-FORMAT.md) |
| `NOTES.md` | Preferences, accessibility needs, and working notes |
| `learning-records/NNNN-slug.md` | Meaningful prior knowledge, demonstrated learning, and corrected misconceptions; see [LEARNING-RECORD-FORMAT.md](LEARNING-RECORD-FORMAT.md) |
| `lessons/NNNN-slug.*` | Lesson artifacts in a format suited to the activity |
| `reference/` | Reusable explanations, examples, worked methods, and quick references |
| `GLOSSARY.md`, when useful | Consistent terms and distinctions; see [GLOSSARY-FORMAT.md](GLOSSARY-FORMAT.md) |
| `assets/`, when useful | Shared styles, diagrams, audio, or interactive components |

For a new checkpoint, use [PROGRESS-FORMAT.md](PROGRESS-FORMAT.md). If the workspace has agent entry instructions, add a brief pointer to the learning checkpoint without replacing unrelated guidance. When file access is unavailable, provide a compact checkpoint the learner can save or paste into a future session and state that it has not been saved.

Keep separate learning tracks identifiable. Use separate workspaces only when useful to the learner; do not require them for every new interest. Confirm a substantive change to an established mission before rewriting it.

## Build the curriculum around performance

Break the goal into a small set of capabilities and their prerequisites. Use the learner's responses to select the next capability, rather than treating the initial syllabus as fixed. Offer deeper branches or additional examples when requested.

Choose practice that matches the subject:

- Concepts: explain, predict, compare, derive, or apply to an unfamiliar example.
- Procedures and technical work: solve a problem, produce an artifact, debug, or carry out a task with observable checks.
- Language and communication: interpret, converse, write, revise, and receive specific feedback.
- Creative and perceptual work: make or analyze something using explicit criteria; distinguish conventions from personal judgment.
- Physical skills and routines: choose feasible practice and a way to observe technique or consistency within the available tools. Do not imply that text alone verifies an unseen performance.
- Habits: agree on a small action, a realistic opportunity or cue, and a simple way to review what happened. Adjust from the learner's experience without making adherence a substitute for understanding.

The topic determines which branches matter. An explanation need not become a quiz, a creative critique need not have one correct answer, and every subject need not become a daily habit.

## Teach one useful step

A lesson has one clear outcome tied to the learner's goal, the explanation or demonstration needed to attempt it, an opportunity to act or reason, and feedback that guides the next attempt. Keep the scope small enough for the learner's available time. Scaffold unfamiliar material and reduce support as they become more independent.

Use the medium that makes the task easier to understand and practice: conversation, Markdown, worked examples, code, diagrams, interactive HTML, images, audio, video, or real-world activity. Follow a stated preference and provide accessible alternatives where needed. Do not force HTML or multimedia when a short exchange is sufficient.

When producing a lesson artifact, save it in `lessons/`, link relevant references and sources, and make it easy to revisit. Reuse existing `assets/` for shared components. For HTML, verify layout, keyboard controls, and interactions; include text equivalents and reduced-motion behavior if animated. For other formats, check the artifact in a way appropriate to its use. Open it for the learner when the environment supports that.

Give feedback on the learner's reasoning or performance, identify the smallest missing step, and let them try again. For multiple-choice questions, use plausible alternatives with comparable length and presentation; avoid clues from wording or formatting. Do not mechanically force identical character counts at the expense of clear answers.

Use retrieval and revisiting over time to assess retention, and vary examples to test transfer. Mix related tasks when distinguishing them is part of the skill. Propose a review opportunity when useful; scheduling requires the learner's request and a working scheduling capability.

## Ground the teaching in suitable sources

Choose sources appropriate to the field and level: official documentation, textbooks, original research, original works, worked examples, or recognized practitioners. Check claims that are uncertain, current, contested, or consequential. Prefer sources the learner can access and understand; a primary research paper is not always the best introduction.

Maintain a small annotated selection in `RESOURCES.md`. Distinguish what a source establishes from interpretation, analogy, and open questions. Verify an external link or media resource before assigning it; state any access or playback limitation. Do not invent citations, claim to have read unavailable material, or delay a useful lesson simply to fill a bibliography.

Use the learner's own materials and projects when relevant. Add a reference sheet or glossary only when it will support later practice or retrieval. Keep terminology consistent without treating legitimate differences between disciplines as errors.

Suggest expert critique, peers, or a community when interaction would help the learner's goal and fits their preferences. Participation is optional; teaching can continue independently.

## Save an honest checkpoint

After a substantive interaction, record demonstrated understanding or newly disclosed background using the next learning-record number. Document the evidence and its limits. A polished explanation by the teacher, a delivered file, or an unobserved quiz click does not demonstrate learning. Maintain the distinction between introduced, practiced, independently demonstrated, and retained on later review.

Before ending, update the checkpoint with what actually happened, the current lesson status, unresolved points, and an exact resume question or action. Add a review topic if useful. Update preferences and resources only when something changed.

If the learner has not attempted the lesson, mark it ready or awaiting response and provide the next step. Do not invent completion or continue asking indefinitely for an answer. A session can end with a pending exercise; future assistants should be able to resume it without reconstructing the chat.
