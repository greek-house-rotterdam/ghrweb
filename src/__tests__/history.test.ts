import { describe, it, expect } from "vitest";
import { existsSync, readFileSync, readdirSync } from "fs";
import { join } from "path";
import { parse } from "yaml";

// The History page (#200): timeline cards have no photo. A photo goes in the
// history page the card links to. These checks read the content files; the
// built pages are checked in site.test.ts, after the build.

const ROOT = join(__dirname, "../..");
const MILESTONES = join(ROOT, "src/content/history-milestones");
const SECTIONS = join(ROOT, "src/content/history-sections");
const LANGS = ["gr", "nl", "en"] as const;

function entries(dir: string): { name: string; data: Record<string, unknown>; body: string }[] {
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .map((f) => {
      const raw = readFileSync(join(dir, f), "utf-8");
      const match = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
      if (!match) throw new Error(`No frontmatter in ${dir}/${f}`);
      return { name: f.replace(/\.md$/, ""), data: parse(match[1]) ?? {}, body: match[2] };
    });
}

describe("history timeline cards", () => {
  for (const lang of LANGS) {
    for (const { name, data } of entries(join(MILESTONES, lang))) {
      it(`${lang}/${name}.md has no photo of its own`, () => {
        expect(data).not.toHaveProperty("image");
      });
    }
  }

  // Dutch and English pages come from the translation workflow, so only the
  // Greek ones must exist as soon as a card links to them.
  for (const { name, data } of entries(join(MILESTONES, "gr"))) {
    if (!data.linkedSection) continue;
    it(`gr/${name}.md links to a Greek history page that exists`, () => {
      expect(existsSync(join(SECTIONS, "gr", `${data.linkedSection}.md`))).toBe(true);
    });
  }
});

describe("history pages", () => {
  for (const lang of LANGS) {
    for (const { name, body } of entries(join(SECTIONS, lang))) {
      const images = [...body.matchAll(/!\[[^\]]*\]\((\/images\/[^)\s]+)\)/g)].map((m) => m[1]);
      if (images.length === 0) continue;
      it(`${lang}/${name}.md shows only photos that exist`, () => {
        for (const src of images) {
          expect(existsSync(join(ROOT, "public", src)), src).toBe(true);
        }
      });
    }
  }
});
