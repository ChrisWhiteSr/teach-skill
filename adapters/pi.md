# Runtime Adapter: teach → pi

## Compatibility

- Supported: yes
- Reason: pi has `read`, `write`, `edit`, and `bash` — sufficient to run the full teaching workflow. Particularly strong at precise file edits for maintaining MISSION.md/RESOURCES.md incrementally.

## Native Installation Target

`~/.pi/agent/skills/teach/SKILL.md` + format files alongside.

## Required Tool Mapping

| Canonical capability | Runtime-specific tool/instruction |
|---|---|
| Read workspace files | `read` tool |
| Write/edit lessons, records, glossary | `write` (new files) + `edit` (precise updates to existing) |
| Open lesson HTML for user | `bash` running `open`/`xdg-open` |
| Generate HTML lessons | model generation → `write` to `./lessons/*.html` |
| Curate RESOURCES.md | `bash` web fetch + `read` to evaluate; or web skill if installed |

## Import / Compile Steps

1. Copy `skill.md` + format files into `~/.pi/agent/skills/teach/`.
2. Invoke via `/skill:teach` in a session whose working directory is the teaching workspace.

## Safety Checks

- `writes-files` — confined to the workspace directory.

## Known Gaps

- pi has no built-in web search; RESOURCES.md curation needs a web skill installed or `bash` curl + `read`.
- pi sessions are per-directory; the teaching workspace should be a dedicated directory.
- No automatic scheduling — re-engagement requires a new session or external cron.
