import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";
import { parse as parseYaml } from "yaml";

const ROOT = join(__dirname, "../..");
const config = parseYaml(
  readFileSync(join(ROOT, "public/admin/config.yml"), "utf-8"),
);

interface CmsField {
  name: string;
  widget: string;
  required?: boolean;
  pattern?: [string, string];
  options?: string[];
  default?: unknown;
}

interface CmsCollection {
  name: string;
  label: string;
  folder: string;
  create: boolean;
  slug: string;
  fields: CmsField[];
}

const collections: CmsCollection[] = config.collections;

const LANGUAGES = ["gr", "nl", "en"] as const;
// history-milestones, history-sections, and about-sections are intentionally
// absent: they're programmatic-only collections, not exposed in Decap.
const CONTENT_TYPES = [
  "news",
  "event-translations",
  "activities",
  "faq",
  "resources",
] as const;

function getCollection(type: string, lang: string): CmsCollection {
  return collections.find((c) => c.name === `${type}-${lang}`)!;
}

function getFieldNames(col: CmsCollection, excludeBody = true): string[] {
  return col.fields
    .filter((f) => !excludeBody || f.name !== "body")
    .map((f) => f.name);
}

function getField(col: CmsCollection, name: string): CmsField | undefined {
  return col.fields.find((f) => f.name === name);
}

function extractMaxLength(pattern?: [string, string]): number | null {
  if (!pattern) return null;
  const match = pattern[0].match(/\{0,(\d+)\}/);
  return match ? parseInt(match[1], 10) : null;
}

// Expected schema structure — derived from content.config.ts.
// If content.config.ts changes, update these expectations to match.
const EXPECTED_FIELDS: Record<
  string,
  {
    required: string[];
    optional: string[];
    maxLengths?: Record<string, number>;
    enums?: Record<string, string[]>;
    defaults?: Record<string, unknown>;
  }
> = {
  news: {
    required: ["title", "description", "date", "lang"],
    optional: ["image"],
    maxLengths: { title: 100, description: 200 },
  },
  "event-translations": {
    required: ["tt_event_id", "title", "description", "lang"],
    optional: [],
    maxLengths: { title: 100, description: 200 },
  },
  activities: {
    required: ["title", "description", "lang"],
    optional: ["image", "emoji", "schedule", "order"],
    maxLengths: { title: 100, description: 200 },
    defaults: { order: 100 },
  },
  faq: {
    required: ["question", "answer", "lang"],
    optional: ["order"],
    maxLengths: { question: 200 },
    defaults: { order: 100 },
  },
  resources: {
    required: ["title", "description", "category", "lang"],
    optional: ["order"],
    maxLengths: { title: 100, description: 200 },
    defaults: { order: 100 },
  },
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Decap CMS config — global settings", () => {
  it("uses github backend", () => {
    expect(config.backend.name).toBe("github");
  });

  it("targets the correct repo", () => {
    expect(config.backend.repo).toBe("greek-house-rotterdam/ghrweb");
  });

  it("targets the main branch", () => {
    expect(config.backend.branch).toBe("main");
  });

  it("uses editorial workflow", () => {
    expect(config.publish_mode).toBe("editorial_workflow");
  });

  it("stores media in public/images", () => {
    expect(config.media_folder).toBe("public/images");
    expect(config.public_folder).toBe("/images");
  });
});

describe("Decap CMS config — collection coverage", () => {
  for (const type of CONTENT_TYPES) {
    for (const lang of LANGUAGES) {
      it(`has collection ${type}-${lang}`, () => {
        const col = getCollection(type, lang);
        expect(col).toBeDefined();
      });
    }
  }

  it("has exactly 15 collections (5 types x 3 languages, programmatic ones excluded)", () => {
    expect(collections).toHaveLength(CONTENT_TYPES.length * LANGUAGES.length);
  });
});

