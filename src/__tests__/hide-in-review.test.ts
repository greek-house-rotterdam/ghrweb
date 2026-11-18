// @vitest-environment happy-dom
import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";
import { parse } from "yaml";
import { COLUMN_NAME, MENU_ITEM, apply, reviewColumn } from "../../public/admin/hide-in-review.js";

// public/admin/hide-in-review.js hides Decap's «In Review» status. The pages
// below are simplified copies of what Decap 3.16.3 draws: only the structure,
// the class names and the texts the script reads are real.

const ROOT = join(__dirname, "../..");
const HIDDEN = "data-ghr-hidden";
const TWO_COLUMNS = "data-ghr-two-columns";

function card(slug: string): string {
  return `<div><div class="css-1yz6lr0-WorkflowCardContainer">
    <a class="css-x-WorkflowLink" href="#/collections/news-gr/entries/${slug}?ref=workflow">${slug}</a>
  </div></div>`;
}

// One grid item per status, as WorkflowList.js draws them.
function column(name: string, slugs: string[] = []): string {
  return `<div style="height: 100%;"><div class="css-1q9yxlz">
    <h2 class="css-9ynd1a-ColumnHeader e1yhfjtd1">${name}</h2>
    <p class="css-1ckbsp3-ColumnCount e1yhfjtd0">${slugs.length} entries</p>
    <div>${slugs.map(card).join("")}</div>
  </div></div>`;
}

function board(review: string[] = []): string {
  return `<div class="css-1tkl9bl-WorkflowListContainer e1yhfjtd3">
    ${column("Drafts", ["draft-post"])}${column("In Review", review)}${column("Ready", ["ready-post"])}
  </div>`;
}

// The open Status menu of an entry (react-aria-menubutton items).
const STATUS_MENU = `<div class="css-z-ToolbarDropdown"><div><button>Status: Draft</button></div>
  <div role="menu"><ul class="css-y-DropdownList">
    <div role="menuitem" class="css-m"><span>Draft</span><div class="css-i"><svg></svg></div></div>
    <div role="menuitem" class="css-m"><span>In review</span></div>
    <div role="menuitem" class="css-m"><span>Ready</span></div>
  </ul></div></div>`;

// A page in its own document, so each test starts clean.
function page(html: string): Document {
  const doc = document.implementation.createHTMLDocument("GHR Admin");
  doc.body.innerHTML = `<div id="nc-root">${html}</div>`;
  return doc;
}

const headings = (doc: Document) =>
  [...doc.querySelectorAll("h2")].map((h) => ({
    name: h.textContent!.trim(),
    hidden: h.closest(`[${HIDDEN}]`) !== null,
  }));

describe("hide «In Review» — Workflow board", () => {
  it("hides the empty «In Review» column and keeps «Drafts» and «Ready»", () => {
    const doc = page(board());
    expect(apply(doc)).toBe("hidden");
    expect(headings(doc)).toEqual([
      { name: "Drafts", hidden: false },
      { name: "In Review", hidden: true },
      { name: "Ready", hidden: false },
    ]);
  });

  it("hides the whole grid item, not only its heading", () => {
    const doc = page(board());
    apply(doc);
    const { board: grid, item } = reviewColumn(doc)!;
    expect(item.parentElement).toBe(grid);
    expect(item.hasAttribute(HIDDEN)).toBe(true);
  });

  it("lays the board out in two columns while «In Review» is hidden", () => {
    const doc = page(board());
    apply(doc);
    expect(reviewColumn(doc)!.board.hasAttribute(TWO_COLUMNS)).toBe(true);
  });

  it("keeps the column while a post is in it, so the post never disappears", () => {
    const doc = page(board(["waiting-post"]));
    expect(apply(doc)).toBe("kept");
    const { board: grid, item } = reviewColumn(doc)!;
    expect(item.hasAttribute(HIDDEN)).toBe(false);
    expect(grid.hasAttribute(TWO_COLUMNS)).toBe(false);
  });

  it("hides the column again once its last post moves out", () => {
    const doc = page(board(["waiting-post"]));
    apply(doc);
    reviewColumn(doc)!.item.querySelector("a")!.closest("div > div")!.remove();
    expect(apply(doc)).toBe("hidden");
    expect(reviewColumn(doc)!.item.hasAttribute(HIDDEN)).toBe(true);
  });

  it("stays hidden when Decap rewrites the column's classes", () => {
    const doc = page(board());
    apply(doc);
    const { item } = reviewColumn(doc)!;
    item.className = "css-other";
    (item.firstElementChild as HTMLElement).className = "css-1q9yxlz css-hovered";
    expect(item.hasAttribute(HIDDEN)).toBe(true);
  });

  it("changes nothing on a second run", () => {
    const doc = page(board() + STATUS_MENU);
    apply(doc);
    const observer = new MutationObserver(() => {});
    observer.observe(doc.body, { attributes: true, childList: true, subtree: true });
    apply(doc);
    expect(observer.takeRecords()).toEqual([]);
    observer.disconnect();
  });

  it("does nothing on pages without the board", () => {
    const doc = page('<header><nav><ul><li><a href="#/">Contents</a></li></ul></nav></header>');
    expect(apply(doc)).toBe("none");
    expect(doc.querySelector(`[${HIDDEN}]`)).toBeNull();
  });

  it("leaves a board it doesn't recognise alone", () => {
    // After a Decap upgrade that renames the grid: nothing is hidden, so the
    // board still works, with three columns.
    const doc = page(board().replace("WorkflowListContainer", "SomethingElse"));
    expect(apply(doc)).toBe("none");
    expect(doc.querySelector(`[${HIDDEN}]`)).toBeNull();
  });
});

describe("hide «In Review» — Status menu", () => {
  it("hides «In review» and keeps «Draft» and «Ready»", () => {
    const doc = page(STATUS_MENU);
    apply(doc);
    const items = [...doc.querySelectorAll('[role="menuitem"]')].map((i) => ({
      name: i.textContent!.trim(),
      hidden: i.hasAttribute(HIDDEN),
    }));
    expect(items).toEqual([
      { name: "Draft", hidden: false },
      { name: "In review", hidden: true },
      { name: "Ready", hidden: false },
    ]);
  });
});

describe("hide «In Review» — Decap's labels", () => {
  it("matches Decap's English labels for the status", () => {
    expect(COLUMN_NAME).toBe("In Review");
    expect(MENU_ITEM).toBe("In review");
  });

  it("runs on an English /admin (the labels change with Decap's locale)", () => {
    const config = parse(readFileSync(join(ROOT, "public/admin/config.yml"), "utf-8"));
    expect(config.locale ?? "en").toBe("en");
  });

  it("adds the styles that hide what it marks", () => {
    // Importing the script started it on this test file's own page.
    const css = [...document.querySelectorAll("style")].map((s) => s.textContent).join("\n");
    expect(css).toContain(`[${HIDDEN}] { display: none !important; }`);
    expect(css).toContain(`[${TWO_COLUMNS}] { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }`);
  });
});
