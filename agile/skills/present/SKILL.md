---
name: present
description: "Use when the user wants to turn a written update, such as a daily standup or weekly summary given as a Markdown file or pasted text, into a narrated slide video (MP4). Splits the update into title, section, bullet and quote slides, writes a short spoken narration per slide from the input only, voices it with ElevenLabs and renders it with a saved Remotion template, so the look and voice stay the same from run to run. Named presets in .present.json at the notes root hold the context, voice, theme and output format. Unchanged narration reuses cached audio. The video is saved as <input folder>/<input stem>.mp4, or ./PRESENTATION.mp4 for pasted text, unless the preset or the user gives an output format with {stem}, {date} or {preset}."
license: Apache-2.0
compatibility: Python 3.9+ (standard library only). Requires Node.js 18+ with npx, ffmpeg with ffprobe, ELEVENLABS_API_KEY, and the Remotion (remotion-best-practices, remotion-render) and ElevenLabs (text-to-speech) agent skills. Works in Claude Code and Codex.
metadata:
  version: "0.1.0"
  author: "WebStoating"
---

# Present

Turn a written update (a Markdown file or pasted text), usually a **daily standup** or a **weekly summary**,
into a narrated slide video. Each slide gets a short narration voiced with ElevenLabs, and a saved Remotion
template renders one MP4 where every slide lasts as long as its narration.

**Core principle:** slides and narration contain only what the input says, regrouped and condensed. Never
invent progress, names, numbers, blockers, IDs or filler sections. Rules:
[references/slides-and-narration.md](references/slides-and-narration.md).

## Inputs and paths

- `<skill-dir>`: the directory containing this SKILL.md.
- The input: a document path (Markdown preferred, any text file works) or text pasted into the request.
- Optional, from the request: a preset name ("as weekly"), an output format, and one-off changes to the
  preset (another voice, a longer narration). One-off changes apply to this run only; afterwards, offer to
  save them back to the preset.
- `<root>`: the notes root, the folder holding `.present.json`. Everything the skill keeps lives in
  `<root>/.present/`. Schema, preset resolution and the folder layout:
  [references/settings.md](references/settings.md).

Run every script as `python3 -I <skill-dir>/scripts/<script>.py`. They use only the Python standard library,
never touch the network, and never print key values. Quote every path argument in every command, as shown:
notes folders often contain spaces.

**Keys.** Never print, echo or store the value of `ELEVENLABS_API_KEY` or `REMOTION_LICENSE_KEY`, and never
put one on a command line as literal text. Report only present or absent. When a key lives in `<root>/.env`
rather than the environment, load that file into the environment of the command that needs it without
showing it (in a POSIX shell: `set -a; . "<root>/.env"; set +a; <command>`).

## Step 0: Preflight (always first)

1. Run Step 1's `settings.py resolve` command to learn `<root>`, then:

   ```bash
   python3 -I "<skill-dir>/scripts/check_tools.py" --root "<root>"
   ```

   - **Exit 1:** show the user the `MISSING` / `PROBLEM` lines with their hints and **stop**. For a missing
     `ELEVENLABS_API_KEY`, point to the ElevenLabs `setup-api-key` skill, which sets the key up without
     showing it. Do not work around a missing tool.
   - **Exit 0:** mention the `LICENSE` line once (Remotion needs a paid company license for organisations
     of more than 3 people), then continue.
2. Check that you have the agent skills `remotion-best-practices`, `remotion-render`, `text-to-speech` and
   `setup-api-key`. If any is missing, show the install commands and install only on the user's go-ahead.
   If the user declines, **stop**:

   ```bash
   npx skills add remotion-dev/skills
   npx skills add elevenlabs/skills
   ```

3. The ElevenLabs CLI (`npx -y @elevenlabs/cli@1.11.0`) is downloaded on first use. Ask once before the
   first run of it on this machine.

## Step 1: Resolve the input and the preset

```bash
python3 -I "<skill-dir>/scripts/settings.py" resolve --input "<file>" [--preset "<name>"] [--output "<format>"]
python3 -I "<skill-dir>/scripts/settings.py" resolve --pasted [--preset "<name>"] [--output "<format>"]
```

