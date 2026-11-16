# Settings: `.present.json` and the `.present/` folder

## The settings file

`.present.json` sits at the notes root (`<root>`), the folder that holds the user's notes, possibly with week
subfolders below it. It holds named presets, so the user states the purpose of a video once.

```json
{
  "version": 1,
  "presets": {
    "standup": {
      "context": "Daily standup for the backend team: yesterday, today, blockers. Under 2 minutes.",
      "voice": { "voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "model_id": "eleven_v4" },
      "theme": {
        "primary": "#2563EB",
        "background": "#0B1220",
        "text": "#F8FAFC",
        "font": "Inter",
        "logo": "brand/logo.png"
      },
      "output": "{stem}.mp4"
    },
    "weekly": {
      "context": "Weekly summary for stakeholders: highlights, risks, next week. About 3 minutes.",
      "voice": { "voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "model_id": "eleven_v4" },
      "theme": { "primary": "#0F766E", "background": "#FFFFFF", "text": "#111827", "font": "Roboto", "logo": null },
      "output": "videos/{date}-{preset}.mp4"
    }
  },
  "default_preset": "standup"
}
```

Preset fields:

- `context`: who watches, what the update covers, and the target length. It steers the slides and the
  narration length.
- `voice`: the ElevenLabs `voice_id`, a display `name`, and the `model_id`. The `model_id` is saved when the
  preset is created (default `eleven_v4`) and is never changed silently; a new model means new audio for
  every slide.
- `theme`: `primary`, `background` and `text` as hex colors, `font` as a Google Fonts family name, and `logo`
  as a path relative to `<root>` (or `null`). See [remotion-template.md](remotion-template.md).
- `output`: the output format (optional). See the placeholders below.

API keys never go in this file. `ELEVENLABS_API_KEY` and `REMOTION_LICENSE_KEY` come from the environment
or from `<root>/.env`.

`settings.py save --root <root> --preset <name> --json-file <file> [--default]` writes one preset as a
whole (it replaces a preset of the same name) and keeps every other preset. `--default` makes it the
`default_preset`.

## Finding the root

`settings.py resolve` walks up from the input file's folder (or the current folder for pasted text) to the
nearest `.present.json`. If there is none, the folder the walk started from becomes the root when the first
preset is saved. Its JSON reports `root`, `settings_path` and `settings_exists`.

## Choosing the preset

1. The preset the user names (`--preset`).
2. Otherwise `default_preset`.
3. Otherwise the only preset, if there is exactly one.
4. Otherwise ask the user (`status` is `ambiguous`).

`status` is `none` when no preset exists yet (first-run setup) and `unknown` when the named preset does not
exist.

## Output path

The format comes from `--output` (the user's request), else the preset's `output`, else `{stem}.mp4`.

| Placeholder | Value |
|---|---|
| `{stem}` | The input file name without its extension; `PRESENTATION` for pasted text |
| `{date}` | Today, `YYYY-MM-DD` |
| `{preset}` | The preset name (`default` when there is none) |

A relative result resolves against the input file's folder, or the current folder for pasted text. `~` is
expanded; an absolute path is used as is. Any other `{name}` is an error. So by default `week-46/monday.md`
renders to `week-46/monday.mp4`, and pasted text to `./PRESENTATION.mp4`.

`output_exists` means the video is already there (ask before overwriting). `output_parent_missing` means the
folder must be created first.

## The `.present/` folder

```
<root>/.present/
├── remotion/        # the copied Remotion template plus node_modules/, shared by all presets
├── public/          # passed to Remotion with --public-dir
│   ├── audio/       # <sha256 of voice_id, model_id and narration>.mp3, the narration cache
│   └── logo.<ext>   # the current theme's logo, copied by deck.py prepare
└── runs/
    ├── week-46/monday/deck.json      # one folder per input, by its path relative to <root>
    └── _pasted/2026-11-16/deck.json  # pasted text, by date
```

- `run_dir` holds the `deck.json` of the latest render of that input. Keying by the relative path keeps
  `monday.md` in each week folder apart.
- The audio cache is shared by every preset and input. A slide is voiced again only when its voice, model or
  narration text changes.
- `public/` survives a template refresh; only `remotion/` is replaced.
- In a git repository, offer to add `.present/` to `<root>/.gitignore` (`setup_project.py --gitignore`).

## One-off changes

Values the user states in the request (another voice, a different length, an output format) override the
preset for this run only. After the run, offer to save the changed value back to the preset: write the
whole preset with the change to a scratch JSON file and run `settings.py save` with the same preset name.
