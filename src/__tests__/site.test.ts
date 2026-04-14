import { describe, it, expect } from "vitest";
import { execSync } from "child_process";
import { readFileSync, readdirSync } from "fs";
import { join } from "path";
import { z } from "zod";

const ROOT = join(__dirname, "../..");
const CONTENT = join(ROOT, "src/content");

// --- Zod schemas (mirror content.config.ts, without astro:content imports) ---

const langEnum = z.enum(["gr", "nl", "en"]);

const newsSchema = z.object({
  title: z.string().max(100),
  description: z.string().max(200),
  date: z.coerce.date(),
  image: z.string().optional(),
  lang: langEnum,
});

const eventsSchema = z.object({
  title: z.string().max(100),
  description: z.string().max(200),
  date: z.coerce.date(),
  endDate: z.coerce.date().optional(),
  location: z.string().optional(),
  category: z
    .enum(["workshop", "social", "cultural", "class", "meetup", "other"])
    .default("other"),
  price: z.string().optional(),
  registrationRequired: z.boolean().default(false),
  image: z.string().optional(),
  lang: langEnum,
});

const activitiesSchema = z.object({
  title: z.string().max(100),
  description: z.string().max(200),
  emoji: z.string().optional(),
  schedule: z.string().optional(),
  image: z.string().optional(),
  order: z.number().default(100),
  lang: langEnum,
});

const faqSchema = z.object({
  question: z.string().max(200),
  answer: z.string(),
  order: z.number().default(100),
  lang: langEnum,
});

const resourcesSchema = z.object({
  title: z.string().max(100),
  description: z.string().max(200),
  category: z.string(),
  order: z.number().default(100),
  lang: langEnum,
});

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

describe("build smoke test", () => {
  it("astro build completes without errors", () => {
    const result = execSync("npm run build", {
      cwd: ROOT,
      timeout: 60_000,
      encoding: "utf-8",
    });
    expect(result).toContain("[build] Complete!");
  });
}, 90_000);

describe("content schema validation", () => {
  const collections = [
    { name: "news", dir: join(CONTENT, "news"), schema: newsSchema },
    { name: "events", dir: join(CONTENT, "events"), schema: eventsSchema },
    {
      name: "activities",
      dir: join(CONTENT, "activities"),
      schema: activitiesSchema,
    },
    { name: "faq", dir: join(CONTENT, "faq"), schema: faqSchema },
    {
      name: "resources",
      dir: join(CONTENT, "resources"),
      schema: resourcesSchema,
    },
  ];

  for (const { name, dir, schema } of collections) {
    describe(name, () => {
      const files = getMarkdownFiles(dir);

      it("has at least one content file", () => {
        expect(files.length).toBeGreaterThan(0);
      });

      for (const file of files) {
        const relative = file.replace(ROOT + "/", "");
        it(`${relative} has valid frontmatter`, () => {
          const fm = parseFrontmatter(file);
          const result = schema.safeParse(fm);
          if (!result.success) {
            throw new Error(
              `Invalid frontmatter in ${relative}:\n${result.error.issues.map((i) => `  ${i.path.join(".")}: ${i.message}`).join("\n")}`,
            );
          }
        });
      }
    });
  }
});

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
