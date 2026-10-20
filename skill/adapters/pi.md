# teach in pi

**Install:** copy the whole `skill/` folder to `~/.pi/agent/skills/teach/`. Invoke with `/skill:teach`.

| Need | pi |
|---|---|
| Read and write the course folder | `read`, `write`, `edit` |
| Find sources for `RESOURCES.md` | a web skill if installed; otherwise `bash` with `curl` |
| Open an HTML lesson | `bash`: `open` or `xdg-open` |

**Gaps:** no built-in web search, so source curation is slower without a web skill. pi sessions are tied to a directory; start pi in the course folder.
