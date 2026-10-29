/// <reference types="vitest/config" />
// Lets tests import .astro components (e.g. the redirect page) through
// Astro's container. Other tests are unaffected.
import { getViteConfig } from "astro/config";

export default getViteConfig({
  test: {
    exclude: [".claude/**", "node_modules/**"],
  },
});
