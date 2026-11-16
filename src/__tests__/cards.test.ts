import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "fs";
import { join, relative } from "path";

// Raised = clickable, flat = read (#122). The hard offset shadow and the
// press-in belong to links and buttons only; BrutCard adds them when it gets
// an href. These checks keep pages from bringing the old patterns back.

const ROOT = join(__dirname, "../..");

function files(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const full = join(dir, e.name);
    if (e.isDirectory()) return e.name === "starwind" ? [] : files(full);
    return e.name.endsWith(".astro") ? [full] : [];
  });
}

const SOURCES = [...files(join(ROOT, "src/pages")), ...files(join(ROOT, "src/components"))];

// Hand-written shadows are allowed only on things that are clickable.
const CLICKABLE_SHADOWS: Record<string, number> = {
  "src/components/BrutButton.astro": 2,
  "src/components/BrutCard.astro": 1,
  "src/components/Header.astro": 2, // "Become a member" button, menu button
  "src/components/Footer.astro": 1, // social icon links
  "src/pages/[lang]/faq.astro": 1, // accordion questions open on click
};

describe("cards: raised = clickable", () => {
  for (const file of SOURCES) {
    const rel = relative(ROOT, file);
    const src = readFileSync(file, "utf-8");

    it(`${rel} doesn't wrap a card in its own link`, () => {
      expect(src).not.toMatch(/<a\b[^>]*>\s*<BrutCard/);
    });

    it(`${rel} uses only the current BrutCard props`, () => {
      expect(src).not.toMatch(/<BrutCard[^>]*\b(interactive|tag=)/);
    });

    it(`${rel} puts offset shadows only on clickable things`, () => {
      const shadows = src.match(/shadow-\[\d+px_\d+px_0_0_#000\]/g) ?? [];
      expect(shadows.length).toBe(CLICKABLE_SHADOWS[rel] ?? 0);
    });
  }
});
