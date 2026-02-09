# FAQ & Knowledge Base

> Curated insights from development Q&A sessions. Organized by topic for quick reference.

---

## Decap CMS

### Where does content go when an admin publishes?

Content goes to the `src/content/` directories as **Markdown files** — not to `public/admin/config.yml`. The config file only defines CMS structure (collections, fields, settings). It never changes when content is added or edited.

- News: `src/content/news/{gr,nl,en}/`
- Events: `src/content/events/{gr,nl,en}/`

Locally, Decap writes directly to these files on disk. In production, it commits them to the GitHub repo, triggering a Cloudflare Pages rebuild.

### How does the local CMS workflow work?

Run `npm run dev:cms` to start both the Astro dev server and the Decap proxy server (`decap-server` on port 8081). Visit `http://localhost:4321/admin/index.html` — no GitHub login required.

The `local_backend: true` setting in `public/admin/config.yml` enables this. Changes write directly to local files.

### Is `local_backend: true` safe to leave in production?

**Yes.** Decap CMS only activates `local_backend` on `localhost` (or explicitly configured `allowed_hosts`). On any production domain, it's silently ignored and the GitHub backend takes over. No environment variable or build-time toggle needed.

---

## Astro

### What does Astro actually do?

Astro is a **static site generator**. It takes `.astro` templates and Markdown content files, combines them at build time, and outputs plain HTML/CSS/JS files. There is no server running in production — visitors get pre-built HTML from a CDN.

Think of it as a compiler: templates + content in, static website out.

### Why Astro instead of Next.js?

Next.js is designed for full web applications with client-side interactivity (dashboards, real-time features, authenticated experiences). It ships the React runtime (~80-100KB) to every visitor.

This project is a content hub with no interactivity beyond navigation and forms. Astro is purpose-built for this:

| | Astro | Next.js (static export) |
|---|---|---|
| Designed for | Content/marketing sites | Full web applications |
| Default JS shipped | Zero | React runtime (~80-100KB) |
| Learning curve | HTML-like templates | Must learn React (components, hooks, JSX) |
| i18n | Built-in routing | Manual setup or extra packages |
| Content collections | Built-in | Manual or requires MDX plugins |

---

## Permissions & Access Control

### How are admin vs. editor roles managed?

Decap CMS has no built-in role system. Permission tiers are handled at the **GitHub level** using a **GitHub Organization (free tier)**:

- **Admins** (`Maintain` role): Full repo access — push to `main`, merge PRs, manage settings
- **Editors** (`Write` role): Can create content — with branch protection on `main`, their changes go through a PR that an admin reviews and approves

This creates a lightweight editorial workflow: editor writes a post via Decap CMS → PR created → admin reviews and merges → site rebuilds.

### Does every member need a GitHub account?

**Yes.** GitHub OAuth requires each person to have their own (free) GitHub account. There is no "log in with email" option with the GitHub backend.

If this becomes a dealbreaker:

- **Netlify Identity** — email/password login, no GitHub needed. Free tier limited to 5 users, adds Netlify as a dependency.
- **Cloudflare Access** — email-based auth, free for up to 50 users. More complex to integrate with Decap CMS's Git backend.

For a small org (5-10 people), asking members to create GitHub accounts is the pragmatic choice.

---

## Analytics

### Why Google Analytics (GA4) instead of Firebase Analytics?

Firebase Analytics is designed for **mobile apps and SPAs**. It requires the Firebase SDK and is optimized for in-app events, screen views, and user engagement in native/hybrid apps. For a static HTML website, it's the wrong tool.

GA4 is the standard for websites. Implementation is a single `<script>` tag in the site layout.

### What about GDPR?

GA4 uses cookies, so EU visitors (Dutch, Greek) require a **cookie consent banner** before GA4 loads. This is a hard requirement under GDPR.

If the consent banner becomes a maintenance burden, **Plausible** (~€9/month) is a cookieless alternative that's GDPR-compliant by design — no consent banner needed. It covers the essentials (visitors, pages, referrers) without the full GA4 feature set.

---

## Cost Comparison: Current Stack vs. Managed Hosting

| | Current stack (Astro + Cloudflare) | Hostinger (managed hosting) |
|---|---|---|
| Hosting | Free (Cloudflare Pages free tier) | ~€36-48/year (Premium plan) |
| CMS | Free (Decap CMS) | Included (Website Builder) or WordPress |
| Domain | ~€10-15/year | ~€10-15/year |
| SSL | Free (Cloudflare) | Free (included) |
| CDN | Free (Cloudflare global CDN) | Cloudflare CDN on higher tiers |
| Translation | DeepL API free tier | Manual or paid plugin |
| Forms | Free (Google Forms) | Included or WP plugin |
| **Total/year** | **~€10-15** | **~€50-65** |

### Beyond price

| | Current stack | Hostinger |
|---|---|---|
| Performance | Excellent (static + global CDN) | Good (shared server) |
| Security | Excellent (no server to hack) | Moderate (WordPress = constant patching) |
| Maintenance | Near-zero | Ongoing (updates, backups, plugin conflicts) |
| Admin ease | Moderate (Decap CMS — functional but basic) | High (drag-and-drop builder) |
| Developer control | Full | Limited |
| Vendor lock-in | None (code in GitHub, fully portable) | High (migration is painful) |

**Bottom line:** The current stack saves ~€40-50/year, is faster, more secure, and fully portable. The tradeoff is a less polished admin editing experience.

---

## Templates & UI Resources

### Astro-specific themes

[astro.build/themes](https://astro.build/themes/) — free and paid Astro templates, many using Tailwind. Filter by "blog", "portfolio", etc. Starting from one of these can save weeks of work.

### Free Tailwind component libraries

- [Flowbite](https://flowbite.com/) — comprehensive free component library
- [HyperUI](https://www.hyperui.dev/) — copy-paste Tailwind components
- [DaisyUI](https://daisyui.com/) — pre-styled themes on top of Tailwind

### Premium (paid)

- [Tailwind UI](https://tailwindui.com/) — official premium components from the Tailwind team (~$299 one-time)
