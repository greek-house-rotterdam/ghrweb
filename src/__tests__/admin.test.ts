import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";
import { parse as parseYaml } from "yaml";
import { t, type UIKey } from "../i18n/ui";

const ROOT = join(__dirname, "../..");
const config = parseYaml(
  readFileSync(join(ROOT, "public/admin/config.yml"), "utf-8"),
);

interface CmsField {
  name: string;
  widget: string;
  required?: boolean;
  pattern?: [string, string];
  hint?: string;
  options?: string[];
  default?: unknown;
}

interface CmsCollection {
  name: string;
  label: string;
  folder: string;
  create: boolean;
  delete?: boolean;
  slug: string;
  fields: CmsField[];
}

// Folder collections hold one file per entry (news, FAQ, ...). The site
// settings collection is a files collection: it has no folder and no `create`.
// It is checked in site-settings.test.ts.
const collections: CmsCollection[] = config.collections.filter(
  (c: { folder?: string }) => c.folder !== undefined,
);

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
    required: ["title", "date", "lang"],
    optional: ["description", "image", "url_slug", "hidden"],
    maxLengths: { title: 100, description: 200 },
    defaults: { hidden: false },
  },
  "event-translations": {
    required: ["tt_event_id", "title", "lang"],
    optional: ["description"],
    maxLengths: { title: 100, description: 200 },
  },
  activities: {
    required: ["title", "lang"],
    optional: ["description", "image", "emoji", "schedule", "order", "url_slug", "hidden"],
    maxLengths: { title: 100, description: 200 },
    defaults: { order: 100, hidden: false },
  },
  faq: {
    required: ["question", "answer", "lang"],
    optional: ["order", "hidden"],
    maxLengths: { question: 200 },
    defaults: { order: 100, hidden: false },
  },
  resources: {
    required: ["title", "category", "lang"],
    optional: ["description", "order", "url_slug", "hidden"],
    maxLengths: { title: 100, description: 200 },
    defaults: { order: 100, hidden: false },
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

  it("asks GitHub for a public-repo token only", () => {
    expect(config.backend.auth_scope).toBe("public_repo");
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

  it("has exactly 15 folder collections (5 types x 3 languages, programmatic ones excluded)", () => {
    expect(collections).toHaveLength(CONTENT_TYPES.length * LANGUAGES.length);
  });

  it("has only the site settings collection besides those", () => {
    const others = config.collections
      .filter((c: { folder?: string }) => c.folder === undefined)
      .map((c: { name: string }) => c.name);
    expect(others).toEqual(["settings"]);
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
  resources: (lang) => `${lang}/resources/{{slug}}`,
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

describe("Decap CMS config — optional description", () => {
  for (const type of CONTENT_TYPES) {
    if (!EXPECTED_FIELDS[type].optional.includes("description")) continue;
    for (const lang of LANGUAGES) {
      it(`${type}-${lang}: description is optional and has a Greek hint`, () => {
        const f = getField(getCollection(type, lang), "description");
        expect(f!.required).toBe(false);
        expect(f!.hint).toMatch(/Προαιρετικό/);
      });
    }
    it(`${type}: description hint is the same in all languages`, () => {
      const hints = LANGUAGES.map(
        (lang) => getField(getCollection(type, lang), "description")!.hint,
      );
      expect(hints[1]).toBe(hints[0]);
      expect(hints[2]).toBe(hints[0]);
    });
  }
});

describe("Decap CMS config — fields copied from the Greek entry", () => {
  // The translation step translates these fields and the body. It copies every
  // other field from the Greek entry on every run, so a change made to it on a
  // Dutch or English entry is lost.
  const translateScript = readFileSync(join(ROOT, ".github/scripts/translate.py"), "utf-8");
  const translated = new Set(
    [...translateScript.match(/^TRANSLATABLE_FIELDS = \{([^}]*)\}/m)![1].matchAll(/"([a-z_]+)"/g)].map(
      (m) => m[1],
    ),
  );
  translated.add("body");
  const COPIED_HINT =
    "Αλλάζει στην ελληνική καταχώρηση· εδώ αντιγράφεται αυτόματα. / Change this on the Greek entry; it is copied here automatically.";

  it("reads the translated fields from translate.py", () => {
    expect(translated).toContain("title");
    expect(translated).toContain("description");
  });

  for (const type of CONTENT_TYPES) {
    for (const lang of ["nl", "en"]) {
      for (const f of getCollection(type, lang).fields) {
        if (f.widget === "hidden" || translated.has(f.name)) continue;
        it(`${type}-${lang}.${f.name} says to change it on the Greek entry`, () => {
          expect(f.hint).toBe(COPIED_HINT);
        });
      }
    }
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
// (Folder collections only: the settings collection has fixed files and no
// `create`; see site-settings.test.ts.)
describe("Decap CMS config — only Greek collections allow creation", () => {
  for (const col of collections) {
    const isGreek = col.name.endsWith("-gr");
    it(`${col.name} has create: ${isGreek}`, () => {
      expect(col.create).toBe(isGreek);
    });
  }
});

// No entry can be deleted in /admin. Deleting a published entry commits
// straight to main and removes only that file (tested on #99), so its
// translations would stay live without a Greek source. Editors take an entry
// off the site with "Hide from site" (the `hidden` field) instead, which goes
// through a pull request like any save. Decap's default is `delete: true`.
describe("Decap CMS config — no collection allows deleting", () => {
  for (const col of collections) {
    it(`${col.name} has delete: false`, () => {
      expect(col.delete).toBe(false);
    });
  }
});

// No Publish button anywhere, settings included: setting a post to Ready is
// the only way to publish, and auto-publish then waits for the translations
// and the checks. The admin account may skip the ruleset, so its Publish could
// merge a post before its translations exist.
describe("Decap CMS config — no collection shows Publish", () => {
  for (const col of config.collections as { name: string; publish?: boolean }[]) {
    it(`${col.name} has publish: false`, () => {
      expect(col.publish).toBe(false);
    });
  }
});

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
    const external = tags.filter((t) => /\bsrc="https?:/.test(t));
    expect(external.length).toBeGreaterThan(0);
    for (const t of external) {
      expect(t).toMatch(/integrity="sha384-[A-Za-z0-9+/]+=*"/);
      expect(t).toMatch(/crossorigin="anonymous"/);
    }
  });

  it("loads every other script from this site", () => {
    const local = tags.filter((t) => !/\bsrc="https?:/.test(t));
    for (const t of local) {
      expect(t).toMatch(/\bsrc="\/admin\/[\w-]+\.js"/);
    }
  });

  it("loads the Workflow board badges as a module", () => {
    expect(tags).toContainEqual(
      '<script type="module" src="/admin/workflow-badges.js">',
    );
  });

  it("loads the editor guide link as a module", () => {
    expect(tags).toContainEqual('<script type="module" src="/admin/guide-link.js">');
  });

  it("loads the «In Review» hider as a module", () => {
    expect(tags).toContainEqual('<script type="module" src="/admin/hide-in-review.js">');
  });
});

// One interface language rule (#106): everything an editor reads in /admin
// is Greek first, then " / ", then English. Collection names are the
// exception: each names its own language (e.g. "Nieuws (Nederlands)").
describe("Decap CMS config — Greek / English labels and hints", () => {
  const GREEK_THEN_ENGLISH = /^[^/]*[Ͱ-Ͽἀ-῿].* \/ .*[A-Za-z]/s;

  interface Node {
    name?: string;
    label?: string;
    widget?: string;
    hint?: string;
    description?: string;
    pattern?: [string, string];
    options?: unknown[];
    fields?: Node[];
    files?: Node[];
  }

  // Every text an editor can see, with where it comes from.
  const texts: [string, string][] = [];
  const walk = (node: Node, where: string) => {
    for (const f of node.fields ?? []) {
      const at = `${where}.${f.name}`;
      if (f.widget === "hidden") continue;
      texts.push([`${at} label`, f.label ?? ""]);
      if (f.hint) texts.push([`${at} hint`, f.hint]);
      if (f.pattern) texts.push([`${at} pattern message`, f.pattern[1]]);
      for (const o of f.options ?? []) {
        if (typeof o === "object" && o && "label" in o) texts.push([`${at} option`, String(o.label)]);
      }
      walk(f, at);
    }
  };
  for (const col of config.collections as Node[]) {
    if (col.description) texts.push([`${col.name} description`, col.description]);
    for (const file of col.files ?? []) {
      texts.push([`${col.name}/${file.name} label`, file.label ?? ""]);
      walk(file, `${col.name}/${file.name}`);
    }
    walk(col, col.name ?? "");
  }

  it("finds the texts to check", () => {
    expect(texts.length).toBeGreaterThan(100);
  });

  for (const [where, text] of texts) {
    it(`${where} is Greek / English`, () => {
      expect(text).toMatch(GREEK_THEN_ENGLISH);
    });
  }

  it("resource categories show a readable name, and every value has a page heading", () => {
    const ui = readFileSync(join(ROOT, "src/i18n/ui.ts"), "utf-8");
    for (const lang of LANGUAGES) {
      const f = getField(getCollection("resources", lang), "category") as unknown as {
        options: { label: string; value: string }[];
      };
      expect(f.options.length).toBeGreaterThan(0);
      for (const o of f.options) {
        expect(o.label).toMatch(GREEK_THEN_ENGLISH);
        // One heading per language in ui.ts.
        expect(ui.match(new RegExp(`"resources\\.category\\.${o.value}":`, "g"))).toHaveLength(3);
      }
    }
  });
});

// Editors see these names in /admin (Collections, Workflow). They must match
// the site's own page names, e.g. «Δράσεις», not «Δραστηριότητες».
describe("Decap CMS config — Greek collection names match the site", () => {
  const PAGE_NAME: Record<(typeof CONTENT_TYPES)[number], UIKey> = {
    news: "nav.news",
    "event-translations": "nav.events",
    activities: "activities.title",
    faq: "faq.title",
    resources: "resources.title",
  };
  for (const type of CONTENT_TYPES) {
    it(`${type}-gr is labelled with the site's page name`, () => {
      expect(getCollection(type, "gr").label).toBe(`${t("gr", PAGE_NAME[type])} (Ελληνικά)`);
    });
  }
});
