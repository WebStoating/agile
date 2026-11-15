---
name: video-to-spec
description: "Use when the user has a narrated presentation video (slide-deck walkthrough, feature demo, or screen recording with voice-over) that describes a feature to build and wants a written specification or requirements document a coding agent can implement from. Checks that ffmpeg and openai-whisper are installed, transcribes the narration to English with Whisper, extracts one complete frame per slide with ffmpeg scene detection, and writes SPECIFICATION.md: scope, functional requirements traced to slides and timestamps, data model suggestion, acceptance criteria, tests and open questions, with the video's requirements kept separate from additions."
license: Apache-2.0
compatibility: Python 3.9+ (standard library only). Requires ffmpeg 5.1+ with ffprobe and the openai-whisper CLI (turbo model; medium for non-English narration). Works in Claude Code and Codex.
metadata:
  version: "0.1.0"
  author: "WebStoating"
---

# Video to Spec

Turn a narrated presentation video that describes a feature into `SPECIFICATION.md`, a requirements
document the user can hand to a coding agent to implement.

**Core principle:** the video is the source of truth. Everything in the specification is traceable to a
slide or a moment in the narration, or is clearly marked as your addition. Never invent names, numbers or
behaviour and present them as requirements.

## Inputs and paths

- `<skill-dir>` — the directory containing this SKILL.md.
- `<video>` — the local video file the user named. URLs are out of scope: ask for a downloaded file.
- **Project context** — one or two sentences on where the feature lives and who sees it, e.g. *"It will be
  a project available inside Django admin to run the simulation. It will not be visible to actual users."*
- `<out>` — `./<video-stem>-spec/` in the working directory, unless the user names another folder. If it
  already exists and is not empty, ask the user before reusing it.

Run every script as `python3 -I <skill-dir>/scripts/<script>.py`. They use only the Python standard library.

## Step 0 — Preflight (always first)

```bash
python3 -I <skill-dir>/scripts/check_tools.py
```

- **Exit 1:** show the user the `MISSING` / `PROBLEM` lines with their install hints and **stop**. Do not try
  to work around a missing tool, and do not install anything without the user's go-ahead.
- **Exit 0:** if a `MODEL` line says a model is not downloaded yet, tell the user in one line that the first
  transcription downloads it (size is in the line), then continue.
- Confirm `<video>` exists.
- If the user has not given project context, ask for it once. If they decline, write "Project context: not
  provided" in the Scope section and keep going.

## Step 1 — Transcribe

```bash
python3 -I <skill-dir>/scripts/transcribe.py <video> --out <out>
```

Whisper on a CPU can take longer than a normal command timeout for a long video. Run it with a long timeout
(for example 10 minutes) or in the background, and check `<out>/transcribe.status.json` (`stage` is `audio`,
`transcribe`, `translate`, `done` or `error`). A rerun with an existing transcript for the same video is
reused instantly.

- Non-English narration is translated to English automatically with the `medium` model.
- **Exit 2:** the video has no audio. Tell the user, and continue from the slides only.
- **Exit 1:** show the error lines and stop.
- On success, show the user the transcript (`<out>/transcript.txt`); for a long one, the first ~40 lines
  plus the path. `<out>/transcript.json` has timestamped segments for Step 4.

## Step 2 — Extract slide frames

```bash
python3 -I <skill-dir>/scripts/extract_slides.py <video> --out <out>
```

The script detects slide changes, takes each frame just before the next change (slides often build up
gradually, so the first frame of a slide is incomplete), and writes `<out>/frames/slide_NN.jpg` plus
`<out>/slides.json`. If the video is not a slide deck, it switches to one frame every few seconds with
near-duplicates removed. How it works and how to tune it:
[references/frame-extraction.md](references/frame-extraction.md).

## Step 3 — Check every frame

Open **every** image in `<out>/frames/` and look at it.

- If a frame is incomplete (a build animation mid-way, a transition, a blurred cursor over the content),
  re-take it at a better moment inside that slide's time range:
  `python3 -I <skill-dir>/scripts/extract_slides.py <video> --out <out> --retake <N> --at <seconds>`
  then open it again.
- Write each slide's title (or a short description if it has none) into its `title` field in
  `<out>/slides.json`.
- Show the user a table: file, time range, slide title.

## Step 4 — Write the specification

Write `<out>/SPECIFICATION.md` from [assets/specification-template.md](assets/specification-template.md),
following every rule in [references/spec-writing.md](references/spec-writing.md). Use the transcript and
the slide images together: match transcript segments to slides by time range, so each requirement cites
where it came from. Look at the frames again whenever a slide carries numbers, tables, fields or diagrams.

## Step 5 — Report to the user

In chat, give:
1. The path of every file: `SPECIFICATION.md`, `transcript.txt`, `transcript.json`, `slides.json`, `frames/`.
2. Which parts you added yourself (everything marked *(added)*), in a short list.
3. The open questions the user should answer before handing the specification to a coding agent, most
   important first.

## Red flags — stop and correct course

| Thought | Reality |
|---|---|
| "The tool check failed, but I can probably manage without whisper" | Stop and show the install hints. The spec depends on the narration. |
| "The slide shows a number, so that's the requirement" | Check the narration: is it an example or placeholder? Label it as such if so. |
| "I know what this model or service is probably called in their codebase" | Do not invent names. Section 1 tells the implementing agent to find them. |
| "Section 6 or 7 is empty, I'll fill it with sensible defaults" | Write "Not covered in the video" and move the point to Open questions. |
| "The frame looks roughly right, no need to open the others" | Open every frame. Partial build-up frames are the most common defect. |
| "I'll tidy the speaker's wording" | Keep exact numbers, examples and wording; clarity edits go in your own sentences. |
