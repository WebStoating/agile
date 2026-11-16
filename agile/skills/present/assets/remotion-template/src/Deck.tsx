import { useEffect, useState } from "react";
import { AbsoluteFill, Audio, Img, Sequence, staticFile, useDelayRender, useVideoConfig } from "remotion";
import { FALLBACK, loadFontByName } from "./fonts";
import { SlideView } from "./Slides";
import { deckFrames } from "./timing";
import type { DeckProps } from "./types";

const useFontFamily = (name: string): string => {
  const { delayRender, continueRender } = useDelayRender();
  const [handle] = useState(() => delayRender(`Loading font ${name}`));
  const [family, setFamily] = useState(FALLBACK);
  useEffect(() => {
    loadFontByName(name)
      .then(setFamily)
      .catch((err) => {
        console.warn(`Could not load font "${name}": ${err}`);
        setFamily(FALLBACK);
      })
      .finally(() => continueRender(handle));
  }, [name, handle, continueRender]);
  return family;
};

const Logo = ({ src }: { src: string }) => {
  const { height } = useVideoConfig();
  const u = height / 1080;
  return (
    <Img
      src={staticFile(src)}
      style={{ position: "absolute", top: 56 * u, right: 72 * u, height: 72 * u, objectFit: "contain" }}
    />
  );
};

export const Deck = (deck: DeckProps) => {
  const { theme } = deck;
  const fontFamily = useFontFamily(theme.font);
  const frames = deckFrames(deck);
  const starts = frames.map((_, i) => frames.slice(0, i).reduce((a, b) => a + b, 0));

  return (
    <AbsoluteFill style={{ backgroundColor: theme.background, color: theme.text, fontFamily }}>
      {deck.slides.map((slide, i) => (
        <Sequence key={i} name={`${i + 1} ${slide.type}`} from={starts[i]} durationInFrames={frames[i]}>
          {slide.audio ? <Audio src={staticFile(slide.audio)} /> : null}
          <SlideView slide={slide} theme={theme} />
        </Sequence>
      ))}
      {theme.logo ? <Logo src={theme.logo} /> : null}
    </AbsoluteFill>
  );
};
