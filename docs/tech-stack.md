# Tech Stack — Greek House in Rotterdam Website

> Chosen stack and rationale for the GHR website. Based on requirements, developer profile, and project constraints.

---

## Stack Summary

| Layer | Choice | Role |
|-------|--------|------|
| **Framework** | Astro | Static site generator — outputs plain HTML, built-in i18n, excellent SEO |
| **Styling** | Tailwind CSS | Utility-first CSS — fast to build, AI-friendly, responsive by default |
| **CMS** | Decap CMS | Git-based admin UI at `/admin` — free, no backend, non-technical friendly |
| **Hosting** | Cloudflare Pages | Static hosting with global CDN — free tier, auto-deploy from GitHub |
| **Translation** | GitHub Action + DeepL API | Auto-translates content on commit — trilingual (GR/NL/EN) |
| **Forms** | Google Forms (embedded) | Contact and enrollment — built-in spam protection, responses in Google Sheets |
| **Analytics** | Google Analytics (GA4) | Traffic and engagement tracking — requires cookie consent banner (GDPR) |
| **Auth/Access** | GitHub Organization (free tier) | Team-based repo access — admin/editor permissions via GitHub roles |

---

## Architecture & Workflows

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GITHUB REPOSITORY                            │
│                     (single source of truth)                        │
│                                                                     │
│  src/content/news/gr/  ← Markdown posts                            │
│  src/content/events/gr/                                             │
│  src/pages/            ← Page templates (.astro)                    │
│  src/components/       ← UI components                              │
│  src/i18n/             ← Translation strings                        │
│  public/images/        ← Uploaded images                            │
│  public/admin/         ← Decap CMS admin panel                      │
└──────────┬───────────────────────┬──────────────────────────────────┘
           │                       │
           │ on push to main       │ GitHub Action triggered
           ▼                       ▼
┌──────────────────┐    ┌─────────────────────┐
│  CLOUDFLARE      │    │  TRANSLATION        │
│  PAGES           │    │  WORKFLOW            │
│                  │    │                     │
│  Auto-builds     │    │  Detects new/changed│
│  Astro site      │    │  content in gr/     │
│  Deploys to      │    │  Calls DeepL API    │
│  global CDN      │    │  Commits nl/ + en/  │
│                  │    │  versions to repo   │
└──────────────────┘    └─────────────────────┘
           │
           ▼
┌──────────────────┐    ┌─────────────────────┐
│  LIVE WEBSITE    │    │  GOOGLE FORMS       │
│  (static HTML)   │    │  (embedded)         │
│                  │    │                     │
│  yoursite.com    │    │  Contact form       │
│  /gr/ /nl/ /en/  │    │  Enrollment form    │
│                  │    │  → Google Sheets    │
└──────────────────┘    └─────────────────────┘
```

### Developer Workflow

```
Code change (pages, components, styles, config)
  │
  ▼
Edit locally in IDE  →  git push to main
                              │
                              ▼
                     Cloudflare auto-builds & deploys
                              │
                              ▼
                         Live in ~30 seconds
```

### Admin Workflow (non-technical)

```
Visit yoursite.com/admin  →  Log in (GitHub OAuth)
  │
  ▼
Write/edit post in visual editor  →  Click "Publish"
  │
  ▼
Decap CMS commits Markdown file to GitHub repo
  │
  ├──→ Cloudflare rebuilds site (~30 sec)
  └──→ GitHub Action translates to other languages
         │
         ▼
       Cloudflare rebuilds again with translations
