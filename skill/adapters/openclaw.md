# teach in OpenClaw

**Install:** copy the whole `skill/` folder to `~/.openclaw/skills/teach/`.

| Need | OpenClaw |
|---|---|
| Read and write the course folder | `read`, `write`, `edit`, `apply_patch` |
| Find sources for `RESOURCES.md` | `web_search`, `web_fetch` |
| Deliver items in chat | One message per item; wait for the reply |
| Open an HTML lesson | `exec` with `open` or `xdg-open` |
| Serve HTML lessons with saved answers (optional) | `exec`: `teach-onboard serve <course folder>` (see the repo README) |
| Answers pasted from a lesson page | Append the block to `answers/<lesson>.md` as it is, then judge it (`references/answers-format.md`) |

**Gaps:** OpenClaw selects skills eagerly. The description limits triggers to learning over time; if it starts firing on one-off "explain X" questions, tighten the description.
