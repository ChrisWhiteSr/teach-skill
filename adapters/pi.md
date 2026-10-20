# Runtime adapter: teach in pi

## Installation

Place `SKILL.md` and the format documents together in the configured skill directory. The installation convention used by these notes is `~/.pi/agent/skills/teach/`; confirm the actual directory in your environment.

Use the runtime's supported invocation syntax, such as `/skill:teach` where available, from the learner's course workspace. Read its checkpoint, mission, and relevant learning records before resuming.

## Capability mapping

| Teaching need | Use when available |
| --- | --- |
| Read course state | File-reading tools |
| Maintain lessons, learning records, and checkpoint | File-writing or editing tools |
| Teach and give feedback | Conversation or artifacts in the chosen format |
| Create interactive HTML | File writing and a browser for verification |
| Find sources for the learner's subject | An available web tool, supplied files, or a suitable research integration |

Use the core skill's subject selection and lesson-format guidance. Do not assume web search or scheduling is present. Save a review prompt in the checkpoint when no requested scheduling integration is available; offer a portable checkpoint if file writing is unavailable.
