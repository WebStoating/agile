# The Remotion template

The skill ships one small Remotion project in `assets/remotion-template/`. `setup_project.py` copies it to
`<root>/.present/remotion/`, where `npm install` runs once. Every preset and every run uses the same copy;
the deck data, not the code, changes from run to run.

## Files

| File | Purpose |
|---|---|
| `package.json` | Exact pinned versions: `remotion`, `@remotion/cli` and `@remotion/google-fonts` 4.0.544, React 19 |
| `present-template.json` | `templateVersion`, which decides when a copy is refreshed |
| `remotion.config.ts` | JPEG frames, overwrite output |
| `src/index.ts`, `src/Root.tsx` | Registers the single `Deck` composition; `calculateMetadata` sets duration, fps and size from the props |
| `src/Deck.tsx` | Places one sequence per slide with its audio, loads the font, draws the logo |
| `src/Slides.tsx` | The four slide layouts and the entrance animation (fade and rise over 12 frames); at most 6 bullets are drawn |
| `src/timing.ts` | Frame count per slide |
| `src/fonts.ts` | Loads a Google Fonts family by name, falling back to `sans-serif` |
| `src/types.ts` | The deck contract in TypeScript |
| `src/defaultDeck.json` | Default props, so the studio opens without a deck |

## The deck contract

`deck.json` is passed as input props (`--props=<run_dir>/deck.json`). Its shape is
`assets/deck.example.json`, checked by `deck.py` (`pr_lib/deck.py` `load_deck`) and mirrored in
`src/types.ts`:

| Field | Value |
|---|---|
| `version` | `1` |
| `fps`, `width`, `height` | Positive integers; the skill uses 30, 1920 and 1080 |
| `pauseSeconds` | Silence after each slide's narration, a number ≥ 0; the skill uses 0.6 |
| `voice` | `voice_id` and `model_id` from the preset (they are part of the audio cache key) |
| `theme` | Required. `primary`, `background`, `text` and `font` are required strings; `logo` is a string or `null` (below) |
| `slides` | A non-empty list. Each has `type` (`title`, `section`, `bullets`, `quote`), a non-empty `narration`, and that type's fields: `title`, `section` and `bullets` need a non-empty `title`; `bullets` needs 1 to 6 strings in `bullets`; `quote` needs a string `quote`; `subtitle` (title slides) and `title` (quote slides) are optional strings |

The scripts fill in the rest:

- `deck.py prepare` sets each slide's `audio` (`audio/<key>.mp3`, relative to `public/`) and replaces
  `theme.logo` with the name of the copy it put in `public/`.
- `deck.py finalize` sets each slide's `durationInSeconds` from the audio file.

`deck.py prepare` and `finalize` reject a deck that breaks these rules, naming the field, before anything is
rendered. The render fails on a slide without `durationInSeconds`, so always finalize before rendering.

## Timing

Each slide lasts `ceil((durationInSeconds + pauseSeconds) × fps)` frames, and the video is the sum of all
slides. `src/timing.ts` (`slideFrames`) and `pr_lib/deck.py` (`total_frames`) must use the same formula,
because `verify.py` checks the rendered length against it (tolerance 0.5 s).

## Theme

The theme comes from the preset as data, so presets never need code changes.

- `primary`: accent color (accent bars and borders, bullet markers, the quote title). `background` and `text`: slide colors. All
  are CSS colors; hex is safest.
- `font`: a Google Fonts family name as Google lists it, such as `Inter` or `Roboto Slab`. An unknown name
  falls back to `sans-serif` with a warning in the render log.
- `logo`: a path relative to `<root>`, such as `brand/logo.png`, or `null`. `deck.py prepare` copies it to
  `public/logo.<ext>`; it is drawn in the top-right corner of every slide.

## Previewing and test renders

Use the `remotion-studio` skill. Run the studio in `remotion_dir` with the current deck:

```bash
npx remotion studio --props="<run_dir>/deck.json" --public-dir="<public_dir>"
```

After a fresh copy or a template refresh (`setup_project.py` reports `created` or `updated`), SKILL.md
Step 2 renders one second of `Deck` with its default props (`src/defaultDeck.json`, no audio needed) to
confirm the install works.

A test render (a few seconds, or a quick check after a template change) is never a production render:

```bash
npx remotion render Deck "<scratch>/test.mp4" --props="<run_dir>/deck.json" --public-dir="<public_dir>" --license-key=free-license --is-production=false --frames=0-89
```

## Changing the template

The template is maintained in the skill (`assets/remotion-template/`), never in a user's copy and never per
preset. Use the Remotion skills (`remotion-best-practices`) for the code.

- Change `templateVersion` in `present-template.json` whenever any template file changes. Otherwise the
  copies in users' notes folders are not refreshed. `setup_project.py` replaces everything except
  `node_modules/` when the version differs, and asks for `npm install` again when `package.json` changed.
- Keep every dependency an exact version (no `^` or `~`), with all `@remotion/*` packages on the same
  version as `remotion`.
- A new slide type or deck field needs the same change in `src/types.ts`, `pr_lib/deck.py`,
  `assets/deck.example.json` and [slides-and-narration.md](slides-and-narration.md).
