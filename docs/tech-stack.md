# Tech Stack — Greek House in Rotterdam Website

> Chosen stack and rationale for the GHR website. Based on requirements, developer profile, and project constraints.

---

## Stack Summary

| Layer | Choice | Role |
|-------|--------|------|
| **Framework** | Astro | Static site generator — outputs plain HTML, built-in i18n, excellent SEO |
| **Styling** | Tailwind CSS | Utility-first CSS — fast to build, AI-friendly, responsive by default |
| **CMS** | Decap CMS | Git-based admin UI at `/admin` — free, no backend, non-technical friendly |
| **Hosting** | Cloudflare Workers (static assets) | Static hosting with global CDN — free tier, auto-deploy from GitHub. Configured via `wrangler.json`. |
| **Translation** | GitHub Action + DeepL API | Auto-translates content within PRs — trilingual (GR/NL/EN) |
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
│  wrangler.json         ← Cloudflare deployment config               │
│  CODEOWNERS            ← Requires translators review on content     │
└──────────┬───────────────────────┬──────────────────────────────────┘
           │                       │
           │ on pull request       │ GitHub Action triggered
           ▼                       ▼
┌──────────────────┐    ┌─────────────────────┐
│  CLOUDFLARE      │    │  TRANSLATE CONTENT  │
│  PAGES           │    │  WORKFLOW           │
│                  │    │                     │
│  Builds preview  │    │  Detects new/changed│
│  for each PR     │    │  content → translate│
│  Deploys to CDN  │    │  Detects deletions  │
│  on merge to     │    │  → sync across langs│
│  main            │    │  Commits to PR      │
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
Edit locally in IDE  →  Open PR to main
                              │
                              ▼
                     Cloudflare builds deploy preview
                              │
                              ▼
                     Review preview → Merge PR
                              │
                              ▼
                     Cloudflare deploys to production (~30 sec)
```

### Content Workflow (editors & admins)

```
Visit yoursite.com/admin  →  Log in (GitHub OAuth)
  │
  ▼
Write/edit content in visual editor  →  Click "Publish"
  │
  ▼
Decap CMS opens a PR (editorial workflow)
  │
  ├──→ Translation workflow runs on PR
  │      Detects new/changed content → translates via DeepL
  │      Commits translations to the same PR
  │
  ├──→ Cloudflare builds deploy preview of the PR
  │
  └──→ Translators team auto-requested for review (CODEOWNERS)
         ⛔ PR blocked until CODEOWNER approves
         │
         ▼
       Reviewer approves → Admin merges PR
         │
         ▼
       Cloudflare deploys to production
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

## UI Components

**Strategy:** Individual components, not starter templates. The codebase already has i18n, content collections, Decap CMS integration, and deployment pipelines — a template would overwrite all of this for marginal design benefit.

| Library | Role | How it's used |
|---------|------|---------------|
| **Starwind UI** | Interactive components | CLI-installed Astro-native components (accordion, dropdown, mobile nav, carousel). Code ownership — files live in the project. |
| **HyperUI** | Static layout blocks | Copy-paste Tailwind HTML for one-off sections (hero, CTA, timeline, team cards, footer). No dependency. |

Both are Tailwind CSS v4 compatible and ship zero JavaScript by default.

**Component-to-page mapping:**

| Page | Key components | Source |
|------|---------------|--------|
| Home | Hero, news cards, event cards, CTA | HyperUI + Starwind Card |
| History | Timeline | HyperUI |
| Teams | Team/activity cards | HyperUI + Starwind Card, Badge |
| News / Events | Card grid, pagination | Starwind Card, Pagination |
| FAQ | Accordion | Starwind Accordion |
| Contact | Info layout, map embed | HyperUI |
| About | Content section, board cards | HyperUI + Starwind Avatar |
| Header | Responsive nav, mobile drawer | Starwind Sheet |
| Footer | Multi-column, social icons | HyperUI |

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
- Repository ruleset enforces editorial review: editors submit, CODEOWNER must approve before merge is allowed

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
| **Content** | News, events, page text | GitHub Action auto-translates within PRs using DeepL API |

