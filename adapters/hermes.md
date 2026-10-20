# Runtime Adapter: teach → hermes

## Compatibility

- Supported: yes
- Reason: Hermes has terminal/shell, file R/W, web research, and cron for scheduled re-engagement. Well-suited to the multi-session, stateful nature of `teach`.

## Native Installation Target

`~/.hermes/skills/teach/SKILL.md` + format files. Or load directly from the vault via the obsidian skill.

## Required Tool Mapping

| Canonical capability | Runtime-specific tool/instruction |
|---|---|
| Read workspace files | `terminal` cat / `read_file` |
| Write lessons, records | file-write via terminal |
| Open lesson HTML for user | `terminal` running `open`/`xdg-open` |
| Generate HTML lessons | model generation → terminal file write |
| Curate RESOURCES.md | `web_search` + research skills (arxiv, pubmed, blogwatcher) |
| Scheduled re-engagement (spaced repetition) | `cronjob` tool to open a teaching session on a cadence |

## Import / Compile Steps

1. Copy `skill.md` + format files into `~/.hermes/skills/teach/`.
2. Optionally set a cron job to re-engage the teaching workspace on a spaced-repetition schedule.

## Safety Checks

- `writes-files` — confined to the workspace directory.

## Known Gaps

- Hermes subagents are synchronous; long lesson authoring should stay in the main session.
- Hermes cannot display HTML itself — the user must open the generated lesson file.
