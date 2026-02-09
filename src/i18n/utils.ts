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
