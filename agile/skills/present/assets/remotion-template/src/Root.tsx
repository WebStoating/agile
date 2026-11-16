import { CalculateMetadataFunction, Composition } from "remotion";
import { Deck } from "./Deck";
import defaultDeck from "./defaultDeck.json";
import { deckFrames } from "./timing";
import type { DeckProps } from "./types";

const calculateMetadata: CalculateMetadataFunction<DeckProps> = ({ props }) => ({
  durationInFrames: Math.max(1, deckFrames(props).reduce((a, b) => a + b, 0)),
  fps: props.fps,
  width: props.width,
  height: props.height,
});

export const RemotionRoot = () => {
  return (
    <Composition
      id="Deck"
      component={Deck}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={defaultDeck as DeckProps}
      calculateMetadata={calculateMetadata}
    />
  );
};
