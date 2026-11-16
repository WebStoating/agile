import type { DeckProps } from "./types";

// Frames for one slide: its narration plus the pause after it, rounded up.
// Must stay identical to pr_lib/deck.py total_frames, which verify.py uses to check the rendered length.
export const slideFrames = (seconds: number, pause: number, fps: number): number =>
  Math.ceil((seconds + pause) * fps);

export const slideSeconds = (deck: DeckProps, index: number): number => {
  const seconds = deck.slides[index].durationInSeconds;
  if (typeof seconds !== "number" || !(seconds > 0)) {
    throw new Error(`slide ${index + 1} has no durationInSeconds; run deck.py finalize first`);
  }
  return seconds;
};

export const deckFrames = (deck: DeckProps): number[] =>
  deck.slides.map((_, i) => slideFrames(slideSeconds(deck, i), deck.pauseSeconds, deck.fps));
