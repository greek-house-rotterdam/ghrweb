import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";
import { arrowState, scrollStep } from "../lib/card-row";

const ROOT = join(__dirname, "../..");
const read = (path: string) => readFileSync(join(ROOT, path), "utf-8");

describe("arrowState", () => {
  it("hides the arrows when the row fits on the screen", () => {
    expect(arrowState(0, 800, 800).show).toBe(false);
    expect(arrowState(0, 800.5, 800).show).toBe(false);
  });

  it("at the start, only the right arrow works", () => {
    expect(arrowState(0, 2000, 800)).toEqual({ show: true, atStart: true, atEnd: false });
  });

  it("in the middle, both arrows work", () => {
    expect(arrowState(600, 2000, 800)).toEqual({ show: true, atStart: false, atEnd: false });
  });

  it("at the end, only the left arrow works, even with a fractional position", () => {
    expect(arrowState(1199.6, 2000, 800)).toEqual({ show: true, atStart: false, atEnd: true });
  });
});

describe("scrollStep", () => {
  it("scrolls by the whole cards in view", () => {
    // 3 cards of 374px with 24px gaps fit in 1248px.
    expect(scrollStep(1248, 374, 24)).toBe(3 * 398);
  });

  it("scrolls by at least one card when a card is wider than the view", () => {
    expect(scrollStep(300, 400, 24)).toBe(424);
  });

  it("falls back to the view width when there is no card", () => {
    expect(scrollStep(800, 0, 0)).toBe(800);
  });
});

describe("CardRow component", () => {
  const src = read("src/components/CardRow.astro");

  it("never moves by itself (no timers)", () => {
    expect(src).not.toMatch(/setInterval|setTimeout|requestAnimationFrame/);
  });

  it("keeps the arrows hidden until the script shows them", () => {
    expect(src).toMatch(/<div data-arrows hidden\b/);
  });

  it("respects reduced motion", () => {
    expect(src).toContain("prefers-reduced-motion");
  });
});

describe("home page activities", () => {
  const home = read("src/pages/[lang]/index.astro");
  const query = home.slice(home.indexOf("const activities"), home.indexOf("---", home.indexOf("const activities")));

  it("shows all visible activities, not just the first few", () => {
    expect(query).toContain('getVisible("activities")');
    expect(query).not.toMatch(/\.slice\(/);
  });

  it("puts them in a CardRow", () => {
    expect(home).toMatch(/<CardRow lang=\{lang\}>[\s\S]*activities\.map[\s\S]*<\/CardRow>/);
  });
});
