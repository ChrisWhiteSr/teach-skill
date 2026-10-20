# Runtime Adapter: teach → openclaw

## Compatibility

- Supported: yes
- Reason: OpenClaw has filesystem read/write/edit, shell exec for opening lesson files, and can generate HTML. No special infrastructure needed.

## Native Installation Target

`~/.openclaw/workspace/skills/teach/SKILL.md` + format files alongside.

## Required Tool Mapping

| Canonical capability | Runtime-specific tool/instruction |
|---|---|
| Read workspace files (MISSION.md, learning-records/) | `read` tool on vault/workspace path |
| Write lessons, records, glossary | `write` / `edit` / `apply_patch` tools |
| Open lesson HTML for user | `exec` running `open`/`xdg-open`, or shell command |
| Generate HTML lessons | Model generation → `write` to `./lessons/*.html` |
| Curate RESOURCES.md from web | `web_search` + `web_fetch` to evaluate sources |

## Import / Compile Steps

1. Copy `skill.md` + all format files (`*-FORMAT.md`) into the OpenClaw skill folder.
2. No content changes needed — the skill is runtime-agnostic.
3. Ensure the working directory when invoked is the teaching workspace.

## Safety Checks

- `writes-files` — creates/edits files in the current workspace directory only.
- Lessons are HTML; no script execution by default.

## Known Gaps

- OpenClaw's mandatory skill selection may load this on any "learn" mention; verify the description trigger is specific enough.
- No automatic spaced-repetition scheduling — the agent must re-engage across sessions manually or via cron.
