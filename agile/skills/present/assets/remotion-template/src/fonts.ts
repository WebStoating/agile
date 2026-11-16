import { getAvailableFonts } from "@remotion/google-fonts";

export const FALLBACK = "sans-serif";

const pick = (available: string[], wanted: string[]): string[] => {
  const hits = wanted.filter((w) => available.includes(w));
  return hits.length > 0 ? hits : available.slice(0, 1);
};

// Loads a Google Fonts family by its display name ("Inter", "Roboto Slab").
// Resolves to a CSS font-family stack, or the fallback when the family is unknown.
export const loadFontByName = async (name: string): Promise<string> => {
  const entry = getAvailableFonts().find((f) => f.fontFamily.toLowerCase() === name.trim().toLowerCase());
  if (!entry) {
    console.warn(`Font "${name}" is not a Google Fonts family; using ${FALLBACK}`);
    return FALLBACK;
  }
  const font = await entry.load();
  const info = font.getInfo();
  const style = info.fonts.normal ? "normal" : Object.keys(info.fonts)[0];
  const { fontFamily } = font.loadFont(style, {
    weights: pick(Object.keys(info.fonts[style]), ["400", "700"]),
    subsets: pick(info.subsets, ["latin", "latin-ext"]),
  });
  return `${fontFamily}, ${FALLBACK}`;
};
