// Links inside content texts lead to pages in the reader's own language.
//
// Editors write Greek texts, so their links point to Greek pages, e.g.
// [επικοινωνήστε μαζί μας](/gr/contact). The translation bot keeps links as
// they are, so the Dutch and English texts also say /gr/contact. This step
// runs while Astro turns a content file's Markdown into HTML (see
// astro.config.mjs). It rewrites the language at the start of every internal
// link to the language of the file's folder:
//
//   src/content/about-sections/nl/cultural-group.md
//     /gr/contact  →  /nl/contact
//
// Content files in all three languages share their file names and url_slug,
// so the same address with another language leads to the same page.
// External links (https://…), image paths (/images/…) and anchors (#…) are
// left alone. Only Markdown links are seen: the processor keeps raw HTML
// (<a href="/gr/…">) as plain text, so such a link keeps its language.

import type { HastPluginDefinition, PluginFactoryContext } from "satteri";
import { LANGUAGES, type Lang } from "../i18n/utils";

const LANG_CODES = Object.keys(LANGUAGES).join("|");

// "/gr", "/gr/…", "/gr?…" or "/gr#…" (but not "/grocery").
const LANG_PREFIX = new RegExp(`^/(${LANG_CODES})(?=/|\\?|#|$)`);

// The language folder in a content file's path:
// …/src/content/<collection>/<lang>/<file>.md
const CONTENT_FOLDER = new RegExp(`/src/content/[^/]+/(${LANG_CODES})/`);

/** The same internal address in `lang`. Other addresses come back unchanged. */
export function localizeHref(href: string, lang: Lang): string {
  return href.replace(LANG_PREFIX, `/${lang}`);
}

/** The language folder of a content file, or undefined for other files. */
export function contentFileLang(fileURL: URL | undefined): Lang | undefined {
  const match = fileURL?.pathname.match(CONTENT_FOLDER);
  return match ? (match[1] as Lang) : undefined;
}

/**
 * Sätteri plugin (Astro's Markdown processor) that rewrites internal links in
 * a content file to the file's language. Leaves files outside src/content/
 * untouched.
 */
export function localizeContentLinks(
  ctx: PluginFactoryContext,
): HastPluginDefinition | null {
  const lang = contentFileLang(ctx.fileURL);
  if (!lang) return null;
  return {
    name: "localize-content-links",
    element: {
      filter: ["a"],
      visit(node, visit) {
        const href = node.properties?.href;
        if (typeof href !== "string") return;
        const localized = localizeHref(href, lang);
        if (localized !== href) visit.setProperty(node, "href", localized);
      },
    },
  };
}
