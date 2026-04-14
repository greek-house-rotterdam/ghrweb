import { describe, it, expect } from "vitest";
import {
  LANGUAGES,
  DEFAULT_LANG,
  getLangFromSlug,
  getStaticLangPaths,
} from "../i18n/utils";
import { t } from "../i18n/ui";

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
      const gr = t("gr", "nav.events");
      const nl = t("nl", "nav.events");
      const en = t("en", "nav.events");
      expect(gr).toBe("Εκδηλώσεις");
      expect(nl).toBe("Evenementen");
      expect(en).toBe("Events");
    });
  });

  describe("translation completeness", () => {
    it("all languages have nav.home defined", () => {
      for (const lang of ["gr", "nl", "en"] as const) {
        expect(t(lang, "nav.home")).toBeTruthy();
      }
    });

    it("all languages have events keys defined", () => {
      for (const lang of ["gr", "nl", "en"] as const) {
        expect(t(lang, "events.registration-required")).toBeTruthy();
        expect(t(lang, "events.none")).toBeTruthy();
      }
    });

    it("all languages have activities keys defined", () => {
      for (const lang of ["gr", "nl", "en"] as const) {
        expect(t(lang, "activities.title")).toBeTruthy();
        expect(t(lang, "activities.intro")).toBeTruthy();
      }
    });

    it("all languages have resources keys defined", () => {
      for (const lang of ["gr", "nl", "en"] as const) {
        expect(t(lang, "resources.title")).toBeTruthy();
        expect(t(lang, "resources.intro")).toBeTruthy();
      }
    });
  });
});
