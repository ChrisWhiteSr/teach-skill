# Portable progress checkpoint

Use the workspace's existing checkpoint path, or `PROGRESS.md` for a new course. This file lets another assistant resume without the original conversation. Keep it current and concise; link to detailed learning records instead of duplicating them.

## Template

```md
# Learning checkpoint: {Subject or track}

Updated: {Date and timezone if relevant}.

## Read first
- Mission: {Relative path}.
- Curriculum: {Relative path, if one exists}.
- Relevant learning records: {Paths}.
- Preferences and constraints: {Notes path or brief description}.

## Current position
- Lesson or activity: {Title and artifact path, if any}.
- Status: {Ready, awaiting response, practicing, or demonstrated; state only what is supported}.
- Last interaction: {Actual learner response or a concise summary}.
- Unresolved: {Specific uncertainty or missing prerequisite}.

## Resume with
{The exact next question, exercise, or action. Include what to do if it is already easy or still unclear.}

## Review later
{A concept or skill to revisit, if useful. No schedule is implied unless one was agreed and set up.}
```

Update at a meaningful session boundary. A file being generated does not mean the learner completed it. Browser interaction, practice, or scores are visible to the assistant only if a working integration exposes them or the learner reports them. If an assistant cannot write files, it should provide the checkpoint text and clearly state that it remains unsaved.
