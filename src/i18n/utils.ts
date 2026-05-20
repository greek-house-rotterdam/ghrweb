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

// Locales chosen so every language renders dd/mm/yyyy (European style).
const DATE_LOCALES: Record<Lang, string> = {
  gr: "el-GR",
  nl: "nl-NL",
  en: "en-GB",
};

export function formatDate(date: Date, lang: Lang): string {
  return date.toLocaleDateString(DATE_LOCALES[lang], {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
