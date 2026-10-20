# teach in Claude Code

**Install:** copy the whole `skill/` folder to `~/.claude/skills/teach/` (all projects) or `.claude/skills/teach/` (one project). `SKILL.md` reads its `references/` from the same folder.

**Use:** "teach me X" triggers it, or type `/teach`.

| Need | Claude Code tool |
|---|---|
| Read and write the course folder | Read, Write, Edit |
| Find sources for `RESOURCES.md` | WebSearch, WebFetch |
| Open an HTML lesson | Bash: `open` (macOS) or `xdg-open` (Linux) |

**Gaps:** Claude Code has no scheduler of its own. For review reminders, use a scheduled task or another runtime with cron, and only when the learner asks.
