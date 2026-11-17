/**
 * Documents (PDFs) the site serves from `public/documents/`. Only the
 * developer adds them: `/admin` can't. Not in `public/images/`, because the
 * content pipeline treats that folder as images only. Cloudflare Workers
 * serves files of at most 25 MiB. `documents.test.ts` checks every file here.
 */
export const DOCUMENTS = {
  /**
   * «Χρονικό της Ενώσεως Ελλήνων Ολλανδίας 1946–1996» by Theodoros I.
   * Theodoridis: a scanned book, in Greek. It was only on vvgn.eu, which
   * closes when this site moves to that address (#114).
   */
  chronicle: "/documents/chroniko-eeo-1946-1996.pdf",
} as const;
