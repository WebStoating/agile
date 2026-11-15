# How frame extraction works

`scripts/extract_slides.py` produces one image per slide, plus `slides.json`.

## Slide mode (default for slide decks)

1. `ffprobe` reads the duration and resolution.
2. ffmpeg scene detection (`select='gt(scene,T)',showinfo`) lists the moments the picture changes. The script
   tries thresholds `0.02`, then `0.05`, then `0.1`, and keeps the first that gives a plausible number of
   changes: at least one, and at most one per 3 seconds of video on average. The most sensitive threshold
   comes first because slides that differ only in their text score as low as ~0.05. Changes less than 1 second apart
   count as one.
3. Slides often build up gradually (bullets appear one by one), so the first frame of a slide is
   incomplete. The script takes the frame **0.4 s before the next change** (for the last slide, 0.4 s before
   the end of the video). Change it with `--offset`.
4. Large frames are scaled down to a size image-reading models handle at full detail (never scaled up) and saved as
   `frames/slide_NN.jpg`. Old `slide_*.jpg` files in `frames/` are removed first.

## Interval mode (screen recordings, talking heads)

When no threshold gives a plausible count (or with `--mode interval`), the script takes a frame every 5
seconds, compares tiny grayscale thumbnails of neighbouring frames, and drops near-duplicates. Two frames
that differ only in colour at the same brightness can be merged; re-take one if that matters.

## slides.json

```json
{"mode": "slides", "threshold": 0.1, "offset": 0.4, "duration": 312.4, "width": 1920, "height": 1080,
 "slides": [{"index": 1, "file": "frames/slide_01.jpg", "start": 0.0, "end": 14.2, "frame_time": 13.8,
             "title": null}]}
```

Fill in `title` after looking at each frame.

## Troubleshooting

| Symptom | What to do |
|---|---|
| A frame shows a half-built slide or a transition | `--retake N --at <seconds>` with a time later in that slide's range. |
| Two slides were merged into one (a change was missed) | Look at the merged range, then re-take or rerun with `--mode slides`; add the missing slide's content to the spec from the transcript. |
| Far too many "slides" (animations, video inside a slide) | Rerun with `--mode interval`. |
| `--mode slides` says too many scene changes | The video is not a static deck; use `--mode interval`. |
| Speaker video in a corner causes constant changes | Use `--mode interval`; the duplicate check ignores small movement. |
| Error "no readable video stream" | The file is audio-only or damaged; ask the user for the original video. |