describe("Decap CMS config — folder paths", () => {
  for (const type of CONTENT_TYPES) {
    for (const lang of LANGUAGES) {
      it(`${type}-${lang} points to src/content/${type}/${lang}`, () => {
        const col = getCollection(type, lang);
        expect(col.folder).toBe(`src/content/${type}/${lang}`);
      });
    }
  }
});

// "View Preview" in the editorial workflow. Decap takes the base URL from the
// `deploy/preview` commit status (see .github/workflows/preview-status.yml)
// and appends preview_path.
const PREVIEW_PATH: Record<string, (lang: string) => string> = {
  news: (lang) => `${lang}/news/{{slug}}`,
  "event-translations": (lang) => `${lang}/events/{{slug}}`,
  activities: (lang) => `${lang}/activities/{{slug}}`,
  faq: (lang) => `${lang}/faq`,
  resources: (lang) => `${lang}/resources`,
};

describe("Decap CMS config — preview", () => {
  it("sets site_url and display_url to the production URL", () => {
    const url = "https://ghrweb.enosi-ellinon-ollandias.workers.dev";
    expect(config.site_url).toBe(url);
    expect(config.display_url).toBe(url);
  });

  for (const type of CONTENT_TYPES) {
    for (const lang of LANGUAGES) {
      it(`${type}-${lang} has preview_path ${PREVIEW_PATH[type](lang)}`, () => {
        const col = getCollection(type, lang) as CmsCollection & {
          preview_path?: string;
          editor?: { preview?: boolean };
        };
        expect(col.preview_path).toBe(PREVIEW_PATH[type](lang));
        expect(col.editor?.preview).toBe(false);
      });
    }
  }
});

describe("Decap CMS config — all language variants are consistent", () => {
  for (const type of CONTENT_TYPES) {
    it(`all ${type} collections have identical field names`, () => {
      const fieldSets = LANGUAGES.map((lang) => {
        const col = getCollection(type, lang);
        return getFieldNames(col).sort().join(",");
      });
      expect(fieldSets[0]).toBe(fieldSets[1]);
      expect(fieldSets[1]).toBe(fieldSets[2]);
    });

    it(`all ${type} collections have identical widget types`, () => {
      const widgetSets = LANGUAGES.map((lang) => {
        const col = getCollection(type, lang);
        return col.fields
          .filter((f) => f.name !== "body")
          .map((f) => `${f.name}:${f.widget}`)
          .sort()
          .join(",");
      });
      expect(widgetSets[0]).toBe(widgetSets[1]);
      expect(widgetSets[1]).toBe(widgetSets[2]);
    });
  }
});

describe("Decap CMS config — field sync with content schemas", () => {
  for (const type of CONTENT_TYPES) {
    describe(type, () => {
      const col = getCollection(type, "gr"); // use gr as representative
      const expected = EXPECTED_FIELDS[type];
      const allExpected = [...expected.required, ...expected.optional].sort();

      it("CMS fields (excluding body) match schema fields", () => {
        const cmsFields = getFieldNames(col).sort();
        expect(cmsFields).toEqual(allExpected);
      });

      for (const field of expected.required) {
        it(`${field} is required`, () => {
          const f = getField(col, field);
          expect(f).toBeDefined();
          // In CMS config, fields are required by default (required !== false)
          // Hidden fields with defaults are still "required" in schema sense
          if (f!.widget !== "hidden") {
            expect(f!.required).not.toBe(false);
          }
        });
      }

      for (const field of expected.optional) {
        it(`${field} is optional or has a default`, () => {
          const f = getField(col, field);
          expect(f).toBeDefined();
          const isOptional = f!.required === false;
          const hasDefault = f!.default !== undefined;
          expect(isOptional || hasDefault).toBe(true);
        });
      }
    });
  }
});