**Content flow:** Editor/admin creates content in one language → PR is opened (via Decap CMS or git) → translation workflow detects new/changed files → calls DeepL API → commits translations to the same PR → verification script checks for missing files → **PR is blocked until the designated CODEOWNER approves** → admin reviews the deploy preview and merges → Cloudflare deploys.

**Manual edit protection:** Translated files include a `source_hash` in frontmatter — a fingerprint of the source content they were translated from. On subsequent workflow runs, the hash is compared: if the source hasn't changed, the translation is skipped. This allows reviewers to fix individual translations without retranslation overwriting their edits. For translations that should never be auto-overwritten (e.g., professionally translated content), editors can set `translation_locked: true` in frontmatter. See `docs/workflows.md` for the full workflow.

**Deletion flow:** Content is deleted in a PR → translation workflow detects deleted files → removes corresponding files in the other two language folders → commits deletions to the same PR. This prevents "ghost posts" (translations that outlive their source).

**No infinite loops:** The translation workflow commits to the PR branch using `GITHUB_TOKEN`. GitHub's built-in rule ensures these pushes do not trigger new workflow runs.

**Future option — AI translation:** DeepL may be replaced by Gemini 2.5 Flash as the primary translation backend if quality or cost issues arise. AI models handle Markdown frontmatter more reliably via system prompts. DeepL would remain as a fallback. See `docs/pending-tasks.md` (Feature F1) for trigger conditions.

---

## GitHub Actions

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **Translate Content** | PR with changes to `src/content/**/*.md` | Auto-translate new/changed content within the PR; sync deletions; verify content integrity |
| **Image QA** | PR with changes to `public/images/**` | Validate image dimensions, file size, and format. Auto-optimize (resize, compress, convert to WebP). Block merge only for hard limit violations. Uses Pillow — no AI. |
| **Content Review** | PR with changes to `src/content/**/*.md` | AI review (Gemini Flash) against style guide. Posts advisory PR comments — does not block merge. |
| **Tests** | PR with changes to code files (`.ts`, `.astro`, `.py`, configs) | Runs Node (vitest) and Python (pytest) test suites in parallel. Does not trigger on content-only PRs. |

All workflows use path filters — they only run when the PR touches relevant files. Only the **Cloudflare Pages** build is a required status check for merging. The other checks are informational. See `docs/github-access-control.md` for rationale.

Deployment is handled by Cloudflare Pages directly (built-in GitHub integration). No GitHub Action needed. Cloudflare also builds deploy previews for every PR, providing a rendered preview URL for admin review.

---

## Security Model

- **Static hosting** — no server, no runtime, no database to exploit
- **Cloudflare** — DDoS protection, SSL, WAF included on free tier
- **Cloudflare access model** — organization-owned account, with `@PanoEvJ` assigned Super Admin for setup/operations
- **Decap CMS** — runs in browser, authenticates via GitHub OAuth, commits directly to repo
- **No user uploads** — eliminates file-based attack vectors
- **Google Forms** — form processing happens on Google's infrastructure, not ours
- **GitHub Organization** — team-based access control, individual accountability, 2FA enforced for all members
- **Owner redundancy** — at least 2 Organization Owners required (e.g., developer + board president) to prevent lockout if one loses access. Losing the sole Owner means losing control of the repo, CMS access, and deployment pipeline.

