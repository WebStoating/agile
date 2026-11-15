---
name: video-to-spec
description: Use when the user has a narrated presentation video (slide-deck walkthrough, feature demo, or screen recording with voice-over) that describes a feature to build and wants a written specification or requirements document a coding agent can implement from. Checks that ffmpeg and openai-whisper are installed, transcribes the narration to English with Whisper, extracts one complete frame per slide with ffmpeg scene detection, and writes SPECIFICATION.md: scope, functional requirements traced to slides and timestamps, data model suggestion, acceptance criteria, tests and open questions, with the video's requirements kept separate from additions.
license: Apache-2.0
compatibility: Python 3.9+ (standard library only). Requires ffmpeg 5.1+ with ffprobe and the openai-whisper CLI (turbo model; medium for non-English narration). Works in Claude Code and Codex.
metadata:
  version: "0.1.0"
  author: "WebStoating"
---

# Video to Spec

Workflow pending.
