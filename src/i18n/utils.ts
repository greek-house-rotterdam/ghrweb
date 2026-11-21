export const LANGUAGES = {
  gr: "Ελληνικά",
  nl: "Nederlands",
  en: "English",
} as const;

export type Lang = keyof typeof LANGUAGES;

export const DEFAULT_LANG: Lang = "gr";

export function getLangFromSlug(slug: string): Lang {
  const lang = slug.split("/")[0];
  if (lang in LANGUAGES) return lang as Lang;
  return DEFAULT_LANG;
}

export function getStaticLangPaths() {
  return Object.keys(LANGUAGES).map((lang) => ({ params: { lang } }));
}

// The language code written into the page (<html lang>, lang="…").
// `gr` is the site's own code (URLs, content folders, ui.ts), but it is not a
// real language code: Greek is `el`. Browsers drop the accents from Greek
// capitals (CSS `uppercase`) only when the page says `el`.
const HTML_LANGS: Record<Lang, string> = {
  gr: "el",
  nl: "nl",
  en: "en",
};

export function htmlLang(lang: Lang): string {
  return HTML_LANGS[lang];
}

// Locales chosen so every language renders dd/mm/yyyy (European style).
const DATE_LOCALES: Record<Lang, string> = {
  gr: "el-GR",
  nl: "nl-NL",
  en: "en-GB",
};

// Dates are shown as they fall in the Netherlands, whatever time zone the build
// runs in. Without it, a build in UTC shows an event at 00:30 in Rotterdam on
// the day before (#175).
export const SITE_TIME_ZONE = "Europe/Amsterdam";

export function formatDate(date: Date, lang: Lang): string {
  return date.toLocaleDateString(DATE_LOCALES[lang], {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: SITE_TIME_ZONE,
  });
}
