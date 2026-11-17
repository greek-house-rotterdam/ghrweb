// A link to the editor guide (docs/editor-guide.md) in /admin's top bar, on
// every page.
//
// Decap has no setting for extra links in its top bar, so this script finds
// the bar on the page and adds the link. It depends on how Decap draws its
// pages (checked in Decap 3.16.3):
// - Contents, Workflow and Media: a <header> whose <nav> holds a list of
//   links. The guide becomes the list's last item, after «Media».
// - The entry editor has no <header>. Its top bar ends with a section that
//   holds the site's address and the account menu (Emotion label
//   "ToolbarSectionMeta"). The guide goes first in that section.
// - Anywhere else (the login page, while Decap loads, or after a Decap upgrade
//   changed its layout): a small button fixed in the bottom-right corner, so
//   the link never disappears silently.
// After upgrading Decap (see index.html), open Contents, Workflow and an entry
// on the preview and check that the link sits in the top bar, not the corner.

export const GUIDE_URL =
  "https://github.com/greek-house-rotterdam/ghrweb/blob/main/docs/editor-guide.md";
export const LABEL = "Οδηγός / Guide";
export const TITLE =
  "Ο οδηγός για τους συντάκτες, σε νέα καρτέλα / The editor guide, in a new tab";

const LINK = "a[data-ghr-guide]";
const ITEM = "li[data-ghr-guide-item]";
const NAV_LIST = "header nav > ul";
const EDITOR_META = '[class*="ToolbarSectionMeta"]';
// Decap marks the link of the page you are on with this class.
const ACTIVE = "header-link-active";

// An open book, drawn for this link (Decap's own icons are filled shapes).
const ICON =
  '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">' +
  '<path d="M3 5.5A1.5 1.5 0 0 1 4.5 4H11v16H4.5A1.5 1.5 0 0 1 3 18.5v-13Zm10-1.5h6.5A1.5 1.5 0 0 1 21 5.5v13a1.5 1.5 0 0 1-1.5 1.5H13V4Z"/>' +
  "</svg>";

// Room for the guide: Decap already cuts the site's address with "…" when
// it's short of space, but never lets it get shorter. Let it, in the top bar
// and in the entry editor's bar, so Decap's own buttons keep their room.
const STYLE = `
.ghr-guide-nav { white-space: nowrap; }
[class*="AppHeaderActions"], [class*="ToolbarSectionMeta"], [class*="AppHeaderSiteLink"] { min-width: 0; }
.ghr-guide-icon { display: inline-block; line-height: 0; width: 18px; height: 18px; }
.ghr-guide-icon svg { width: 100%; height: 100%; }
.ghr-guide-toolbar { display: inline-flex; align-items: center; gap: 4px; padding: 10px 12px;
  font-size: 14px; color: #798291; text-decoration: none; white-space: nowrap; }
.ghr-guide-toolbar:hover, .ghr-guide-toolbar:focus-visible { color: #3a69c7; }
.ghr-guide-corner { position: fixed; right: 16px; bottom: 16px; z-index: 10000;
  display: inline-flex; align-items: center; gap: 6px; padding: 8px 12px;
  font: 500 14px/1.2 system-ui, sans-serif; color: #313d3e; background: #fff;
  border: 1px solid #dfdfe3; border-radius: 5px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  text-decoration: none; }
.ghr-guide-corner:hover, .ghr-guide-corner:focus-visible { color: #3a69c7; }
.ghr-guide-toolbar:focus-visible, .ghr-guide-corner:focus-visible {
  outline: 2px solid #3a69c7; outline-offset: 2px; }
`;

function makeLink(doc) {
  const link = doc.createElement("a");
  link.setAttribute("data-ghr-guide", "");
  link.href = GUIDE_URL;
  link.target = "_blank";
  link.rel = "noopener";
  link.title = TITLE;
  const icon = doc.createElement("span");
  icon.innerHTML = ICON;
  link.append(icon, doc.createTextNode(LABEL));
  return link;
}

function setClass(element, name) {
  if (element && element.className !== name) element.className = name;
}

// Put the guide link where it belongs on the current page and return where:
// "nav", "editor" or "corner". It runs after every change Decap makes to the
// page, so it does nothing when the link is already in place; otherwise its
// own change would make it run again, without end. There is only ever one
// link: it moves between places, and a new one is made only when Decap
// removed the old one with its bar.
export function ensure(doc = document) {
  const link = doc.querySelector(LINK) || makeLink(doc);
  const icon = link.firstElementChild;
  const parent = link.parentElement;
  const oldItem = parent && parent.matches(ITEM) ? parent : null;

  const list = doc.querySelector(NAV_LIST);
  if (list) {
    // The same look as Decap's own links («Contents», «Media»), never shown
    // as the page you are on.
    const template = list.querySelector("a:not([data-ghr-guide])");
    const look = template
      ? template.className.split(/\s+/).filter((c) => c && c !== ACTIVE)
      : [];
    setClass(link, [...look, "ghr-guide-nav"].join(" "));
    const templateIcon = template && template.querySelector("span");
    setClass(icon, templateIcon ? templateIcon.className : "ghr-guide-icon");
    const item = oldItem || doc.createElement("li");
    item.setAttribute("data-ghr-guide-item", "");
    if (link.parentElement !== item) item.append(link);
    // Last, after «Media»: Decap adds «Workflow» only once it knows the
    // publishing mode, which can put it after the guide.
    if (list.lastElementChild !== item) list.append(item);
    return "nav";
  }

  const meta = doc.querySelector(EDITOR_META);
  if (meta) {
    setClass(link, "ghr-guide-toolbar");
    setClass(icon, "ghr-guide-icon");
    if (meta.firstElementChild !== link) meta.prepend(link);
    if (oldItem) oldItem.remove();
    return "editor";
  }

  setClass(link, "ghr-guide-corner");
  setClass(icon, "ghr-guide-icon");
  if (link.parentElement !== doc.body) doc.body.append(link);
  if (oldItem) oldItem.remove();
  return "corner";
}

function start() {
  const style = document.createElement("style");
  style.textContent = STYLE;
  document.head.append(style);

  ensure();
  let frame = 0;
  new MutationObserver(() => {
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      ensure();
    });
  }).observe(document.body, { childList: true, subtree: true });
}

if (typeof document !== "undefined") start();
