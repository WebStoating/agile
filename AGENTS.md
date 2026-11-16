# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, others) working in this repository.

## What this repository is

The source for `agile`, a Claude Code and Codex plugin of Agile project-management
[Agent Skills](https://agentskills.io/specification). Every skill must work in Claude Code and in Codex.

Skills:
- `video-to-spec` — turns a narrated presentation video into `SPECIFICATION.md`, a specification-style
  document built only from the video, used as the source for brainstorming with a coding agent. Uses
  ffmpeg and the openai-whisper CLI.

## Layout

```
AGENTS.md
README.md
.agents/plugins/marketplace.json  # dev-only Codex marketplace (local source); never installed
docs/                             # local design notes and plans; git-ignored, never committed
tests/                            # unittest suite
agile/                            # THE PLUGIN — the only thing that ships
├── .claude-plugin/plugin.json    # Claude Code manifest
├── plugin.json                   # Codex manifest
└── skills/video-to-spec/
    ├── SKILL.md
    ├── scripts/                  # check_tools.py, transcribe.py, extract_slides.py, vts_lib/
    ├── references/
    └── assets/
```

## Commands

```bash
python3 -m unittest discover -s tests -t . -v                    # offline suite (ffmpeg tests skip without ffmpeg)
uvx --from "git+https://github.com/agentskills/agentskills#subdirectory=skills-ref" skills-ref validate agile/skills/video-to-spec
claude plugin validate --strict agile
claude --plugin-dir agile                                        # load the plugin from the working tree
```

## Hard rules

**Skill format (Agent Skills standard):**
- `SKILL.md` frontmatter `name` must equal the skill's folder name.
- `description` ≤1024 chars, `compatibility` ≤500 chars, body under 500 lines, `metadata` values quoted strings.
- Reference files are linked one level deep from `SKILL.md`, with relative paths.

**Plugin packaging:**
- `agile/` is the plugin root and holds only `.claude-plugin/plugin.json`, `plugin.json` and `skills/`. Both
  agents copy the whole folder into their plugin cache, so nothing repo-only (tests, docs, dev config) may go in it.
- Both manifests are identical, use `name` `agile`, and their `version` must equal every skill's `SKILL.md`
  `metadata.version`. Users get an update only when that version changes, so bump them together.
- No symlink inside the plugin may point outside it.
- The published catalog lives in `WebStoating/skills`; `.agents/plugins/marketplace.json` here is for local
  development only.
- `tests/test_plugin_package.py` enforces these rules.

**Agent neutrality:** `SKILL.md` and `references/` use generic actions ("run", "open the image", "ask the user").
Never name one agent's tools or model-specific limits.

**Skill scripts:** Python ≥3.9, standard library only, always run as `python3 -I`. Subprocess calls take an argv
list (first element resolved with `shutil.which`), never `shell=True`. External tools: ffmpeg ≥5.1, ffprobe,
openai-whisper CLI.

**Tests:** never run real whisper in the suite; use the stub executables from `tests/stubs.py`. Tests that need
ffmpeg generate their videos at test time and skip when ffmpeg is absent. No media files are committed.

## Commits

Follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/). One logical change per
commit. No `Co-Authored-By:` trailers and no AI-attribution lines in commit messages or pull request
descriptions. Never commit `docs/`.
