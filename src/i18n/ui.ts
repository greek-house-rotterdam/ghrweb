import type { Lang } from "./utils";

const ui = {
  gr: {
    "nav.home": "Αρχική",
    "nav.history": "Ιστορία",
    "nav.teams": "Ομάδες",
    "nav.news": "Νέα",
    "nav.events": "Εκδηλώσεις",
    "nav.contact": "Επικοινωνία",
    "nav.about": "Σχετικά",
    "nav.faq": "FAQ",
    "nav.become-a-member": "Γίνε Μέλος",
    "footer.rights": "Με επιφύλαξη παντός δικαιώματος.",
    "common.read-more": "Διαβάστε περισσότερα",
  },
  nl: {
    "nav.home": "Home",
    "nav.history": "Geschiedenis",
    "nav.teams": "Teams",
    "nav.news": "Nieuws",
    "nav.events": "Evenementen",
    "nav.contact": "Contact",
    "nav.about": "Over ons",
    "nav.faq": "FAQ",
    "nav.become-a-member": "Word Lid",
    "footer.rights": "Alle rechten voorbehouden.",
    "common.read-more": "Lees meer",
  },
  en: {
    "nav.home": "Home",
    "nav.history": "History",
    "nav.teams": "Teams",
    "nav.news": "News",
    "nav.events": "Events",
    "nav.contact": "Contact",
    "nav.about": "About",
    "nav.faq": "FAQ",
    "nav.become-a-member": "Become a Member",
    "footer.rights": "All rights reserved.",
    "common.read-more": "Read more",
  },
} as const;

export type UIKey = keyof (typeof ui)["gr"];

export function t(lang: Lang, key: UIKey): string {
  return ui[lang][key];
}
