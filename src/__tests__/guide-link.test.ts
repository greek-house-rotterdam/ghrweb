// @vitest-environment happy-dom
import { describe, it, expect, vi } from "vitest";
import { existsSync } from "fs";
import { join } from "path";
import { GUIDE_URL, LABEL, TITLE, ensure } from "../../public/admin/guide-link.js";

// public/admin/guide-link.js adds «Οδηγός / Guide» to /admin's top bar. The
// pages below are simplified copies of what Decap 3.16.3 draws: only the
// structure and the class names the script reads are real.

const ROOT = join(__dirname, "../..");
const LINK = "a[data-ghr-guide]";

const icon = '<span class="e1jeq5dr0 css-5nxuzj-IconWrapper e1jeq5dr1"><svg></svg></span>';
const navLink = "css-nofkcj-AppHeaderNavLink-AppHeaderButton e1rbzf6g6";

// The top bar of Contents, Workflow and Media. Decap adds «Workflow» only once
// it knows the publishing mode.
function header(workflow = true): string {
  return `<header class="css-mxshdh-AppHeader-css"><div class="css-j8x405-AppHeaderContent">
    <nav><ul class="css-gozwmv-AppHeaderNavList e1rbzf6g1">
      <li><a class="${navLink} header-link-active" href="#/" aria-current="page">${icon}Contents</a></li>
      ${workflow ? `<li><a class="${navLink}" href="#/workflow">${icon}Workflow</a></li>` : ""}
      <li><button class="css-uphj2n-AppHeaderButton e1rbzf6g4">${icon}Media</button></li>
    </ul></nav>
    <div class="css-xsq64v-AppHeaderActions"><a href="https://example.org" target="_blank">site</a></div>
  </div></header>`;
}

// The entry editor has no <header>; its top bar ends with the site's address
// and the account menu.
const EDITOR = `<div class="css-1gtfcgu-ToolbarContainer e1d2l9mo22">
  <a class="css-v5veov-ToolbarSectionBackLink" href="#/collections/news-gr">←</a>
  <div class="css-1gn4qo4-ToolbarSectionMain"><button>Publish</button></div>
  <div class="css-1uf4969-ToolbarSectionMeta-toolbarSection-toolbarSection e1d2l9mo17">
    <div class="css-1dcu06v-SettingsWrapper"><a href="https://example.org" target="_blank">site</a></div>
  </div>
</div>`;

const LOGIN = '<section><button>Login with GitHub</button></section>';

// A page in its own document, so each test starts clean.
function page(html: string): Document {
  const doc = document.implementation.createHTMLDocument("GHR Admin");
  doc.body.innerHTML = `<div id="nc-root">${html}</div>`;
  return doc;
}

function fragment(doc: Document, html: string): Element {
  const box = doc.createElement("div");
  box.innerHTML = html.trim();
  return box.firstElementChild!;
}

const links = (doc: Document) => [...doc.querySelectorAll(LINK)];

