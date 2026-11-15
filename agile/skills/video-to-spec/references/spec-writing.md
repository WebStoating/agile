# Writing SPECIFICATION.md

Rules for turning the transcript and slide frames into a specification a coding agent can implement from.
Fill in [../assets/specification-template.md](../assets/specification-template.md) section by section.

## Provenance

- Every requirement cites its source as `[slide N, mm:ss–mm:ss]` (time range from `slides.json` or the
  transcript segment).
- Anything that does not come from the video is marked *(added)* at the start of the sentence or bullet:
  your inferences, suggested defaults, the data model, tests you propose. List all of them again in your
  report to the user.
- Keep the requirements that come from the video separate from your additions. Never blend an addition into
  a cited requirement.

## Fidelity

- Follow the order of the slides in the workflow and functional requirements.
- Keep the exact numbers, examples and wording from the video. Quote short phrases where wording matters.
- When a number or example is clearly illustrative (the speaker says "for example", "something like",
  "placeholder", or the slide shows dummy data), label it **example** or **placeholder**, never as a fixed
  requirement, and add an open question if the real value matters.
- If the narration and a slide disagree, record both and add an open question.

## Section 1 — Instructions for the implementing agent

Always include, adapted to the project context:
- Explore the existing codebase first; find the models, services and modules this feature touches.
- Reuse what exists rather than creating parallel versions.
- Propose a plan and wait for approval before implementing.
- Do not invent model, class or table names; if something named in this document does not exist, ask.
- Resolve the Open questions (section 11) with the user before building the parts they affect.

## Scope and safety

- Scope (section 3): in scope and out of scope, based on the video and the project context. If no project
  context was given, write "Project context: not provided".
- Safety and isolation (section 7): constraints implied by the project context, for example "internal only,
  never visible to end users", "no side effects on real users' data, emails or payments", "runs against
  copies or simulated data". Each implied constraint is marked *(added)* unless the video states it.

## Optional sections

Sections 5 (data, results and reporting), 6 (execution: background jobs, progress, retries) and 7 (safety
and isolation) are kept only when the video or the project context implies them. Otherwise the section body
is exactly `Not covered in the video.` and anything related goes to Open questions. Never pad a section
with invented content.

## Data model, acceptance criteria, tests

- Section 8 is a **suggestion**, marked *(added)*, using names from the video where it gives them and generic
  descriptive names otherwise, with a note that the implementing agent must map them to the real codebase.
- Section 9: numbered, testable acceptance criteria (`AC-1`, `AC-2`, …), each citing its source or marked
  *(added)*.
- Section 10: the tests that prove the acceptance criteria, referencing them by number.

## Open questions

Section 11 lists everything ambiguous, contradictory, or missing that would change what gets built, most
important first, each with why it matters. Do not invent answers to them elsewhere in the document.
