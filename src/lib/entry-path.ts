// One place that decides the page address of a news or activity entry.
//
// An entry file lives at src/content/<type>/<lang>/<file-name>.md. Its entry
// id is "<lang>/<file-name>". By default the page is served at
// /<lang>/<type>/<file-name>. If the editor filled in the optional short
// address (`url_slug`), the page is served at /<lang>/<type>/<url_slug>
// instead, and the file-name address stays as a redirect page so old links
// keep working.

/** Same rule as the `url_slug` field in content.config.ts and config.yml. */
export const URL_SLUG_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;
export const URL_SLUG_MAX_LENGTH = 60;

/** The part of a content entry these helpers need. */
export interface PathEntry {
  id: string;
  filePath?: string;
  data: { url_slug?: string };
}

/** The language folder of an entry ("gr", "nl" or "en"). */
export function entryLang(entry: PathEntry): string {
  return entry.id.split("/")[0];
}

/** The file-name part of the entry id, e.g. "easter-2026". */
export function fileSlug(entry: PathEntry): string {
  return entry.id.split("/").slice(1).join("/");
}

/** The address part the page is served at: the short address if set. */
export function pageSlug(entry: PathEntry): string {
  return entry.data.url_slug || fileSlug(entry);
}

/** Link to the entry's page, e.g. "/gr/news/pascha-2026". */
export function entryPath(type: string, entry: PathEntry): string {
  return `/${entryLang(entry)}/${type}/${pageSlug(entry)}`;
}

function describe(entry: PathEntry): string {
  return entry.filePath ?? entry.id;
}

/**
 * Stop the build if two entries of one language would end up at the same
 * address. Every entry claims its short address (if set) and its file-name
 * address (as the page or as the redirect), and no address may be claimed by
 * two different entries.
 */
export function assertUniquePaths(type: string, entries: PathEntry[]): void {
  const claims = new Map<string, { entry: PathEntry; via: string }>();
  for (const entry of entries) {
    const lang = entryLang(entry);
    const slugs: [string, string][] = [[fileSlug(entry), "its file name"]];
    if (entry.data.url_slug) slugs.push([entry.data.url_slug, "its url_slug"]);
    for (const [slug, via] of slugs) {
      const path = `/${lang}/${type}/${slug}`;
      const other = claims.get(path);
      if (other && other.entry !== entry) {
        throw new Error(
          `Two ${type} entries would share the address ${path}:\n` +
            `  - ${describe(other.entry)} (through ${other.via})\n` +
            `  - ${describe(entry)} (through ${via})\n` +
            `Change the url_slug of one of them (or leave it empty).`,
        );
      }
      claims.set(path, { entry, via });
    }
  }
}

export interface EntryRoute<E extends PathEntry> {
  params: { lang: string; slug: string };
  props: { entry: E; redirectTo?: string };
}

/**
 * The static routes for one collection: the entry's page, plus a redirect
 * page at the file-name address when a short address is set.
 */
export function buildEntryRoutes<E extends PathEntry>(
  type: string,
  entries: E[],
): EntryRoute<E>[] {
  assertUniquePaths(type, entries);
  const routes: EntryRoute<E>[] = [];
  for (const entry of entries) {
    const lang = entryLang(entry);
    routes.push({ params: { lang, slug: pageSlug(entry) }, props: { entry } });
    if (pageSlug(entry) !== fileSlug(entry)) {
      routes.push({
        params: { lang, slug: fileSlug(entry) },
        props: { entry, redirectTo: entryPath(type, entry) },
      });
    }
  }
  return routes;
}
