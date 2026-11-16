# Writing SPECIFICATION.md

`SPECIFICATION.md` is a specification-style document that a coding agent (Claude, Codex, …) uses as the
source for a **brainstorming** session about the feature. It is **not** a requirements document. It says
what the video says, in a readable form, and nothing more. Designing the solution, choosing names, writing
tests and filling gaps all happen later, in the brainstorming session.

Fill in [../assets/specification-template.md](../assets/specification-template.md).

## The one rule: only the video and the user's context

Every statement in the document comes from the video (narration or slides) or from the project context the
user gave. Do not invent anything:
- No new requirements, behaviour, edge cases, limits, names, numbers or defaults.
- No tests or test plans, no data model, no class or table designs, no implementation steps, no export
  formats, no "nice to have" ideas, no risks or options you thought of yourself.
- No sections the video and the user's context do not cover. Delete an optional section rather than
  writing "Not covered in the video" or similar filler in it.
- No appendix: no slide table, no transcript copy, no notes about how the video was processed.

If you notice something important the video leaves out, it may only appear as an open question, and only
when it is anchored to something the video says (see Open questions).

## Format

- No IDs anywhere: no `FR-1`, `AC-1`, `Q1`, `T-1`, and no cross-references such as "(see Q3)". Use plain
  bullets and plain headings.
- No "must" or "shall" in your own sentences. A "must" is fine inside a quote from the video.
- Keep it short and readable. Prefer the speaker's words over formal paraphrase.

## Citations and fidelity

- Cite every statement about the video as `[slide N, mm:ss–mm:ss]` (time range from `slides.json` or the
  transcript segment).
- Follow the order of the slides.
- Keep the exact numbers, examples and wording from the video. Quote short phrases where wording matters.
- When the video marks a number or example as illustrative ("for example", "for now", "placeholder", or a
  slide note such as "example numbers"), label it **example** or **placeholder** in place.
- If the narration and a slide disagree, record both and add an open question.

## Sections

**Required:** title and source line, How to use this document, Goal, What the video describes, Open
questions. **Optional**, kept only when the video or the user's context has content for them: Project
context, Scope, Acceptance criteria.

### How to use this document

A few bullets to the receiving agent, adapted to the project context:
- This document is the input for a brainstorming session. Do not start implementing.
- Explore the existing codebase first and find what the feature touches and what can be reused.
- Do not invent model, class or table names. Names in this document come from the video.
- Go through the open questions with the user, one at a time, before proposing a design.

### Goal

One short paragraph: what the speaker wants and why, in their terms, with citations.

### Project context

Copy the user's project context as given. If the user gave none, delete the section.

### What the video describes

One subsection per slide or group of related slides, in slide order. Plain bullets with citations.

### Scope

Only what the video explicitly includes, excludes or defers ("we'll decide later", "not part of this"),
each cited. If the video does not talk about scope, delete the section.

### Acceptance criteria

Plain bullets, no IDs. Each one is an observable outcome the video states or directly implies, and cites
where. Do not add criteria for cases the video does not mention (error handling, empty results, unchanged
billing, and so on). If the video gives nothing to base criteria on, delete the section.

### Open questions

Points the video raises but leaves unclear, ambiguous, contradictory or undefined, most important first.
Each question cites the slide that raises it and says in one line why the answer matters. Do not ask
about topics the video never touches, and do not answer the questions yourself.
