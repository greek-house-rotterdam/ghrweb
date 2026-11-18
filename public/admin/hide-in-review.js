// Hides Decap's «In Review» status: the Workflow board's middle column and
// the «In review» choice in an entry's Status menu. Our editors only need
// «Draft» and «Ready»: «Ready» publishes the post by itself (auto-publish.yml),
// and «In Review» does nothing.
//
// Decap has no setting for its workflow statuses, so this script finds them
// on the page by their English text and hides them. It depends on how Decap
// draws them (checked in Decap 3.16.3, English interface):
// - Workflow board: a grid (Emotion label "WorkflowListContainer") with one
//   item per status, each holding an <h2> with the column's name: «Drafts»,
//   «In Review», «Ready».
// - Status menu: items with role="menuitem" whose text is «Draft»,
//   «In review», «Ready».
// A post that is already «In Review» (moved there before this script, or
// through GitHub) keeps its column, so it never disappears from the board.
// Moving it to «Draft» or «Ready» hides the column again.
// After upgrading Decap (see index.html), open the Workflow board and an
// entry's Status menu on the preview and check that «In Review» is gone.

export const COLUMN_NAME = "In Review";
export const MENU_ITEM = "In review";

const HIDDEN = "data-ghr-hidden";
const TWO_COLUMNS = "data-ghr-two-columns";
const BOARD = '[class*="WorkflowListContainer"]';
const CARD = 'a[href^="#/collections/"]';

// Data attributes, not classes: React rewrites an element's class when Decap
// restyles it (a card dragged over a column), but leaves these alone.
const STYLE = `
[${HIDDEN}] { display: none !important; }
[${TWO_COLUMNS}] { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
`;

function text(element) {
  return element.textContent.trim();
}

function mark(element, name, on) {
  if (on && !element.hasAttribute(name)) element.setAttribute(name, "");
  if (!on && element.hasAttribute(name)) element.removeAttribute(name);
}

// The «In Review» column of the Workflow board: the board's grid item that
// holds the column's name. Null when the board isn't on the page, or Decap
// drew it differently.
export function reviewColumn(doc = document) {
  for (const board of doc.querySelectorAll(BOARD)) {
    for (const item of board.children) {
      const heading = item.querySelector("h2");
      if (heading && text(heading) === COLUMN_NAME) return { board, item };
    }
  }
  return null;
}

// Hide what should be hidden on the current page, and return what it did:
// "hidden" (the column is hidden), "kept" (the column holds a post, so it
// stays) or "none" (no Workflow board). It runs after every change Decap
// makes to the page, so it changes nothing that is already right.
export function apply(doc = document) {
  for (const item of doc.querySelectorAll('[role="menuitem"]')) {
    if (text(item) === MENU_ITEM) mark(item, HIDDEN, true);
  }

  const found = reviewColumn(doc);
  if (!found) return "none";
  const hide = !found.item.querySelector(CARD);
  mark(found.item, HIDDEN, hide);
  mark(found.board, TWO_COLUMNS, hide);
  return hide ? "hidden" : "kept";
}

function start() {
  const style = document.createElement("style");
  style.textContent = STYLE;
  document.head.append(style);

  apply();
  let frame = 0;
  new MutationObserver(() => {
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      apply();
    });
  }).observe(document.body, { childList: true, subtree: true });
}

if (typeof document !== "undefined") start();