The only authentication surface is GitHub OAuth (2FA required).

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
| 8 | Translation approach | GitHub Action + DeepL API (PR-based) | Triggers on PR, translates within the PR before merge. Admin reviews rendered preview. | Push-to-main approach (blocked by branch protection on free tier), manual translation (doesn't scale) |
| 9 | Deployment | Cloudflare Workers auto-deploy | Push to production branch runs `npm run build` + `npx wrangler deploy`. Preview branches run `npx wrangler versions upload`. Configured via `wrangler.json` (static assets from `./dist`). Temporary URL: `*.pages.dev` until custom domain is connected. | GitHub Actions deploy step (unnecessary — Cloudflare handles it natively) |
| 10 | Analytics | Google Analytics (GA4) | Free, full-featured, already referenced in success metrics. Requires cookie consent banner (GDPR) | Plausible (~€9/mo, GDPR-friendly but paid), Firebase Analytics (designed for mobile apps/SPAs, not static sites) |
| 11 | CMS auth / access control | GitHub Organization (free tier) + GitHub OAuth | Teams for admin/editor/translator roles, repository rulesets for editorial workflow, CODEOWNERS for translation review, free, individual accountability | Netlify Identity (adds external dependency, free tier limited to 5 users), shared GitHub account (no audit trail, no individual access control) |
| 12 | Repository visibility | Public | Enables rulesets, required PR reviews, and Code Owners on the free tier — all unavailable for private repos without a paid plan. Unlimited GitHub Actions minutes. No secrets to protect — site content is public by nature. | Private repo (would require GitHub Team at $4/user/month to get rulesets, which the editorial workflow depends on) |
| 13 | Branch protection mechanism | Repository rulesets (not classic branch protection) | Supports bypass actors, squash-only merge, linear history, Code Owners review. Classic branch protection cannot add GitHub Actions as a bypass actor. Org-level rulesets require paid plan. | Classic branch protection (no granular bypass), org-level rulesets (requires GitHub Team plan at $4/user/month) |
| 14 | Git merge strategy | Squash and merge only | Clean linear history. Simplifies the merge button for non-technical users — one predictable action. Each PR becomes exactly one commit on `main`. | Merge commits (messy history), rebase (confusing for non-technical users) |
| 15 | Translation review | CODEOWNERS + translators team | Auto-requests translators team on content PRs. Enforced by "Require review from Code Owners" in the ruleset. | Manual reviewer assignment (easy to forget), no review (risks bad translations going live) |
| 16 | Infrastructure protection | CODEOWNERS + developer review | Auto-requests developer (`@PanoEvJ`) for changes to `.github/`, configs, `src/layouts/`, `src/pages/`, `package.json`. Editors can freely create content but cannot break the site's engine. | No protection (editors could accidentally break deployment), blanket admin review on everything (slows down content publishing unnecessarily) |
| 17 | UI component approach | Starwind UI + HyperUI (individual components) | Codebase already has i18n, content collections, CMS, workflows — components are additive, not destructive. Both are Astro-native / Tailwind v4 compatible, zero JS by default. | Astro starter templates (would overwrite existing infra), daisyUI (adds plugin layer and its own design system — unnecessary abstraction) |
| 18 | Translation overwrite protection | Source hash tracking (`source_hash` frontmatter field) | Deterministic, invisible to editors, no workflow changes needed. Translated files store a hash of the source content they were derived from; retranslation is skipped when the source is unchanged. Also prevents cascade translation (translated files passed as input are detected and skipped). `translation_locked: true` serves as an escape hatch for permanently protected translations. | Commit message conventions like `[skip-translate]` (fragile, only protects one push), frontmatter override flag without hash (requires editor action, stale flags accumulate), smart git diff on latest commit only (breaks on rebases and force-pushes), git blame analysis (unreliable in CI shallow checkouts) |

### Open Decisions

| # | Decision | Options | Status |
|---|----------|---------|--------|
| ~~1~~ | ~~Translation API~~ | ~~DeepL API vs OpenAI API~~ | **Decided: DeepL API** — higher translation quality for European languages, free tier (500k chars/mo) more than sufficient for this project's volume. Implemented in `.github/workflows/translate.yml`. |
| 2 | AI translation backend | Gemini 2.5 Flash vs current DeepL | **Deferred.** Revisit if DeepL quality degrades or free tier is exhausted. See `docs/pending-tasks.md` (Feature F1). |
| 3 | AI-assisted content alignment | Opt-in AI editing via CMS checkbox | **Deferred.** Revisit if editors request writing assistance or tone consistency becomes an issue. See `docs/pending-tasks.md` (Feature F2). |
