# Slides and narration

How to turn the input (a standup, a weekly summary, any short update) into the `slides` of `deck.json`.

## Content only

Slides and narration contain **only what the input says**, regrouped and condensed. You may shorten,
reorder and group, and you may add plain connecting words ("Next", "One blocker today"). You may not add
facts.

- Do not invent progress, percentages, dates, names, numbers, ticket IDs, blockers, risks or next steps.
- Do not add filler sections ("Key takeaways", "Questions?", "Thank you", "Agenda") the input does not have.
- Keep numbers, names, product terms and ticket references exactly as written.
- If the input has no blockers, there is no blocker slide and the narration does not say "no blockers"
  unless the input says so.

Forbidden addition, for an input line `- Finished the login form`:

| Wrong | Why |
|---|---|
| "We finished the login form, about 80% of the auth epic, ahead of schedule." | The percentage, the epic and "ahead of schedule" are not in the input. |
| "We finished the login form." | Right: only what the input says. |

The preset's `context` sets the audience, tone and length. It is not a source of facts for the slides.

## Slide types

| Type | Fields | Use for |
|---|---|---|
| `title` | `title`, optional `subtitle` | Always the first slide: the update's name (for example "Daily Standup") and, if the input gives one, the date or team as the subtitle. |
| `section` | `title` | One per heading in the input, such as Yesterday, Today, Blockers, Highlights, Next week. |
| `bullets` | `title`, `bullets` | The items under a heading. At most 6 bullets, each at most 10 words. Split a longer list over two slides ("Today (2/2)"). |
| `quote` | `quote`, optional `title` | A single blocker, decision or note that should stand out, quoted or condensed from the input. |

Every slide also has `narration`. The scripts add `audio` and `durationInSeconds`; do not write them.

- Bullets are short phrases, not sentences: "Fixed the report export bug", not "I have fixed the bug in
  the report export that was reported".
- Keep the input's order unless regrouping makes it clearer (for example, gathering all blockers).

## Narration

- **Pace:** about 150 words per minute. A daily standup is about 2 minutes (about 300 words in total)
  unless the preset's `context` says otherwise; a weekly summary follows its `context`, about 3 minutes if
  it gives none. Shorter is fine when the input is short. Never pad.
- **Speak around the bullets; do not recite them.** The slide shows the list, the narration connects it:
  what happened, why it matters (only if the input says), what comes next. Full spoken sentences, no
  bullet fragments, no "bullet one".
- **Language:** the document's language. A German update gets German slides and German narration.
- **Exact facts:** numbers and names as written. Write them so they read aloud naturally, without changing
  their value ("PR 412" stays "PR 412").
- Title slide: one or two sentences that say what the update is. Section slides: one short sentence.
- Plain text only: no Markdown, emoji, URLs, code or square brackets in the narration (`eleven_v4` reads
  `[...]` as an audio tag, a stage direction, not as words). Name a link's subject instead of reading its URL.
- Each slide's narration is voiced separately, so each one must make sense on its own and end with a full
  sentence.

## Mapping the input

- **Headed Markdown** (`## Yesterday`, `## Today`, `## Blockers`): a `title` slide, then for each heading a
  `section` slide followed by its `bullets` (or a `quote` for a single blocker or decision).
- **A bare paste with no headings:** a `title` slide followed by `bullets` slides (up to 6 items each).
- **Nested lists:** keep the top-level items as bullets; fold sub-items into the narration if they matter,
  otherwise leave them out.
- **Tables, links and code** in the input: condense into bullets in your own short words, keeping the facts.

## Example

Input:

```markdown
# Standup 2026-11-16
## Yesterday
- Finished the login form
- Reviewed two pull requests
## Today
- Start the password reset flow
## Blockers
- Waiting on access to the staging environment
```

Slides:

1. `title` "Daily Standup", subtitle "2026-11-16"
2. `section` "Yesterday", then `bullets` "Done": the two items
3. `section` "Today", then `bullets` "Planned": the one item
4. `section` "Blockers", then `quote` "Waiting on access to the staging environment."

Narration for the "Done" slide: "Yesterday the login form was finished, and two pull requests got a
review." Not: "Finished the login form. Reviewed two pull requests."
