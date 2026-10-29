import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";
import { parse as parseYaml } from "yaml";
import {
  URL_SLUG_MAX_LENGTH,
  URL_SLUG_PATTERN,
  assertUniquePaths,
  buildEntryRoutes,
  entryPath,
  pageSlug,
  type PathEntry,
} from "../lib/entry-path";

function entry(id: string, url_slug?: string): PathEntry {
  return {
    id,
    filePath: `src/content/news/${id}.md`,
    data: url_slug === undefined ? {} : { url_slug },
  };
}

describe("entryPath", () => {
  it("uses the file name when there is no short address", () => {
    expect(entryPath("news", entry("gr/easter-2026"))).toBe("/gr/news/easter-2026");
  });

  it("uses the short address when it is set", () => {
    const e = entry("gr/ενα-πολυ-μακρο-ονομα", "pascha-2026");
    expect(entryPath("news", e)).toBe("/gr/news/pascha-2026");
    expect(pageSlug(e)).toBe("pascha-2026");
  });

  it("treats an empty short address as not set", () => {
    expect(entryPath("activities", entry("nl/dans", ""))).toBe("/nl/activities/dans");
  });

  it("keeps the same short address in every language", () => {
    const paths = ["gr", "nl", "en"].map((l) => entryPath("news", entry(`${l}/lang-naam`, "pascha-2026")));
    expect(paths.map((p) => p.split("/").slice(2).join("/"))).toEqual([
      "news/pascha-2026",
      "news/pascha-2026",
      "news/pascha-2026",
    ]);
  });
});

describe("url_slug format", () => {
  it.each(["pascha-2026", "a", "a1-b2-c3", "2026"])("accepts %s", (v) => {
    expect(URL_SLUG_PATTERN.test(v)).toBe(true);
  });

  it.each(["Pascha", "pascha_2026", "-pascha", "pascha-", "pa--scha", "πάσχα", "pa scha", ""])(
    "rejects %j",
    (v) => {
      expect(URL_SLUG_PATTERN.test(v)).toBe(false);
    },
  );

  it("allows up to 60 characters", () => {
    expect(URL_SLUG_MAX_LENGTH).toBe(60);
  });
});

describe("assertUniquePaths", () => {
  it("accepts entries that do not clash", () => {
    expect(() =>
      assertUniquePaths("news", [entry("gr/a", "x"), entry("gr/b", "y"), entry("nl/c", "x")]),
    ).not.toThrow();
  });

  it("accepts a short address equal to the entry's own file name", () => {
    expect(() => assertUniquePaths("news", [entry("gr/pascha", "pascha")])).not.toThrow();
  });

  it("fails when two entries use the same short address, naming both files", () => {
    expect(() => assertUniquePaths("news", [entry("gr/a", "x"), entry("gr/b", "x")])).toThrow(
      /\/gr\/news\/x[\s\S]*src\/content\/news\/gr\/a\.md[\s\S]*src\/content\/news\/gr\/b\.md/,
    );
  });

  it("fails when a short address matches another entry's file name", () => {
    expect(() => assertUniquePaths("news", [entry("gr/a", "b"), entry("gr/b")])).toThrow(
      /\/gr\/news\/b/,
    );
  });
});

describe("buildEntryRoutes", () => {
  it("gives one page per entry when no short address is set", () => {
    const routes = buildEntryRoutes("news", [entry("gr/a")]);
    expect(routes).toHaveLength(1);
    expect(routes[0].params).toEqual({ lang: "gr", slug: "a" });
    expect(routes[0].props.redirectTo).toBeUndefined();
  });

  it("serves the page at the short address and redirects the file-name address", () => {
    const routes = buildEntryRoutes("news", [entry("gr/long-name", "short")]);
    expect(routes).toHaveLength(2);
    const page = routes.find((r) => r.params.slug === "short")!;
    const old = routes.find((r) => r.params.slug === "long-name")!;
    expect(page.props.redirectTo).toBeUndefined();
    expect(old.props.redirectTo).toBe("/gr/news/short");
  });

  it("makes no redirect when the short address equals the file name", () => {
    expect(buildEntryRoutes("news", [entry("gr/same", "same")])).toHaveLength(1);
  });

  it("fails on a clash", () => {
    expect(() => buildEntryRoutes("news", [entry("gr/a", "x"), entry("gr/b", "x")])).toThrow();
  });
});

describe("url_slug in the CMS config", () => {
  const config = parseYaml(readFileSync(join(__dirname, "../../public/admin/config.yml"), "utf-8"));

  for (const type of ["news", "activities"]) {
    for (const lang of ["gr", "nl", "en"]) {
      it(`${type}-${lang} has an optional url_slug with the same format rule as the site`, () => {
        const col = config.collections.find((c: { name: string }) => c.name === `${type}-${lang}`);
        const f = col.fields.find((x: { name: string }) => x.name === "url_slug");
        expect(f).toBeDefined();
        expect(f.required).toBe(false);
        expect(f.pattern[0]).toBe(URL_SLUG_PATTERN.source);
      });
    }
  }

  it("has no url_slug where entries have no page of their own", () => {
    for (const c of config.collections as { name: string; fields: { name: string }[] }[]) {
      if (/^(faq|resources|event-translations)-/.test(c.name)) {
        expect(c.fields.map((f) => f.name)).not.toContain("url_slug");
      }
    }
  });
});
