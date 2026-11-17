import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "fs";
import { join, relative } from "path";

// One line between sections. Where two full-width parts of a page meet there
// is exactly one 4px black line, drawn by the upper part (border-b-4). The
// footer draws the line above it (border-t-4). A top line on a section would
// double the line above it, or leave none when the section above is hidden
// (the home page's news and events hide while empty).

const ROOT = join(__dirname, "../..");

function files(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const full = join(dir, e.name);
    if (e.isDirectory()) return files(full);
    return e.name.endsWith(".astro") ? [full] : [];
  });
}

describe("sections draw their line at the bottom only", () => {
  for (const file of files(join(ROOT, "src/pages"))) {
    const rel = relative(ROOT, file);
    const src = readFileSync(file, "utf-8");

    it(`${rel} has no top line on a section`, () => {
      const tags = src.match(/<(section|article)\b[^>]*>/g) ?? [];
      for (const tag of tags) {
        expect(tag).not.toMatch(/\bborder-(t|y)-4\b/);
      }
    });
  }
});
