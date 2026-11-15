// Entries of the collections editors manage in /admin, without the ones they
// hid with "Απόκρυψη από τον ιστότοπο" (Hide from site). Hidden entries get no
// page, no redirect and no place in any list, in every language.
//
// Pages must read these collections through getVisible(), never through
// getCollection() directly: src/__tests__/visible.test.ts checks this.

import { getCollection, type CollectionEntry } from "astro:content";

export const EDITABLE_COLLECTIONS = ["news", "activities", "resources", "faq"] as const;
export type EditableCollection = (typeof EDITABLE_COLLECTIONS)[number];

export function isVisible(entry: { data: { hidden?: boolean } }): boolean {
  return entry.data.hidden !== true;
}

export async function getVisible<C extends EditableCollection>(name: C): Promise<CollectionEntry<C>[]> {
  const entries = (await getCollection(name)) as CollectionEntry<C>[];
  return entries.filter((e) => isVisible(e as { data: { hidden?: boolean } }));
}
