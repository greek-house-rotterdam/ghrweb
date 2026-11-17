// The category of a "useful information" entry (resources collection), in the
// page's language. The values come from the "Category" select in /admin; an
// unknown value is shown as it is.

import { t, isUIKey } from "../i18n/ui";
import type { Lang } from "../i18n/utils";

export function categoryLabel(lang: Lang, category: string): string {
  const key = `resources.category.${category}`;
  return isUIKey(key) ? t(lang, key) : category;
}
