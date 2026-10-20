# The method and where it comes from

Researched 2026-10-20. Alpha School and Timeback publish their principles but not their software internals. The outcome claims (students learn "2x in 2 hours", rank in the top 1–2%) are the school's own, with no independent peer-reviewed evaluation found. Treat the numbers below as a well-reasoned design, not a proven result.

## Alpha School in one paragraph

Alpha is a private K-12 school, with a growing number of campuses in the US, founded by MacKenzie Price and backed by Joe Liemandt. Students do core academics in about two focused hours each morning on adaptive apps, which run on a platform first called 2 Hour Learning and now Timeback. The two hours are split into 25-minute blocks with movement breaks. Adults on the floor are "guides" who coach and motivate rather than lecture, at about one guide to five students. Afternoons go to life skills and projects.

## Mechanism to rule

| Alpha / Timeback mechanism | Source | Rule in this skill |
|---|---|---|
| Students don't advance without ≥90% accuracy on rigorous assessments | Timeback Principles | Mastery gate at 90% |
| No XP below 80% accuracy; 1 XP = 1 minute of focused learning | Timeback Principles | XP in `LOG.md`, zero below 80% |
| Difficulty adjusted to keep students at 80–85% accuracy, their zone of proximal development | Alpha gamification post | Practice in the 80–85% band |
| Placement and adaptive delivery; hole-filling when gaps appear, including earlier-grade material | Timeback How It Works; Alpha program page | Placement check; holes before new ground |
| Retrieval is the primary learning event; practice must require recall, not recognition | Timeback Principles, Tier 0 and Non-negotiable 6 | Recall, not recognition |
| Spacing, interleaving, worked examples before problems, immediate and elaborated feedback | Timeback Principles, Tier 1 | Review schedule, interleaved reviews, worked example first, feedback now |
| Missed topics return "just before the student is likely to forget" | FutureIQ parent review | Review schedule and missed items |
| 25-minute focus blocks | Alpha gamification post; two-hour day page | 25-minute default session |
| Waste meter flags off-task patterns (scrolling without reading, skipping explanations, guessing, tanking placement) | Alpha gamification post; Timeback Principles | Anti-patterns list |
| Progress rings, visible daily wins, weekly goals | Alpha gamification post | Close-of-session progress line |
| Practice on advanced topics counts as review of their prerequisites (Math Academy, an Alpha-adjacent app) | Skycak, FIRe | Implicit review; prerequisites of a placed skill inferred as mastered |
| A knowledge graph of prerequisites drives the diagnostic and what to teach next | Math Academy How It Works | `MAP.md` |

## Kept from the original teach skill

This skill began as Matt Pocock's `teach` skill ([mattpocock/skills](https://github.com/mattpocock/skills), MIT). Its philosophy still holds and sits underneath the rules above.

- **Knowledge, skills, wisdom.** Knowledge comes from high-trust sources. Skills come from practice with feedback. Wisdom comes from using the skill among other practitioners, which is why `RESOURCES.md` lists communities.
- **Fluency versus storage strength.** Feeling fluent in the moment is not the same as remembering in a month. Desirable difficulty (retrieval, spacing, interleaving) builds storage. This is why self-report never counts and why reviews exist.
- **Difficulty is the enemy of acquiring knowledge and the tool for building skill.** Explain plainly; practice hard.

## Deliberately not copied

- **Camera-based attention tracking and proctoring.** Out of place for an adult learning with an agent. The anti-pattern list does the same job in conversation.
- **Cash and currency rewards.** The evidence the FutureIQ review cites (Fryer) shows payment moves easy behaviours such as reading books, but not test scores. For an adult, the mission is the motivator.
- **Human guides.** The agent plays the guide: it holds the standard, names the anti-patterns and ties every session back to the mission. A 1:5 ratio of human attention is part of Alpha's results, and an agent does not fully replace that.
- **A fixed two-hour day.** Adults fit sessions in where they can. One 25-minute block, done consistently, is the unit.

## Sources

- [Timeback Docs: Principles](https://docs.timeback.com/beta/about-timeback/principles): 90% mastery, 1 XP per minute, no XP below 80%, the learning-science tiers.
- [Timeback Docs: How It Works](https://docs.timeback.com/beta/about-timeback/how-it-works): placement, adaptive delivery, waste detection, hole-filling.
- [Alpha School: How AI and gamification transform learning](https://alpha.school/blog/how-ai-and-gamification-transform-learning-at-alpha-school/): waste meter, 25-minute blocks, the 80–85% band, rings and rewards.
- [Alpha School: What the two-hour day looks like](https://alpha.school/resources/how-alpha-two-hour-school-day-works/): session shape, guide role.
- [Alpha School: Introducing TimeBack](https://alpha.school/blog/introducing-timeback-the-next-evolution-of-alphas-model/): the 2 Hour Learning to Timeback rename.
- [FutureIQ: Understanding Alpha School](https://futureiq.substack.com/p/understanding-alpha-school-can-we): a critical parent review covering the 80% credit rule, spaced return of missed topics, incentives, and the argument that the real day is closer to four hours.
- [Math Academy: How It Works](https://mathacademy.com/how-it-works) and [Skycak: Fractional Implicit Repetition](https://justinmath.com/individualized-spaced-repetition-in-hierarchical-knowledge-structures/): the knowledge graph, the diagnostic and implicit review.
- [Wikipedia: Alpha School](https://en.wikipedia.org/wiki/Alpha_School): background and criticism.
