// Short plain-text excerpts of Markdown, used where a page needs a description
// but the editor left the description field empty.

const ELLIPSIS = "…";

const NAMED_ENTITIES: Record<string, string> = {
  nbsp: " ",
  amp: "&",
  lt: "<",
  gt: ">",
  quot: '"',
  apos: "'",
};

/** Turn Markdown (and any HTML inside it) into one line of plain text. */
export function toPlainText(markdown: string): string {
  return (
    markdown
      // Fenced code blocks and HTML comments: drop completely.
      .replace(/```[\s\S]*?```|~~~[\s\S]*?~~~/g, " ")
      .replace(/<!--[\s\S]*?-->/g, " ")
      // Images carry no text of their own: drop them. Links keep their text.
      .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
      .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
      .replace(/<[^>]+>/g, " ")
      // Line starts: headings, quotes, list markers, rules.
      .replace(/^\s{0,3}#{1,6}\s+/gm, "")
      .replace(/^\s{0,3}>+\s?/gm, "")
      .replace(/^\s*([-*_]\s*){3,}$/gm, " ")
      .replace(/^\s*([-*+]|\d+[.)])\s+/gm, "")
      // Emphasis, strikethrough and inline code markers.
      .replace(/(\*\*|__|\*|~~|`)/g, "")
      // Entities.
      .replace(/&(#\d+|#x[0-9a-f]+|[a-z]+);/gi, (whole, name: string) => {
        if (name[0] === "#") {
          const code =
            name[1].toLowerCase() === "x"
              ? parseInt(name.slice(2), 16)
              : parseInt(name.slice(1), 10);
          return Number.isFinite(code) && code > 0 && code < 0x110000
            ? String.fromCodePoint(code)
            : " ";
        }
        return NAMED_ENTITIES[name.toLowerCase()] ?? whole;
      })
      .replace(/\s+/g, " ")
      .trim()
  );
}

/**
 * Plain-text excerpt of at most `limit` characters (the "…" counts).
 * Cuts at a word boundary, and adds "…" only when something was cut.
 */
export function excerpt(markdown: string | undefined, limit = 200): string {
  const text = toPlainText(markdown ?? "");
  if (text.length <= limit) return text;

  // Room for the "…", then back up to the last space so no word is cut in half.
  const room = Math.max(limit - ELLIPSIS.length, 0);
  let cut = text.slice(0, room);
  if (!/\s/.test(text[room] ?? "")) {
    const lastSpace = cut.search(/\s\S*$/);
    if (lastSpace > 0) cut = cut.slice(0, lastSpace);
  }
  cut = cut.replace(/[\s,;:.\-–—]+$/, "");
  return cut + ELLIPSIS;
}

/** The editor's description when there is one, otherwise an excerpt of the body. */
export function descriptionOrExcerpt(
  description: string | undefined,
  body: string | undefined,
  limit = 200,
): string {
  const own = description?.trim();
  return own ? own : excerpt(body, limit);
}