```

### Data Storage

| Data | Stored in | Database needed? |
|------|-----------|-----------------|
| Posts & pages | Markdown files in GitHub repo | No |
| Images | `public/images/` in GitHub repo | No |
| UI translations | JSON files in GitHub repo | No |
| Form submissions | Google Sheets (via Google Forms) | No |
| Analytics | Google Analytics GA4 (external) | No |

**No database. No server. GitHub is the single source of truth.**

---

## Why This Stack

### For the developer

- Astro is the most backend-developer-friendly frontend framework — mostly HTML with `.astro` templating
- No React/Vue/Svelte required (can be added later if needed)
- AI coding assistants are excellent at generating Astro + Tailwind
- GitHub Actions for automation fits existing skills
- Code-first, full control over output

### For the admins

- Decap CMS provides a visual editor at `yoursite.com/admin`
- Log in via GitHub, write a post, hit "Publish" — done
- No terminal, no Git knowledge, no code
- Rich text editing, image upload, draft/publish workflow
- GitHub Organization with teams enables admin/editor role separation
- Branch protection allows editorial review: editors submit, admins approve

### For the project

- **Annual cost:** ~€0–20/year (domain only — hosting and CMS are free)
- **Security:** Static files = near-zero attack surface. Cloudflare adds DDoS protection and SSL
- **Performance:** Static HTML on a global CDN = blazing fast
- **SEO:** Static HTML is the best possible format for search engines
- **Timeline:** 2 months is achievable — Astro sites are fast to build with AI assistance

---

## Translation Strategy

Two layers:

| Layer | What | How |
|-------|------|-----|
| **UI strings** | Nav, buttons, footer, labels | JSON translation files — translated once, maintained manually |
| **Content** | News, events, page text | GitHub Action auto-translates on commit using DeepL API |

**Content flow:** Admin publishes in one language via Decap CMS → commit lands in repo → GitHub Action detects new/changed content → calls DeepL API → commits translated versions → Cloudflare rebuilds the site.

**No infinite loops:** The translation workflow commits translated files back to `main`, which could re-trigger itself. This is prevented by GitHub's built-in rule: pushes made with `GITHUB_TOKEN` do not create new workflow runs. External integrations (Cloudflare Pages) still receive the push event and rebuild normally.

---

## GitHub Actions

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **Translation** | Content file added/changed on `main` | Auto-translate to other two languages |
| **Dependency updates** | Scheduled (Renovate/Dependabot) | Keep npm packages current |

Deployment is handled by Cloudflare Pages directly (built-in GitHub integration). No GitHub Action needed.

---

## Security Model

- **Static hosting** — no server, no runtime, no database to exploit
- **Cloudflare** — DDoS protection, SSL, WAF included on free tier
- **Decap CMS** — runs in browser, authenticates via GitHub OAuth, commits directly to repo
- **No user uploads** — eliminates file-based attack vectors
- **Google Forms** — form processing happens on Google's infrastructure, not ours
- **GitHub Organization** — team-based access control, individual accountability, supports enforcing 2FA for all members
- **Owner redundancy** — at least 2 Organization Owners required (e.g., developer + board president) to prevent lockout if one loses access. Losing the sole Owner means losing control of the repo, CMS access, and deployment pipeline.

The only authentication surface is GitHub OAuth (supports 2FA).

---

## Decisions Log

Lightweight ADRs — each decision, why it was made, and what was rejected.

| # | Decision | Chosen | Why | Rejected alternatives |
|---|----------|--------|-----|----------------------|
| 1 | Framework | Astro | Static output, built-in i18n, HTML-first (suits backend dev profile), AI-friendly | Hugo (Go templating less intuitive), Next.js/Nuxt (overkill — no SSR or client interactivity needed) |
| 2 | Styling | Tailwind CSS | AI assistants generate it well, utility-first = consistent, no custom CSS to maintain | Plain CSS (slow to build), Bootstrap (opinionated, heavier) |
| 3 | CMS | Decap CMS | Free, Git-based (no extra backend), web UI for non-technical admins | WordPress (PHP, security burden), Contentful/Sanity (paid tiers, external dependency) |
| 4 | Hosting | Cloudflare Pages | Free tier, global CDN, auto-deploy from GitHub, DDoS/SSL included | Firebase Hosting (similar but Cloudflare CDN is faster globally), Netlify (comparable but Cloudflare edges on performance) |
| 5 | Forms | Google Forms (embedded) | Free, built-in spam protection, responses in Google Sheets, no backend needed | Custom form + API (unnecessary complexity, needs spam protection, needs a database) |
| 6 | Database | None | No dynamic data — content is Markdown in Git, forms go to Google Sheets | Firebase Firestore, Supabase (no use case — would add cost and complexity for zero benefit) |
| 7 | Content storage | Markdown in GitHub repo | Version-controlled, portable, works with Decap CMS and Astro content collections | Database-backed CMS (unnecessary layer), Cloudflare KV/R2 (overkill for text content) |
| 8 | Translation approach | GitHub Action + API | Fully automated, triggers on content commit, no manual step for admins | Manual translation (doesn't scale), i18n plugin (most only handle UI strings, not content) |
| 9 | Deployment | Cloudflare auto-deploy | Push to `main` = live in ~30 sec, no CI/CD config needed | GitHub Actions deploy step (unnecessary — Cloudflare handles it natively) |
| 10 | Analytics | Google Analytics (GA4) | Free, full-featured, already referenced in success metrics. Requires cookie consent banner (GDPR) | Plausible (~€9/mo, GDPR-friendly but paid), Firebase Analytics (designed for mobile apps/SPAs, not static sites) |
| 11 | CMS auth / access control | GitHub Organization (free tier) + GitHub OAuth | Teams for admin/editor roles, branch protection for editorial workflow, free, individual accountability | Netlify Identity (adds external dependency, free tier limited to 5 users), shared GitHub account (no audit trail, no individual access control) |
| 12 | Repository visibility | Public | Enables branch protection rules, required PR reviews, and Code Owners on the free tier — all unavailable for private repos without a paid plan. Unlimited GitHub Actions minutes. No secrets to protect — site content is public by nature. | Private repo (would require GitHub Team at $4/user/month to get branch protection, which the editorial workflow depends on) |

### Open Decisions

| # | Decision | Options | Status |
|---|----------|---------|--------|
| ~~1~~ | ~~Translation API~~ | ~~DeepL API vs OpenAI API~~ | **Decided: DeepL API** — higher translation quality for European languages, free tier (500k chars/mo) more than sufficient for this project's volume. Implemented in `.github/workflows/translate.yml`. |
