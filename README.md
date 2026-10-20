# Teach

A reusable AI teaching skill for learning a subject over multiple sessions in a local workspace.

The skill grounds lessons in the learner's mission, assesses prior understanding, produces short interactive HTML lessons and printable references, curates trusted sources, and records demonstrated learning so future sessions can resume.

## Install

Copy this repository's contents into your assistant's skill directory as `teach/`, keeping `SKILL.md`, the format documents, and supporting files together. For a Codex installation using the shared user skills directory, the entry point is `~/.agents/skills/teach/SKILL.md`.

Invoke `teach` using your assistant's skill picker or supported command syntax while working in the folder where you want your course stored. Invocation syntax varies by runtime. Runtime-specific adapter notes are in `adapters/`.

## Teaching workspace

The skill creates or maintains these files in the learner's current workspace:

| Path | Purpose |
| --- | --- |
| `MISSION.md` | The learner's concrete purpose and success criteria |
| `RESOURCES.md` | Annotated trusted sources and remaining source gaps |
| `NOTES.md` | Learning preferences and working notes |
| `learning-records/` | Prior knowledge, demonstrated understanding, and corrected misconceptions |
| `lessons/` | Short interactive HTML lessons |
| `reference/` | Printable references and glossaries |
| `assets/` | Shared styling and reusable interactive components |

When resuming, ask the assistant to read the mission, notes, and learning records before choosing the next lesson. Preserve the distinction between material delivered and understanding demonstrated.

## Repository contents

- `SKILL.md`: teaching workflow and principles.
- `*-FORMAT.md`: mission, resources, glossary, and learning-record formats.
- `adapters/`: Hermes, OpenClaw, and pi runtime notes.

This repository contains the reusable skill. Individual course content and learner records live in their respective teaching workspaces.
