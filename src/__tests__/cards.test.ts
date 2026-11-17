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

// A card that shows only the start of a text (an excerpt, cut with "…") must
// open the whole text. Otherwise the rest, such as links and contact details,
// can't be reached: this happened on the resources page.
const CARD = /<BrutCard\b((?:=>|[^>])*)>([\s\S]*?)<\/BrutCard>/g;
const SHORTENS_TEXT = /\b(descriptionOrExcerpt|excerpt)\(/;

describe("cards: a card that shortens a text links to the whole text", () => {
  const excerptCards: string[] = [];

  for (const file of SOURCES) {
    const rel = relative(ROOT, file);
    const src = readFileSync(file, "utf-8");
    for (const [, attributes, inner] of src.matchAll(CARD)) {
      if (!SHORTENS_TEXT.test(inner)) continue;
      excerptCards.push(rel);
      it(`${rel}: the card with an excerpt has an href`, () => {
        expect(attributes).toMatch(/\bhref=/);
      });
    }
  }

  it("finds the excerpt cards (news, activities, resources)", () => {
    for (const page of [
      "src/pages/[lang]/index.astro",
      "src/pages/[lang]/news/index.astro",
      "src/pages/[lang]/activities.astro",
      "src/pages/[lang]/resources.astro",
    ]) {
      expect(excerptCards).toContain(page);
    }
  });
});

// Everything that presses in also shows where keyboard focus is (#122).
describe("clickable things show keyboard focus", () => {
  for (const [rel, count] of Object.entries(CLICKABLE_SHADOWS)) {
    it(`${rel}: every shadowed element has a focus-visible style`, () => {
      const src = readFileSync(join(ROOT, rel), "utf-8");
      const focus = src.match(/focus-visible:(outline-4|ring-4)/g) ?? [];
      // BrutButton holds both sizes in one class list.
      expect(focus.length).toBeGreaterThanOrEqual(rel.endsWith("BrutButton.astro") ? 1 : count);
    });
  }
});
