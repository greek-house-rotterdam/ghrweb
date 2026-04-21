import { describe, it, expect } from "vitest";
import { execSync } from "child_process";
import { readFileSync, readdirSync } from "fs";
import { join } from "path";

const ROOT = join(__dirname, "../..");
const CONTENT = join(ROOT, "src/content");

// --- Helpers ---

function parseFrontmatter(filePath: string): Record<string, unknown> {
  const raw = readFileSync(filePath, "utf-8");
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) throw new Error(`No frontmatter in ${filePath}`);

  const fm: Record<string, unknown> = {};
  for (const line of match[1].split("\n")) {
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const key = line.slice(0, colonIdx).trim();
    let value: unknown = line.slice(colonIdx + 1).trim();

    // Strip surrounding quotes
    if (
      typeof value === "string" &&
      value.startsWith('"') &&
      value.endsWith('"')
    ) {
      value = value.slice(1, -1);
    }

    // Coerce known types
    if (value === "true") value = true;
    else if (value === "false") value = false;
    else if (typeof value === "string" && /^\d+$/.test(value))
      value = parseInt(value, 10);

    fm[key] = value;
  }
  return fm;
}

function getMarkdownFiles(dir: string): string[] {
  const files: string[] = [];
  try {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) files.push(...getMarkdownFiles(full));
      else if (entry.name.endsWith(".md")) files.push(full);
    }
  } catch {
    // directory doesn't exist
  }
  return files;
}

// --- Tests ---

// The build runs Astro's content layer, which validates every markdown file
// against the Zod schemas in content.config.ts. A failing build means invalid
// content, broken templates, or misconfigured collections — no need for a
// separate schema test suite that duplicates what Astro already enforces.
describe("build smoke test", () => {
  it("astro build completes without errors", () => {
    const result = execSync("npm run build 2>&1", {
      cwd: ROOT,
      timeout: 60_000,
      encoding: "utf-8",
    });
    expect(result).toContain("[build] Complete!");
  });
}, 90_000);

// The build does NOT catch a file whose lang field doesn't match its directory.
// A file at news/gr/post.md with lang: nl would build fine but display Greek
// content under the Dutch language route — a silent, user-facing bug.
describe("content files have correct lang", () => {
  const langDirs = ["gr", "nl", "en"] as const;

  for (const collection of ["news", "events", "activities", "faq", "resources"]) {
    for (const lang of langDirs) {
      const dir = join(CONTENT, collection, lang);
      const files = getMarkdownFiles(dir);

      for (const file of files) {
        const relative = file.replace(ROOT + "/", "");
        it(`${relative} has lang: ${lang}`, () => {
          const fm = parseFrontmatter(file);
          expect(fm.lang).toBe(lang);
        });
      }
    }
  }
});
