import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "fs";
import { join, relative } from "path";
import { EDITABLE_COLLECTIONS, isVisible } from "../lib/visible";

const ROOT = join(__dirname, "../..");
const PAGES = join(ROOT, "src/pages");
const COMPONENTS = join(ROOT, "src/components");

function files(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const full = join(dir, e.name);
    if (e.isDirectory()) return files(full);
    return /\.(astro|ts|js)$/.test(e.name) ? [full] : [];
  });
}

describe("isVisible", () => {
  it("hides only entries marked hidden", () => {
    expect(isVisible({ data: { hidden: true } })).toBe(false);
    expect(isVisible({ data: { hidden: false } })).toBe(true);
    expect(isVisible({ data: {} })).toBe(true);
  });
});

// "Hide from site" only works if no page or component reads these collections
// around the filter. New code must use getVisible() from src/lib/visible.ts.
describe("pages and components read the editable collections through getVisible()", () => {
  const direct = new RegExp(`getCollection\\(\\s*["'](${EDITABLE_COLLECTIONS.join("|")})["']`);
  for (const file of [...files(PAGES), ...files(COMPONENTS)]) {
    it(`${relative(ROOT, file)} doesn't bypass "Hide from site"`, () => {
      expect(readFileSync(file, "utf-8")).not.toMatch(direct);
    });
  }
});

// The menus link "News" only while there are posts (hasNews), so visitors
// never land on an empty News page (agreed with the managers, 2026-11-17).
describe("menus link News only through hasNews()", () => {
  for (const name of ["Header.astro", "Footer.astro"]) {
    it(`${name} links News only when there are posts`, () => {
      const lines = readFileSync(join(COMPONENTS, name), "utf-8").split("\n");
      const newsLinks = lines.filter((line) => line.includes('"nav.news"'));
      expect(newsLinks.length).toBeGreaterThan(0);
      for (const line of newsLinks) expect(line).toContain("hasNews(lang)");
    });
  }
});
