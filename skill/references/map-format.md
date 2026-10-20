# MAP.md and LOG.md format

## MAP.md

`MAP.md` is the course's skill map: every skill the mission needs, what each one depends on, and where the learner stands. It is the single source of truth for what to teach next and what to review. Any agent that opens the course reads it first.

```md
# Skill map: {Subject}

Mission: [[MISSION]] · Updated: 2026-10-20 by claude-code

| ID | Skill (the learner can…) | Needs | Status | Best check | Last | Step | Next review |
|---|---|---|---|---|---|---|---|
| S1 | name the inputs a claims-based risk model uses | - | mastered | placement 2/2 | 2026-10-20 | 1 | 2026-10-23 |
| S2 | turn a weighted sum into a probability with the logistic function | S1 | mastered | 5/5 | 2026-10-20 | 0 | 2026-10-21 |
| S2a | convert odds to probability and back | - | learning | 3/5 | 2026-10-20 | - | - |
| S3 | explain why a 0.0 coefficient silences a biomarker | S2 | new | - | - | - | - |

## Missed items
- S2a (2026-10-20): "Odds of 3 to 1: what probability?" answered 0.33. Confused odds with probability.

## Holes
- S2a added 2026-10-20: the S2 check missed two odds questions. Teach S2a before S3.
```

### Columns

- **ID**: `S1`, `S2`… in rough teaching order. A hole found later gets a letter suffix (`S2a`) so the IDs never renumber.
- **Skill**: a verb phrase for something the learner can do. If you can't write a check item for it, it isn't a skill yet.
- **Needs**: the IDs of its prerequisites, or `-`.
- **Status**: `new` (not taught), `learning` (taught or partly known, not yet at 90%), `mastered`.
- **Best check**: the best mastery-check score, `placement n/n` for a skill tested in placement, or `inferred from S5` for a prerequisite of a skill placed as mastered.
- **Last**: the date of the last check or review.
- **Step**: where the skill is on the review schedule, counting from 0. Step 0 is the first interval in the skill's Review schedule section (1 day), step 1 the second, and so on.
- **Next review**: `Last` plus the interval for `Step`. Leave it as `-` while the skill is not mastered.

### Rules

- **Status changes need evidence.** `mastered` only from a check at 90% or above, two correct placement items, or inference from a skill placed that way (confirmed or demoted at its first review). Nothing moves on the learner's say-so.
- **A passed review**: Step +1, Last = today, recompute Next review.
- **A missed review**: Status back to `learning`, Step and Next review back to `-`, and the missed item goes under Missed items.
- **Implicit review**: when a check on a skill correctly exercises a prerequisite, treat it as a passed review of that prerequisite.
- **Missed items** keep the actual question and the wrong answer. They are tomorrow's practice items and the best predictor of the next stumble. Delete an entry once its skill is mastered.
- **The map can change.** Add skills as the mission sharpens and remove ones the mission no longer needs. Note the change in the `Updated` line.

## LOG.md

One line per session, newest at the bottom. It gives the learner a visible record of progress, and gives the next agent the recent history.

```md
# Session log: {Subject}

| Date | Agent | Minutes | XP | Reviews | Check | Taught | Note |
|---|---|---|---|---|---|---|---|
| 2026-10-20 | claude-code | 30 | 30 | - | placement | - | placement: S1 mastered, S2 learning |
| 2026-10-21 | hermes | 10 | 10 | 2/2 | - | - | review-only session over Telegram |
| 2026-10-22 | claude-code | 25 | 0 | 1/2 | S2a 3/5 | S2a | accuracy under 80%, no XP; odds vs probability |
```

- **Minutes**: focused minutes. Estimate from message timestamps when you have them; otherwise ask the learner at close.
- **XP**: one per focused minute. Zero if overall accuracy in the session was below 80%.
- **Progress line for the close**: skills mastered out of the total (from `MAP.md`), XP over the last seven days, and the run of consecutive days with a session (from `LOG.md`).
