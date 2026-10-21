# teach in Codex

**Install:** copy the whole `skill/` folder into your Codex skills folder as `teach/`. Recent versions read `~/.agents/skills/`; older ones read `~/.codex/skills/`.

| Need | Codex |
|---|---|
| Read and write the course folder | shell, `apply_patch` |
| Find sources for `RESOURCES.md` | web search when enabled; otherwise `curl` |
| Open an HTML lesson | shell: `open` or `xdg-open` |
| Serve HTML lessons with saved answers (optional) | shell: `teach-onboard serve <course folder>` (see the repo README) |

**Gaps:** the sandbox may block writes outside the launch directory. Start Codex in the course folder, or allow `$TEACH_HOME`.
