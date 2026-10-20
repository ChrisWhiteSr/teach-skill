# Teach

A reusable AI teaching skill for any subject: concepts, practical skills, creative work, languages, or habits. It adapts to the learner's goal and experience, gives feedback on real attempts, and saves enough context for future sessions to resume.

## What it adapts

| Learning goal | Possible lesson | Evidence of progress |
| --- | --- | --- |
| Understand a scientific field | Trace a mechanism and interpret a study | Explain what the evidence supports and apply it to a new case |
| Learn mathematics | Work through a problem with gradually reduced support | Solve and explain an unfamiliar problem |
| Learn a language | Listen, converse, and revise an answer | Communicate meaning in a new situation |
| Improve writing or music | Create a short piece and revise from critique | Explain and apply a deliberate improvement |
| Learn programming or a craft | Build, debug, repair, or perform a small task | Produce a working result and explain the method |
| Study history or philosophy | Compare original sources and interpretations | Make an argument grounded in the material |
| Build a practice habit | Choose a feasible action and review what happened | Report consistency and adjust obstacles separately from skill mastery |

These illustrate possible uses, not a predefined course. The skill selects the content, examples, sources, and exercises from each learner's topic. Lessons can use chat, Markdown, worked examples, code, diagrams, HTML, audio, video, or real-world activity. Multimedia and community participation are optional.

## Install and use

Copy the repository's contents into your assistant's skill directory as `teach/`, keeping `SKILL.md` and the format documents together. In the shared user skills directory used by this Codex installation, the entry point is `~/.agents/skills/teach/SKILL.md`.

Invoke `teach` through your assistant's skill picker or supported syntax in the workspace where you want your course stored. Invocation syntax varies by runtime; notes for additional runtimes are in `adapters/`.

Possible starting requests:

- "Teach me enough statistics to interpret a research paper. I understand algebra."
- "Help me learn conversational Italian through short practice sessions."
- "I want to understand medieval history using original sources."
- "Help me build a regular drawing practice and improve from critique."
- "Resume my course from the saved checkpoint."

The skill first uses available context and a short diagnostic, then chooses a useful next step. It does not require a long intake or a complete bibliography before teaching can begin.

## Persistent learning state

| Path | Purpose |
| --- | --- |
| `MISSION.md` | Purpose, outcomes, and constraints |
| `CURRICULUM.md` or existing plan | Learning sequence and prerequisites |
| `PROGRESS.md` or existing checkpoint | Current lesson status and exact next action |
| `RESOURCES.md` | Annotated sources and practice materials |
| `NOTES.md` | Preferences and working notes |
| `learning-records/` | Reported background and evidence of understanding |
| `lessons/` | Lesson artifacts in suitable formats |
| `reference/` and optional `GLOSSARY.md` | Reusable references and vocabulary |
| Optional `assets/` | Shared styles, media, and interactive components |

Existing workspace conventions are reused. Files and folders are created when needed. Material introduced, an exercise attempted, and independent understanding demonstrated are tracked separately. Quiz interactions are not automatically available to the AI.

To resume with an assistant that can access the workspace, ask:

> Read my learning mission, progress checkpoint, notes, and relevant learning records. Resume at the saved next exercise and update the checkpoint when we finish.

Automatic file discovery varies by assistant. When file access is unavailable, the skill can provide a portable checkpoint to save or paste into a later session.

## Repository contents

- `SKILL.md`: the adaptive teaching workflow.
- `*-FORMAT.md`: concise templates for missions, resources, terminology, learning records, and progress.
- `adapters/`: runtime integration notes.

Individual courses and learner records belong in their teaching workspaces. This repository distributes the reusable skill and its templates.