describe("Decap CMS config — max length constraints", () => {
  for (const type of CONTENT_TYPES) {
    const expected = EXPECTED_FIELDS[type];
    if (!expected.maxLengths) continue;

    for (const [field, maxLen] of Object.entries(expected.maxLengths)) {
      it(`${type}.${field} enforces max ${maxLen} characters`, () => {
        const col = getCollection(type, "gr");
        const f = getField(col, field);
        expect(f).toBeDefined();
        const cmsMax = extractMaxLength(f!.pattern);
        expect(cmsMax).toBe(maxLen);
      });
    }
  }
});

describe("Decap CMS config — enum options", () => {
  const enumTypes = CONTENT_TYPES.filter((t) => EXPECTED_FIELDS[t].enums);
  if (enumTypes.length === 0) {
    // No enum-bearing fields are currently exposed in Decap. Vitest
    // requires at least one test per describe block, so this placeholder
    // keeps the suite passing until an enum field is added back.
    it.skip("no enum-bearing fields exposed in Decap", () => {});
    return;
  }
  for (const type of enumTypes) {
    for (const [field, options] of Object.entries(EXPECTED_FIELDS[type].enums!)) {
      it(`${type}.${field} has correct options`, () => {
        const col = getCollection(type, "gr");
        const f = getField(col, field);
        expect(f).toBeDefined();
        expect(f!.options).toEqual(options);
      });
    }
  }
});

describe("Decap CMS config — default values", () => {
  for (const type of CONTENT_TYPES) {
    const expected = EXPECTED_FIELDS[type];
    if (!expected.defaults) continue;

    for (const [field, defaultVal] of Object.entries(expected.defaults)) {
      it(`${type}.${field} defaults to ${JSON.stringify(defaultVal)}`, () => {
        const col = getCollection(type, "gr");
        const f = getField(col, field);
        expect(f).toBeDefined();
        expect(f!.default).toEqual(defaultVal);
      });
    }
  }
});

describe("Decap CMS config — language defaults", () => {
  for (const type of CONTENT_TYPES) {
    for (const lang of LANGUAGES) {
      it(`${type}-${lang} has hidden lang field defaulting to "${lang}"`, () => {
        const col = getCollection(type, lang);
        const langField = getField(col, "lang");
        expect(langField).toBeDefined();
        expect(langField!.widget).toBe("hidden");
        expect(langField!.default).toBe(lang);
      });
    }
  }
});

// Greek is the only source language: new entries are written in Greek and
// NL/EN are generated from it. NL/EN entries can still be edited, to fix a
// translation, but not created.
describe("Decap CMS config — only Greek collections allow creation", () => {
  for (const col of collections) {
    const isGreek = col.name.endsWith("-gr");
    it(`${col.name} has create: ${isGreek}`, () => {
      expect(col.create).toBe(isGreek);
    });
  }
});

// The editor is loaded from a CDN, so it must be pinned to an exact version
// and integrity-checked; otherwise it changes unreviewed on every upstream
// release.
describe("Decap CMS admin page — pinned script", () => {
  const html = readFileSync(join(ROOT, "public/admin/index.html"), "utf-8");
  const tags = [...html.matchAll(/<script\b[^>]*\bsrc="[^"]*"[^>]*>/g)].map(
    (m) => m[0],
  );
  const decap = tags.find((t) => /decap-cms/.test(t));

  it("loads decap-cms from an external script tag", () => {
    expect(decap).toBeDefined();
  });

  it("pins decap-cms to an exact version (no ^, ~ or latest)", () => {
    expect(decap).toMatch(
      /src="https:\/\/unpkg\.com\/decap-cms@\d+\.\d+\.\d+\/dist\/decap-cms\.js"/,
    );
  });

  it("has an SRI hash and anonymous CORS on every external script", () => {
    expect(tags.length).toBeGreaterThan(0);
    for (const t of tags) {
      expect(t).toMatch(/integrity="sha384-[A-Za-z0-9+/]+=*"/);
      expect(t).toMatch(/crossorigin="anonymous"/);
    }
  });
});
