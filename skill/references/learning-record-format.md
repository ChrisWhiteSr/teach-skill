# Learning Record Format

Learning records live in `./learning-records/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc. Create the directory lazily, only when the first record is written.

They are the teaching equivalent of ADRs: they capture non-obvious insights that will steer future sessions. Mastery itself is tracked in `MAP.md`, not here; a record explains something the map can't, such as why a misconception arose or why the mission moved.

## Template

```md
# {Short title of what was learned or established}

{1-3 sentences: what was learned (or what prior knowledge was established), and why it matters for future sessions.}
```

That is the whole format. A learning record can be a single paragraph. The value is recording _that_ this is now known and _why_ it changes what to teach next, not in filling out sections.

## Optional sections

Only include these when they add genuine value. Most records won't need them.

- **Status** frontmatter (`active | superseded by LR-NNNN`): useful when an earlier understanding turns out to be wrong and is replaced.
- **Evidence**: how the user demonstrated the understanding (a question answered, an exercise completed, prior experience cited). Useful when the claim might be revisited.
- **Implications**: what this unlocks or rules out for future sessions. Worth recording when non-obvious.

## Numbering

Scan `./learning-records/` for the highest existing number and increment by one.

## When to write a learning record

Write one when any of these is true:

1. **The user disclosed prior knowledge**: "I already know X." Record the claim and the _depth_ claimed, then verify it with a placement check before marking anything mastered in `MAP.md`.
2. **A misconception was corrected**: the user previously believed something wrong and now sees why. These are high-value: they predict future stumbling blocks for related skills.
3. **The mission shifted in response to learning**: the user discovered they cared about something different than they thought. Cross-link to [[MISSION.md]] and update it.

### What does _not_ qualify

- Material that was merely covered. Coverage is not learning. Wait for evidence.
- Anything already captured tersely in [[GLOSSARY.md]] as a term definition. Don't duplicate.
- Session-by-session activity. That goes in `LOG.md`.
- Mastery of a skill. That goes in `MAP.md`.

## Supersession

When a later record contradicts an earlier one (the user's understanding deepened or corrected), mark the old record `Status: superseded by LR-NNNN` rather than deleting it. The history of how understanding evolved is itself useful signal.
