// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import { satteri } from "@astrojs/markdown-satteri";
import { localizeContentLinks } from "./src/lib/localize-links.ts";

// https://astro.build/config
export default defineConfig({
  markdown: {
    // Links in content texts lead to the reader's language (/gr/contact in a
    // Dutch text becomes /nl/contact). See src/lib/localize-links.ts.
    // Keep @astrojs/markdown-satteri at the exact version Astro itself uses.
    processor: satteri({ hastPlugins: [localizeContentLinks] }),
  },
	i18n: {
    defaultLocale: "gr",
    locales: ["gr", "nl", "en"],
    routing: {
      prefixDefaultLocale: true,
      redirectToDefaultLocale: false,
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
