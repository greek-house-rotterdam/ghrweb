// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import { satteri } from "@astrojs/markdown-satteri";
import { localizeContentLinks } from "./src/lib/localize-links.ts";

// `astro dev` only: open Decap at /admin/, as Cloudflare does in production.
// Vite's dev server serves a public/ file only at its exact path
// (/admin/index.html), so /admin/ got the 404 page.
/** @returns {import("vite").Plugin} */
function adminIndexInDev() {
  return {
    name: "admin-index-in-dev",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const { pathname, search } = new URL(req.url ?? "/", "http://localhost");
        if (pathname === "/admin") {
          // Redirect, not serve: under /admin, Decap would look for /config.yml.
          res.statusCode = 307;
          res.setHeader("Location", `/admin/${search}`);
          return res.end();
        }
        if (pathname === "/admin/") req.url = `/admin/index.html${search}`;
        next();
      });
    },
  };
}

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
    plugins: [tailwindcss(), adminIndexInDev()],
  },
});