Read the input file (or take the pasted text). The command prints JSON with `root`, `status`, `preset`,
`presets`, `context`, `voice`, `theme`, `output_path`, `output_exists`, `output_parent_missing`, `run_dir`,
`public_dir` and `remotion_dir`. Pasted text renders to `PRESENTATION.mp4` in the current folder unless an
output format says otherwise. Handle `status`:

- `ok`: use the preset's `context`, `voice` and `theme`, plus any one-off changes from the request.
- `none` (first run, no preset yet): set one up with the user.
  1. Ask for the context: who watches, what the update covers, and the target length.
  2. Help pick a voice. List the premade voices:

     ```bash
     npx -y @elevenlabs/cli@1.11.0 voices search --category premade --page-size 20 --format json
     ```

     Show a short table (name, a few labels, `voice_id`). Offer a sample: open the voice's `preview_url`, or
     voice one sentence with the Step 4 command into a scratch file.
  3. Pick a theme: `primary`, `background`, `text` (hex colors), `font` (a Google Fonts family name) and
     `logo` (a path relative to `<root>`, or `null`). Start from the theme in
     [assets/deck.example.json](assets/deck.example.json) unless the user wants another look.
  4. Use `model_id` `eleven_v4` (the ElevenLabs text-to-speech skill's current default) unless the user
     names another. It is saved into the preset's `voice` and never changed silently later.
  5. Tell the user where `.present.json` will be created (`settings_path`) and ask before creating it. On
     a yes, write the preset as JSON to a scratch file and run:

     ```bash
     python3 -I "<skill-dir>/scripts/settings.py" save --root "<root>" --preset "<name>" --json-file "<file>" [--default]
     ```

     Then run `resolve` again. If the user declines, use the values for this run only.
- `ambiguous`: several presets and no default. Ask which one (`presets` lists them).
- `unknown`: the named preset does not exist. List `presets` and ask.

Then:

- If `output_exists` is true, ask before overwriting the video.
- If `output_parent_missing` is true, create that folder.

## Step 2: Set up the Remotion project

```bash
python3 -I "<skill-dir>/scripts/setup_project.py" --root "<root>" [--gitignore]
```

It copies the template into `remotion_dir` on the first run and refreshes it when the template changes,
keeping `node_modules/`. It prints JSON with `action` (`created`, `updated`, `current`) and `needs_install`.

- On the first setup (`action` is `created`) in a git repository, offer to add `.present/` to
  `<root>/.gitignore`. On a yes, run the command again with `--gitignore`. If it then prints
  `"gitignore_added": false`, tell the user nothing was added: `<root>` is not inside a git work tree, or
  `.present/` is already listed.
- If `needs_install` is true, ask, then run `npm install` in `remotion_dir`. Never install in the skill's
  own folder.
- If `action` is `created` or `updated`, check that the composition renders before going on: in
  `remotion_dir`, render one second of `Deck` with its default props to a scratch file (license as in
  Step 5):

  ```bash
  npx remotion render Deck "<scratch>/preview.mp4" --frames=0-29 --license-key=<license> --is-production=false
  ```

  If it fails, use the `remotion-best-practices` skill to find the cause (often an incomplete
  `npm install`) and fix it before writing the deck. Never fix it by editing the template.

How the template works and how to preview it: [references/remotion-template.md](references/remotion-template.md).

## Step 3: Write the deck

Create `run_dir` if needed and write `<run_dir>/deck.json`, following
[references/slides-and-narration.md](references/slides-and-narration.md) for slides and narration and the
shape of [assets/deck.example.json](assets/deck.example.json): `version` 1, `fps` 30, `width` 1920,
`height` 1080, `pauseSeconds` 0.6, `voice` with the preset's `voice_id` and `model_id`, the preset's
`theme`, and the `slides`.

If `<run_dir>/deck.json` exists from an earlier render of the same input, read it first and keep the
narration word for word for slides whose content did not change, so their audio stays cached.

Show the user a table of slide number, type, title and narration, then continue unless they object.

## Step 4: Voice the narration

```bash
python3 -I "<skill-dir>/scripts/deck.py" prepare --deck "<run_dir>/deck.json" --public-dir "<public_dir>" --root "<root>"
```

It sets each slide's `audio` to a cache path named by voice, model and narration, copies the logo into
`public_dir`, and prints `{"missing": [{"index", "path", "text"}, …], "cached": N}`. Exit 1: show the
`ERROR` line and fix the deck.

For **each** entry in `missing`, and only those, run (with `ELEVENLABS_API_KEY` in the environment):

```bash
npx -y @elevenlabs/cli@1.11.0 text-to-speech convert --voice-id "<voice_id>" --model-id "<model_id>" --text '<text>' --output "<path>.part"
```

Only when the command succeeds, rename `<path>.part` to `<path>`. The cache counts any file at `<path>` as
voiced, so a failed or interrupted call must never leave one there. If a call fails, delete `<path>.part`,
then retry once; if it fails again, show the error and stop. `prepare` also deletes stale `.part` files.

Pass `<text>` as one single argument, exactly as given in `missing`. Never build the command by pasting the
narration into a shell string where quotes, `$` or backticks could be interpreted: quote it so the shell
passes it unchanged (in a POSIX shell, single quotes, with each `'` written as `'\''`). Then:

```bash
python3 -I "<skill-dir>/scripts/deck.py" finalize --deck "<run_dir>/deck.json" --public-dir "<public_dir>"
```

It measures every audio file, writes `durationInSeconds` into the deck and prints the slide count and the
total seconds. If it reports missing audio, voice those slides and run it again.

## Step 5: Render

In `remotion_dir`, run:

```bash
npx remotion render Deck "<output_path>" --props="<run_dir>/deck.json" --public-dir="<public_dir>" --license-key=<license>
```

- `<license>`: if the `LICENSE` line from Step 0 says the key comes from `REMOTION_LICENSE_KEY`, pass the
  variable, never its text: `--license-key="$REMOTION_LICENSE_KEY"`. When the key is only in
  `<root>/.env`, load that file into this command's environment first (see **Keys** above), or the
  variable expands to nothing. Otherwise pass `--license-key=free-license`. Never pass an empty
  `--license-key=`.
- Use absolute paths. This is the final, production render; any preview or test render adds
  `--is-production=false`.
- If the render fails with a Chrome "Target closed" error, run it once more with `--concurrency=1`.
- For other render errors, use the `remotion-render` skill. Never edit the template for one run.

## Step 6: Verify and report

```bash
python3 -I "<skill-dir>/scripts/verify.py" --video "<output_path>" --deck "<run_dir>/deck.json"
```

- `OK  <path>  <mm:ss>  <N> slides`: report to the user the video path, the duration, the slide count, how
  many narrations were voiced now (the `missing` count) versus reused from the cache (`cached`), and the
  path of `deck.json`.
- `PROBLEM <reason>` (exit 1): show it, fix the cause (usually a stale deck: run `deck.py finalize` again,
  then render), and verify again.

If the user changed something for this run only (voice, theme, context, output format), offer to save it
back to the preset with `settings.py save`.

## Red flags: stop and correct course

| Thought | Reality |
|---|---|
| "A progress figure or a blocker would round this out" | Only what the input says. No invented progress, blockers, names, numbers or IDs. |
| "I'll narrate each bullet as written" | Speak around the bullets in full sentences; do not read them aloud. |
| "The narration is fine, no need to show it" | Show the slide and narration table and give the user a chance to object before voicing. |
| "I'll echo the key to check it is set" | Never print a key. `check_tools.py` reports present or absent only. |
| "Re-voice every slide to be safe" | Voice only the `missing` entries. Cached audio is reused and costs nothing. |
| "This preset needs its own colors in the code" | The theme is data in the preset. Never edit template code per preset. |
| "npm install / the skills are missing, I'll just install them" | Ask first. Install only on the user's go-ahead. |
| "The video already exists, Remotion will overwrite it" | Ask before overwriting an existing video. |