describe("guide link — the link itself", () => {
  // The /admin text rule, as in admin.test.ts: Greek, then " / ", then English.
  const GREEK_THEN_ENGLISH = /^[^/]*[Ͱ-Ͽἀ-῿].* \/ .*[A-Za-z]/s;

  it("is labelled Greek, then English", () => {
    expect(LABEL).toBe("Οδηγός / Guide");
    expect(LABEL).toMatch(GREEK_THEN_ENGLISH);
    expect(TITLE).toMatch(GREEK_THEN_ENGLISH);
  });

  it("opens the editor guide on GitHub in a new tab", () => {
    expect(GUIDE_URL).toBe(
      "https://github.com/greek-house-rotterdam/ghrweb/blob/main/docs/editor-guide.md",
    );
    expect(existsSync(join(ROOT, "docs/editor-guide.md"))).toBe(true);
    const doc = page(header());
    ensure(doc);
    const [link] = links(doc);
    expect(link.getAttribute("href")).toBe(GUIDE_URL);
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toBe("noopener");
  });

  it("is a real link whose name is its visible text", () => {
    const doc = page(header());
    ensure(doc);
    const [link] = links(doc);
    expect(link.tagName).toBe("A");
    expect(link.hasAttribute("tabindex")).toBe(false);
    expect(link.hasAttribute("aria-label")).toBe(false);
    expect(link.textContent).toBe(LABEL);
    expect(link.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });
});

describe("guide link — Contents, Workflow and Media", () => {
  it("adds the link once, as the last item, after «Media»", () => {
    const doc = page(header());
    expect(ensure(doc)).toBe("nav");
    const list = doc.querySelector("header nav > ul")!;
    const [link] = links(doc);
    expect(list.lastElementChild).toBe(link.parentElement);
    expect(list.children).toHaveLength(4);

    expect(ensure(doc)).toBe("nav");
    expect(links(doc)).toEqual([link]);
    expect(list.children).toHaveLength(4);
  });

  it("looks like Decap's own links, never like the page you are on", () => {
    const doc = page(header());
    ensure(doc);
    const [link] = links(doc);
    expect(link.className).toContain("css-nofkcj-AppHeaderNavLink");
    expect(link.className).not.toContain("header-link-active");
    expect(link.hasAttribute("aria-current")).toBe(false);
    expect(link.firstElementChild!.className).toBe("e1jeq5dr0 css-5nxuzj-IconWrapper e1jeq5dr1");
  });

  it("stays last when Decap adds «Workflow» after it", () => {
    const doc = page(header(false));
    ensure(doc);
    const list = doc.querySelector("header nav > ul")!;
    const workflow = fragment(doc, `<li><a class="${navLink}" href="#/workflow">Workflow</a></li>`);
    list.append(workflow);
    expect(list.lastElementChild).toBe(workflow);

    ensure(doc);
    expect(links(doc)).toHaveLength(1);
    expect(list.lastElementChild).toBe(links(doc)[0].parentElement);
  });

  it("comes back once when Decap draws the header again", () => {
    const doc = page(header());
    ensure(doc);
    const fresh = fragment(doc, header());
    doc.querySelector("header")!.replaceWith(fresh);
    expect(links(doc)).toHaveLength(0);

    expect(ensure(doc)).toBe("nav");
    expect(links(doc)).toHaveLength(1);
    expect(fresh.contains(links(doc)[0])).toBe(true);
  });
});

describe("guide link — the entry editor", () => {
  it("goes first in the top bar's last section, before the site's address", () => {
    const doc = page(EDITOR);
    expect(ensure(doc)).toBe("editor");
    const meta = doc.querySelector('[class*="ToolbarSectionMeta"]')!;
    const [link] = links(doc);
    expect(meta.firstElementChild).toBe(link);
    expect(link.className).toBe("ghr-guide-toolbar");

    expect(ensure(doc)).toBe("editor");
    expect(links(doc)).toEqual([link]);
  });

  it("keeps one link when moving between a list page and the editor", () => {
    const doc = page(header());
    ensure(doc);
    const root = doc.getElementById("nc-root")!;
    root.innerHTML = EDITOR;
    expect(ensure(doc)).toBe("editor");
    expect(links(doc)).toHaveLength(1);
    expect(doc.querySelector("li[data-ghr-guide-item]")).toBeNull();

    root.innerHTML = header();
    expect(ensure(doc)).toBe("nav");
    expect(links(doc)).toHaveLength(1);
    expect(doc.querySelectorAll("li[data-ghr-guide-item]")).toHaveLength(1);
  });
});

describe("guide link — no top bar", () => {
  it("shows a button in the corner on the login page", () => {
    const doc = page(LOGIN);
    expect(ensure(doc)).toBe("corner");
    const [link] = links(doc);
    expect(link.parentElement).toBe(doc.body);
    expect(link.className).toBe("ghr-guide-corner");
  });

  it("shows a button in the corner when Decap's layout changed", () => {
    const doc = page('<div class="SomeNewTopBar"><a href="#/">Contents</a></div>');
    expect(ensure(doc)).toBe("corner");
    expect(links(doc)).toHaveLength(1);
  });

  it("moves the corner button into the top bar once Decap draws it", () => {
    const doc = page(LOGIN);
    ensure(doc);
    const [corner] = links(doc);
    doc.getElementById("nc-root")!.innerHTML = header();

    expect(ensure(doc)).toBe("nav");
    expect(links(doc)).toEqual([corner]);
    expect(doc.querySelector(".ghr-guide-corner")).toBeNull();
  });

  it("moves back to the corner when the top bar goes away", () => {
    const doc = page(header());
    ensure(doc);
    const [link] = links(doc);
    // The bar is gone, but the link's list item was left on the page.
    doc.querySelector("header")!.remove();
    doc.body.append(link.parentElement!);

    expect(ensure(doc)).toBe("corner");
    expect(links(doc)).toEqual([link]);
    expect(doc.querySelector("li[data-ghr-guide-item]")).toBeNull();
  });
});

describe("guide link — on the real page", () => {
  // Importing the script started it on this test file's document: it watches
  // the page and puts the link back after every change Decap makes.
  it("puts the link in the top bar and keeps it there when Decap re-renders", async () => {
    document.body.innerHTML = `<div id="nc-root">${LOGIN}</div>`;
    await vi.waitFor(() => expect(document.querySelector(`body > ${LINK}`)).not.toBeNull());

    document.getElementById("nc-root")!.innerHTML = header(false);
    await vi.waitFor(() => expect(document.querySelector(`header ${LINK}`)).not.toBeNull());

    // A re-render: Decap draws a new header, now with «Workflow».
    document.querySelector("header")!.replaceWith(fragment(document, header()));
    await vi.waitFor(() => {
      const list = document.querySelector("header nav > ul")!;
      expect(list.lastElementChild?.querySelector(LINK)).not.toBeNull();
    });
    expect(document.querySelectorAll(LINK)).toHaveLength(1);
  });
});
