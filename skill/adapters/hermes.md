# teach in Hermes

**Install:** copy the whole `skill/` folder to `~/.hermes/skills/teach/`.

Hermes suits short review sessions in a chat app, because it reaches the learner on their phone and has cron.

| Need | Hermes |
|---|---|
| Read and write the course folder | terminal, `read_file`, file write |
| Find sources for `RESOURCES.md` | `web_search` |
| Deliver items in chat | One message per item. Wait for the reply before marking it. |
| Review reminders (only if the learner asks) | `cronjob`: once a day, read each `$TEACH_HOME/*/MAP.md`; if any Next review date is today or earlier, message "N reviews due in {subject}. Reply 'review' to start." |

**Gaps:** chat apps can't show HTML, so teach in chat and write lesson files as Markdown. New skills that need a worked example usually go better at a desk.
