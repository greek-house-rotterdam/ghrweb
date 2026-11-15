import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "fs";
import { join, relative } from "path";
import { EDITABLE_COLLECTIONS, isVisible } from "../lib/visible";

const ROOT = join(__dirname, "../..");
const PAGES = join(ROOT, "src/pages");

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

// "Hide from site" only works if no page reads these collections around the
// filter. A new page must use getVisible() from src/lib/visible.ts.
describe("pages read the editable collections through getVisible()", () => {
  const direct = new RegExp(`getCollection\\(\\s*["'](${EDITABLE_COLLECTIONS.join("|")})["']`);
  for (const file of files(PAGES)) {
    it(`${relative(ROOT, file)} doesn't bypass "Hide from site"`, () => {
      expect(readFileSync(file, "utf-8")).not.toMatch(direct);
    });
  }
});
