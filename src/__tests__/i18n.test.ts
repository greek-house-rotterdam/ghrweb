import { describe, it, expect } from "vitest";
import {
  LANGUAGES,
  DEFAULT_LANG,
  getLangFromSlug,
  getStaticLangPaths,
  formatDate,
  htmlLang,
  type Lang,
} from "../i18n/utils";
import { t } from "../i18n/ui";

const ALL_LANGS: Lang[] = ["gr", "nl", "en"];

describe("i18n/utils", () => {
  describe("LANGUAGES", () => {
    it("defines gr, nl, en", () => {
      expect(Object.keys(LANGUAGES)).toEqual(["gr", "nl", "en"]);
    });
  });

  describe("DEFAULT_LANG", () => {
    it("is gr", () => {
      expect(DEFAULT_LANG).toBe("gr");
    });
  });

  describe("getLangFromSlug", () => {
    it("extracts gr from a Greek slug", () => {
      expect(getLangFromSlug("gr/news/hello")).toBe("gr");
    });

    it("extracts nl from a Dutch slug", () => {
      expect(getLangFromSlug("nl/events/test")).toBe("nl");
    });

    it("extracts en from an English slug", () => {
      expect(getLangFromSlug("en/about")).toBe("en");
    });

    it("returns default lang for an unknown prefix", () => {
      expect(getLangFromSlug("fr/news/bonjour")).toBe("gr");
    });

    it("returns default lang for an empty string", () => {
      expect(getLangFromSlug("")).toBe("gr");
    });

    it("handles slug with no slashes", () => {
      expect(getLangFromSlug("gr")).toBe("gr");
    });
  });

  describe("getStaticLangPaths", () => {
    it("returns one path per language", () => {
      const paths = getStaticLangPaths();
      expect(paths).toEqual([
        { params: { lang: "gr" } },
        { params: { lang: "nl" } },
        { params: { lang: "en" } },
      ]);
    });
  });

  // `gr` is the site's own code; pages must declare the real code `el`, or
  // browsers keep the accents on Greek capitals («ΔΡΆΣΕΙΣ»).
  describe("htmlLang", () => {
    it("writes Greek as el", () => {
      expect(htmlLang("gr")).toBe("el");
    });

    it("keeps nl and en", () => {
      expect(htmlLang("nl")).toBe("nl");
      expect(htmlLang("en")).toBe("en");
    });
  });

  // Feedback called out that dates were rendering in American (mm/dd/yyyy) style;
  // every locale must render European (dd/mm/yyyy) regardless of language.
  describe("formatDate", () => {
    const date = new Date(Date.UTC(2026, 0, 7)); // 7 January 2026

    it.each(ALL_LANGS)("renders %s in dd/mm/yyyy", (lang) => {
      const formatted = formatDate(date, lang);
      // Some locales use "-" as separator, others "/" — only the order matters.
      const parts = formatted.split(/[\/\-\.\s]/).filter(Boolean);
      expect(parts[0]).toBe("07");
      expect(parts[1]).toBe("01");
      expect(parts[2]).toBe("2026");
    });

    it("never produces American mm/dd/yyyy order for English", () => {
      // 7 Jan: dd=07, mm=01. If month came first, parts[0] would be "01".
      const parts = formatDate(date, "en").split(/[\/\-\.\s]/).filter(Boolean);
      expect(parts[0]).not.toBe("01");
    });

    // Events near midnight must show the day they happen in Rotterdam, also
    // when the build runs in UTC (#175).
    describe("in Netherlands time", () => {
      const dayOf = (iso: string) => formatDate(new Date(iso), "en").split(/[\/\-\.\s]/).filter(Boolean).join("/");

      // Runs `check` with the process in another time zone, as a build machine might be.
      function inTimeZone(tz: string, check: () => void) {
        const before = process.env.TZ;
        process.env.TZ = tz;
        try {
          check();
        } finally {
          if (before === undefined) delete process.env.TZ;
          else process.env.TZ = before;
        }
      }

      it.each(["UTC", "America/New_York", "Asia/Tokyo"])("shows the Rotterdam day when the build runs in %s", (tz) => {
        inTimeZone(tz, () => {
          // 00:30 on 12 December in Rotterdam (winter time, UTC+1).
          expect(dayOf("2026-12-12T00:30:00+01:00")).toBe("12/12/2026");
          // 23:30 on 12 December in Rotterdam.
          expect(dayOf("2026-12-12T23:30:00+01:00")).toBe("12/12/2026");
          // 00:30 on 1 July in Rotterdam (summer time, UTC+2).
          expect(dayOf("2027-07-01T00:30:00+02:00")).toBe("01/07/2027");
          // 23:30 on 30 June in Rotterdam.
          expect(dayOf("2027-06-30T23:30:00+02:00")).toBe("30/06/2027");
        });
      });

      it("shows a date without a time on that same day", () => {
        // A news date written as 2026-01-07 is read as midnight UTC.
        inTimeZone("UTC", () => expect(dayOf("2026-01-07")).toBe("07/01/2026"));
      });
    });
  });
});

