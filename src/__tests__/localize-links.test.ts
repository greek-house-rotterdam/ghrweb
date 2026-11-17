import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import config from "../../astro.config.mjs";
import { contentFileLang, localizeHref } from "../lib/localize-links";

// Renders Markdown the way the site does: through the Markdown processor set
// in astro.config.mjs, as if the text were the content file at `path`.
async function render(markdown: string, path: string): Promise<string> {
  const renderer = await config.markdown!.processor!.createRenderer({
    syntaxHighlight: false,
  });
  const { code } = await renderer.render(markdown, {
    frontmatter: {},
    fileURL: new URL(`file:///site/${path}`),
  });
  return code;
}

const TEXT = [
  "[Contact](/gr/contact) and [home](/gr).",
  "",
  "![A photo](/images/team.jpg)",
  "",
  "[Elsewhere](https://example.org/gr/contact), [section](#more), [mail](mailto:info@example.org).",
].join("\n");

describe("links in content texts lead to the reader's language", () => {
  it("a Dutch text links to Dutch pages", async () => {
    const html = await render(TEXT, "src/content/about-sections/nl/a.md");
    expect(html).toContain('href="/nl/contact"');
    expect(html).toContain('href="/nl"');
    expect(html).not.toContain('href="/gr');
  });

  it("an English text links to English pages", async () => {
    const html = await render(TEXT, "src/content/news/en/a.md");
    expect(html).toContain('href="/en/contact"');
  });

  it("a Greek text keeps its links", async () => {
    const html = await render(TEXT, "src/content/activities/gr/a.md");
    expect(html).toContain('href="/gr/contact"');
  });

  it("leaves images, external links, anchors and email links alone", async () => {
    const html = await render(TEXT, "src/content/about-sections/nl/a.md");
    expect(html).toContain('src="/images/team.jpg"');
    expect(html).toContain('href="https://example.org/gr/contact"');
    expect(html).toContain('href="#more"');
    expect(html).toContain('href="mailto:info@example.org"');
  });

  it("leaves Markdown outside src/content/ alone", async () => {
    const html = await render(TEXT, "src/pages/a.md");
    expect(html).toContain('href="/gr/contact"');
  });
});

describe("localizeHref", () => {
  it("swaps the language at the start of an internal address", () => {
    expect(localizeHref("/gr/contact", "nl")).toBe("/nl/contact");
    expect(localizeHref("/en/news/pascha-2026", "gr")).toBe("/gr/news/pascha-2026");
    expect(localizeHref("/gr", "en")).toBe("/en");
    expect(localizeHref("/gr?x=1", "en")).toBe("/en?x=1");
    expect(localizeHref("/gr#top", "en")).toBe("/en#top");
  });

  it("leaves other addresses alone", () => {
    expect(localizeHref("/grocery", "nl")).toBe("/grocery");
    expect(localizeHref("/images/gr/a.jpg", "nl")).toBe("/images/gr/a.jpg");
    expect(localizeHref("https://example.org/gr/x", "nl")).toBe("https://example.org/gr/x");
    expect(localizeHref("contact", "nl")).toBe("contact");
  });
});

describe("the Markdown processor package", () => {
  // astro.config.mjs builds the processor from our own copy of
  // @astrojs/markdown-satteri. It must be the version Astro itself uses, or
  // two copies get installed and drift apart. Upgrade both together.
  it("is pinned to the version Astro depends on", () => {
    const read = (path: string) => JSON.parse(readFileSync(path, "utf8"));
    const ours = read("package.json").dependencies["@astrojs/markdown-satteri"];
    const astros = read("node_modules/astro/package.json").dependencies["@astrojs/markdown-satteri"];
    expect(ours).toBe(astros);
  });
});

describe("contentFileLang", () => {
  it("reads the language folder of a content file", () => {
    expect(contentFileLang(new URL("file:///x/src/content/faq/nl/a.md"))).toBe("nl");
    expect(contentFileLang(new URL("file:///x/src/content/faq/de/a.md"))).toBeUndefined();
    expect(contentFileLang(new URL("file:///x/src/pages/nl/a.md"))).toBeUndefined();
    expect(contentFileLang(undefined)).toBeUndefined();
  });
});
