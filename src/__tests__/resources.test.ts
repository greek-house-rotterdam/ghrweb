import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "fs";
import { join } from "path";
import { categoryLabel } from "../lib/resource-category";
import { entryPath } from "../lib/entry-path";

// «Χρήσιμες Πληροφορίες» (the resources collection). The list page shows only
// the start of each text, so every entry has its own page with the whole text.

const ROOT = join(__dirname, "../..");
const LIST_PAGE = join(ROOT, "src/pages/[lang]/resources.astro");
const ENTRY_PAGE = join(ROOT, "src/pages/[lang]/resources/[slug].astro");

describe("resources: one page per entry", () => {
  it("has an entry page", () => {
    expect(existsSync(ENTRY_PAGE)).toBe(true);
  });

  it("builds the entry pages from the visible entries only", () => {
    const src = readFileSync(ENTRY_PAGE, "utf-8");
    expect(src).toMatch(/buildEntryRoutes\(\s*"resources",\s*await getVisible\("resources"\)\s*\)/);
  });

  it("links each card on the list page to the entry's page", () => {
    const src = readFileSync(LIST_PAGE, "utf-8");
    expect(src).toMatch(/<BrutCard\s+href=\{entryPath\("resources",/);
  });

  it("serves the entry at its file name when there is no short address", () => {
    const paths = ["gr", "nl", "en"].map((lang) =>
      entryPath("resources", { id: `${lang}/greek-consulate`, data: {} }),
    );
    expect(paths).toEqual([
      "/gr/resources/greek-consulate",
      "/nl/resources/greek-consulate",
      "/en/resources/greek-consulate",
    ]);
  });

  it("serves the entry at its short address when one is set", () => {
    const entry = { id: "gr/πότε-πώς-και-γιατί", data: { url_slug: "proxeneio" } };
    expect(entryPath("resources", entry)).toBe("/gr/resources/proxeneio");
  });
});

describe("resources: category labels", () => {
  it("names a known category in the page's language", () => {
    expect(categoryLabel("gr", "legal")).toBe("Νομικά");
    expect(categoryLabel("nl", "legal")).toBe("Juridisch");
    expect(categoryLabel("en", "legal")).toBe("Legal");
  });

  it("shows an unknown category as it is", () => {
    expect(categoryLabel("en", "something-new")).toBe("something-new");
  });
});
