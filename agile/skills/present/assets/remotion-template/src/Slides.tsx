import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Slide, Theme } from "./types";

const ENTRANCE_FRAMES = 12;
const MAX_BULLETS = 6;

// 12-frame fade-and-rise; the frame is relative to the slide's <Sequence>.
const Entrance = ({ children }: { children: ReactNode }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  return (
    <AbsoluteFill
      style={{
        opacity: interpolate(frame, [0, ENTRANCE_FRAMES], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
        translate: interpolate(frame, [0, ENTRANCE_FRAMES], [`0px ${(40 * height) / 1080}px`, "0px 0px"], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

export const SlideView = ({ slide, theme }: { slide: Slide; theme: Theme }) => {
  const { height } = useVideoConfig();
  const u = height / 1080;
  const page: CSSProperties = { padding: `${120 * u}px ${160 * u}px`, justifyContent: "center" };
  const title: CSSProperties = { fontSize: 96 * u, fontWeight: 700, lineHeight: 1.1, margin: 0 };
  const bar: CSSProperties = { width: 120 * u, height: 10 * u, backgroundColor: theme.primary, borderRadius: 5 * u };

  let body: ReactNode;
  switch (slide.type) {
    case "title":
      body = (
        <AbsoluteFill style={{ ...page, alignItems: "center", textAlign: "center", gap: 40 * u }}>
          <h1 style={title}>{slide.title}</h1>
          <div style={bar} />
          {slide.subtitle ? <div style={{ fontSize: 56 * u, opacity: 0.8 }}>{slide.subtitle}</div> : null}
        </AbsoluteFill>
      );
      break;
    case "section":
      body = (
        <AbsoluteFill style={{ ...page, gap: 40 * u, borderLeft: `${24 * u}px solid ${theme.primary}` }}>
          <h1 style={title}>{slide.title}</h1>
        </AbsoluteFill>
      );
      break;
    case "bullets":
      body = (
        <AbsoluteFill style={{ ...page, justifyContent: "flex-start", gap: 56 * u }}>
          <h1 style={title}>{slide.title}</h1>
          <div style={bar} />
          <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 28 * u }}>
            {slide.bullets.slice(0, MAX_BULLETS).map((b, i) => (
              <li key={i} style={{ fontSize: 56 * u, lineHeight: 1.25, display: "flex", gap: 32 * u }}>
                <span style={{ color: theme.primary, fontWeight: 700 }}>•</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </AbsoluteFill>
      );
      break;
    case "quote":
      body = (
        <AbsoluteFill style={{ ...page, gap: 48 * u }}>
          {slide.title ? (
            <div style={{ fontSize: 48 * u, fontWeight: 700, color: theme.primary, textTransform: "uppercase", letterSpacing: 4 * u }}>
              {slide.title}
            </div>
          ) : null}
          <blockquote
            style={{ margin: 0, paddingLeft: 48 * u, borderLeft: `${12 * u}px solid ${theme.primary}`, fontSize: 72 * u, lineHeight: 1.25, fontStyle: "italic" }}
          >
            {slide.quote}
          </blockquote>
        </AbsoluteFill>
      );
      break;
  }
  return <Entrance>{body}</Entrance>;
};
