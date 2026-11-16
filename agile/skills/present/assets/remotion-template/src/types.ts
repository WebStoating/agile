// Mirrors the deck.json contract read by pr_lib/deck.py load_deck (see assets/deck.example.json).

export type SlideType = "title" | "section" | "bullets" | "quote";

type SlideBase = {
  narration: string;
  // Set by `deck.py prepare`: "audio/<key>.mp3", relative to the --public-dir folder.
  audio?: string;
  // Set by `deck.py finalize`: the measured length of the narration audio.
  durationInSeconds?: number;
};

export type TitleSlide = SlideBase & { type: "title"; title: string; subtitle?: string };
export type SectionSlide = SlideBase & { type: "section"; title: string };
export type BulletsSlide = SlideBase & { type: "bullets"; title: string; bullets: string[] };
export type QuoteSlide = SlideBase & { type: "quote"; title?: string; quote: string };

export type Slide = TitleSlide | SectionSlide | BulletsSlide | QuoteSlide;

export type Theme = {
  primary: string;
  background: string;
  text: string;
  // A Google Fonts family name; unknown names fall back to sans-serif.
  font: string;
  // A file in the --public-dir folder (for example "logo.png"), or null for no logo.
  logo: string | null;
};

export type Voice = { voice_id: string; model_id: string };

export type DeckProps = {
  version: number;
  fps: number;
  width: number;
  height: number;
  pauseSeconds: number;
  voice: Voice;
  theme: Theme;
  slides: Slide[];
};