describe("i18n/ui", () => {
  describe("t()", () => {
    it("returns Greek translation", () => {
      expect(t("gr", "nav.home")).toBe("Αρχική");
    });

    it("returns Dutch translation", () => {
      expect(t("nl", "nav.home")).toBe("Home");
    });

    it("returns English translation", () => {
      expect(t("en", "nav.home")).toBe("Home");
    });

    it("returns different values per language for the same key", () => {
      expect(t("gr", "nav.events")).toBe("Εκδηλώσεις");
      expect(t("nl", "nav.events")).toBe("Evenementen");
      expect(t("en", "nav.events")).toBe("Events");
    });
  });

  describe("translation completeness", () => {
    it("all languages have nav.home defined", () => {
      for (const lang of ALL_LANGS) {
        expect(t(lang, "nav.home")).toBeTruthy();
      }
    });

    it("all languages have events keys defined", () => {
      for (const lang of ALL_LANGS) {
        expect(t(lang, "events.registration-required")).toBeTruthy();
        expect(t(lang, "events.none")).toBeTruthy();
      }
    });

    it("all languages have activities keys defined", () => {
      for (const lang of ALL_LANGS) {
        expect(t(lang, "activities.title")).toBeTruthy();
        expect(t(lang, "activities.intro")).toBeTruthy();
      }
    });

    it("all languages have resources keys defined", () => {
      for (const lang of ALL_LANGS) {
        expect(t(lang, "resources.title")).toBeTruthy();
        expect(t(lang, "resources.intro")).toBeTruthy();
      }
    });

    // Feedback section 1 (Σχετικά / About): history teaser, board intro and KVK
    // must exist for every language.
    it("all languages have about keys defined", () => {
      for (const lang of ALL_LANGS) {
        expect(t(lang, "about.history.title")).toBeTruthy();
        expect(t(lang, "about.history.intro")).toBeTruthy();
        expect(t(lang, "about.history.cta")).toBeTruthy();
        expect(t(lang, "about.board.intro")).toBeTruthy();
        expect(t(lang, "about.kvk")).toContain("40342991");
      }
    });

    // Event categories must be localized — feedback called out that Greek tabs
    // were showing English category names.
    it("event categories are translated for every language", () => {
      const cats = ["workshop", "social", "cultural", "class", "meetup", "other"] as const;
      for (const lang of ALL_LANGS) {
        for (const cat of cats) {
          expect(t(lang, `events.category.${cat}` as const)).toBeTruthy();
        }
      }
      // Greek must use Greek words, not the English category id.
      expect(t("gr", "events.category.workshop")).toBe("Εργαστήρι");
      expect(t("gr", "events.category.cultural")).toBe("Πολιτιστική");
    });
  });

  describe("feedback-driven copy", () => {
    it("Greek nav uses Δράσεις (not Δραστηριότητες)", () => {
      expect(t("gr", "nav.activities")).toBe("Δράσεις");
      expect(t("gr", "activities.title")).toBe("Δράσεις");
    });

    it("hero title includes the definite article in every language", () => {
      expect(t("gr", "home.hero.title").startsWith("Το ")).toBe(true);
      expect(t("en", "home.hero.title").startsWith("The ")).toBe(true);
      expect(t("nl", "home.hero.title").startsWith("Het ")).toBe(true);
    });

    it("member tier titles match the official taxonomy", () => {
      expect(t("gr", "member.member.title")).toBe("Τακτικό Μέλος");
      expect(t("gr", "member.candidate.title")).toBe("Υποψήφιο Μέλος");
      expect(t("gr", "member.friend.title")).toBe("Φίλος");
    });
  });
});
