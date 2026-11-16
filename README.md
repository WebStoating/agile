# Agile

A Claude Code and Codex plugin of Agile project-management [Agent Skills](https://agentskills.io).

| Skill | What it does |
|---|---|
| `video-to-spec` | Turns a narrated presentation video that describes a feature into `SPECIFICATION.md`, a specification-style document built only from the video, which you feed to a coding agent (Claude, Codex) as the source for brainstorming the feature. |

## video-to-spec

You record (or receive) a narrated slide presentation of a feature. The skill:

1. Checks that `ffmpeg`, `ffprobe` and the `whisper` CLI are installed, and stops with install hints if not.
2. Transcribes the narration with Whisper (`turbo`), translating to English with `medium` when needed.
3. Extracts one complete frame per slide: scene detection, frame taken just before each slide change so
   build-up animations are finished; one frame every few seconds for screen recordings.
4. Has the agent look at every frame, re-take incomplete ones and build a slide table.
5. Writes `SPECIFICATION.md` from the video content only: how the receiving agent should use it, the goal,
   your project context, what the video describes in slide order with `[slide N, mm:ss–mm:ss]` citations,
   scope and acceptance criteria when the video gives them, and open questions. No requirement IDs, no
   invented tests or data models, no sections the video does not cover. Feed it to Claude or Codex to
   brainstorm the design.

Output goes to `./<video-name>-spec/`: `SPECIFICATION.md`, `transcript.txt`, `transcript.json`,
`slides.json` and `frames/`.

### Requirements

- Python 3.9+ (the scripts use only the standard library).
- ffmpeg 5.1+ with ffprobe — macOS `brew install ffmpeg`, Debian/Ubuntu `sudo apt install ffmpeg`,
  Windows `winget install Gyan.FFmpeg`.
- openai-whisper CLI (20240930 or newer, for the `turbo` model) — on macOS with Homebrew,
  `brew install openai-whisper` ([formula](https://formulae.brew.sh/formula/openai-whisper)); elsewhere
  `pipx install openai-whisper`.
  The first transcription downloads the turbo model (~1.5 GB); non-English narration also downloads
  `medium` (~1.4 GB).

## Install

The plugin is published in the [WebStoating skills marketplace](https://github.com/WebStoating/skills). Add the
marketplace once, then install the plugin.

**Claude Code**

```bash
claude plugin marketplace add WebStoating/skills
claude plugin install agile@webstoating-skills
```

**Codex**

```bash
codex plugin marketplace add WebStoating/skills
codex plugin add agile@webstoating-skills
```

Start a new session after installing so the agent picks up the plugin. To update, refresh the marketplace
(`claude plugin marketplace update webstoating-skills` or `codex plugin marketplace upgrade webstoating-skills`).
A new plugin version reaches users only when the version number changes.

## Use

Ask your agent: *"Use video-to-spec on demo.mp4. It will be a page inside Django admin, not visible to real
users."* In Claude Code you can also run `/agile:video-to-spec demo.mp4`.

## Use the scripts directly

```bash
S=agile/skills/video-to-spec/scripts
python3 -I $S/check_tools.py
python3 -I $S/transcribe.py demo.mp4 --out demo-spec
python3 -I $S/extract_slides.py demo.mp4 --out demo-spec            # --mode interval for screen recordings
python3 -I $S/extract_slides.py demo.mp4 --out demo-spec --retake 3 --at 42.5
```

Writing `SPECIFICATION.md` is the agent's part of the workflow (see `SKILL.md`).

## Tests

```bash
python3 -m unittest discover -s tests -t . -v
```

Real whisper never runs in the suite: stub executables stand in for it. Tests that need ffmpeg generate a
short synthetic video at test time and are skipped when ffmpeg is not installed. No media files are committed.

## Repository layout

| Path | Contents |
|---|---|
| `agile/` | The plugin, the only part that ships: `.claude-plugin/plugin.json` (Claude Code), `plugin.json` (Codex) and `skills/` |
| `agile/skills/video-to-spec/` | `SKILL.md` (agent workflow), `scripts/` (`check_tools.py`, `transcribe.py`, `extract_slides.py`, `vts_lib/`), `references/` (spec-writing rules, frame extraction), `assets/` (specification template) |
| `.agents/plugins/marketplace.json` | Dev-only Codex marketplace that installs the plugin from this working tree |
| `tests/` | unittest suite and stub executables |

## Local development

**Claude Code** loads the plugin straight from the working tree:

```bash
claude --plugin-dir agile
```

After an edit, run `/reload-plugins` in the session (or start a new one).

**Codex** has no such flag, so this repository ships a dev-only marketplace, `agile-dev`, that points at the
local plugin folder:

```bash
codex plugin marketplace add .
codex plugin add agile@agile-dev
```

Codex copies the plugin into its cache, so rerun the `codex plugin add` command after every edit, then start a
new session. Don't keep the published plugin installed while you develop, or the agent sees the skill twice.

Validate the skill and the plugin manifest:

```bash
uvx --from "git+https://github.com/agentskills/agentskills#subdirectory=skills-ref" skills-ref validate agile/skills/video-to-spec
claude plugin validate --strict agile
```

See `AGENTS.md` for contributor rules.

## License

[Apache-2.0](LICENSE)
