# Pending Tasks — Greek House in Rotterdam

> Tasks that are defined but cannot be completed yet. Each has a clear trigger or prerequisite.
> UX report (`docs/UX_report.pdf`) informs priorities for Phases A–C.

---

## GitHub Organization Setup

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 1 | **Enforce 2FA** for all org members | Members must enable 2FA on their personal GitHub accounts first | Org Settings → Authentication security → Require 2FA. Anyone without 2FA will be removed from the org. Inform members before enabling. |
| 2 | **Elevate t.a.klouvas to Owner** | t.a.klouvas must accept the org invitation | People → find user → Change role → Owner. Currently invited as Owner but invitation is pending. |
| 3 | **Assign members to teams** | All 3 invitees must accept their invitations | Add t.a.klouvas to **admins** team. Add jschistos and aretizoi to **editors** team. Create **translators** team and add relevant members (e.g. t.a.klouvas). (Teams → team name → Add a member) |

### Pre-Onboarding Access Checklist (`/admin`)

Use this checklist before onboarding editors to avoid the "login works, publish fails" scenario.

- [ ] All invited users accepted the GitHub organization invitation.
- [ ] All users enabled GitHub 2FA (verified in org members list).
- [ ] Teams are finalized: `admins`, `editors`, `translators`.
- [ ] Team repository permissions are correct on `ghrweb`: `admins` = Maintain, `editors` = Write, `translators` = Write.
- [ ] Repository ruleset on `main` is active: PR required, status checks required, **Code Owner review required (blocks merge until CODEOWNER approves)**.
- [ ] `CODEOWNERS` is configured: `src/content/` requires `@greek-house-rotterdam/translators`; infrastructure paths require `@PanoEvJ`.
- [ ] Decap CMS GitHub OAuth is configured and `/admin` login succeeds with an editor account.
- [ ] Smoke test passed with an editor account:
  - create a small content edit in `/admin`
  - click Publish and confirm a PR is created
  - confirm translation workflow runs (`translate` / `verify`)
  - confirm Cloudflare preview appears and updates
  - confirm admin can approve and merge

## Content & Launch

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 4 | ~~**[HIGH] Scrape and archive all content from `https://vvgn.eu/nl/`**~~ | ~~Confirm scope and permission to copy content~~ | Done. Repeatable scraper at `scripts/scrape_vvgn.py`. Outputs at `data/scrapes/vvgn/` (records, `manifest.json`, `crawl-report.md`, inventory CSV). Content-manager handoff: `docs/vvgn-content-manager-dossier.md`. |
| 5 | ~~**Connect Cloudflare to org repo**~~ | ~~Repo transfer complete~~ | Done. Connected via Cloudflare Workers & Pages (Compute → Workers & Pages → Create → Connect to Git). Uses unified Workers flow with `wrangler.json` for static asset deployment. Build: `npm run build`, deploy: `npx wrangler deploy`. `NODE_VERSION=24` set in Cloudflare env vars. Production branch: `main`. Temporary URL on `*.pages.dev` — custom domain to be connected later (Task #8). `wrangler` added as devDependency to prevent CI scaffolding wizard. |
| 6 | ~~**Configure Decap CMS OAuth**~~ | ~~Cloudflare connected (done)~~ | Done. Worker OAuth proxy at `src/oauth.ts`, GitHub OAuth App registered, Worker secrets set. Fixed cross-origin `postMessage` bug (changed target origin to `"*"` for popup→parent communication). `/admin` login tested and working. |
| 7 | ~~**Set up DeepL / translation GitHub Action**~~ | ~~Translation API decision finalized~~ | Done. Workflow at `.github/workflows/translate.yml`, script at `.github/scripts/translate.py`. Requires `DEEPL_API_KEY` secret in GitHub repo settings. |
| 9 | ~~**Evaluate OpenAI for translation**~~ | ~~Content volume or complexity increases~~ | Superseded by Future Feature F1 (AI Translation via Gemini 2.5 Flash). See "Future / Optional Enhancements" section below. |
| 8 | **Connect custom domain** | Domain DNS access available | Cloudflare project settings → Custom domains → Add domain → Update DNS records. Site is live on `*.pages.dev` in the meantime. **Also update:** 1) `base_url` in `public/admin/config.yml` to the new domain. 2) GitHub OAuth App Homepage URL and Authorization callback URL to `https://<new-domain>/callback`. |

## Security Hardening

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 10 | **Audit org-level security settings** | Org fully operational (all members joined, 2FA enforced) | Review what's not yet configured beyond current setup: rulesets, tag protection, Actions permissions, secret scanning, Dependabot alerts, deploy key policies. Free-tier limits apply — focus on what's available and meaningful. |
| 16 | **Define and document audit trail access/retention** | Cloudflare account created and org access model finalized | Verify where activity history is available and for how long across GitHub and Cloudflare. Ensure at least two Owners can access audit logs, and define a lightweight persistence process (e.g., monthly export/checkpoint if native retention is limited). Document the runbook and ownership. |
| 11 | **Configure CODEOWNERS for content and infrastructure** | Repo structure stabilized & Teams created | Create a `CODEOWNERS` file enforcing review boundaries: 1) `src/content/` owned by `@greek-house-rotterdam/translators` (ensures translation QA). 2) Infrastructure paths (`.github/`, `src/layouts/`, `src/pages/`, configs) owned by `@greek-house-rotterdam/admins` (protects site engine). **Combined with the "Require review from Code Owners" ruleset setting, this blocks PR merges until the designated CODEOWNER approves.** The merge button is disabled until approval is given. |
| 15 | **Allow other Owners to modify CODEOWNERS** | Task #11 complete | Explicitly define ownership of the `CODEOWNERS` file itself (e.g. `@greek-house-rotterdam/owners` or specific users) to ensure other Owners can update governance rules without being blocked by a single person. |

## Testing

**Tool:** [Vitest](https://vitest.dev/) — Vite-native, zero-config for TypeScript, Astro's recommended test runner. Single dependency (`vitest`).

**Principle:** Only add tests where there is clear ROI. This is a static content site, not a SaaS app — don't force tests on templates or trivial code. Focus on logic that can actually break silently.

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 12 | **Add site-level tests** | Phase A schema work complete (Tasks #23–27) | Build smoke test (Astro compiles without errors), content schema validation (frontmatter matches Zod schemas), internal link checking. Keep lightweight. Blocked until schemas are finalized to avoid rework. |
| 17 | **Unit test i18n utilities** | Utility logic is stable and non-trivial enough to warrant tests | Test `getLangFromSlug`, `getStaticLangPaths` (from `src/i18n/utils.ts`) and `t()` (from `src/i18n/ui.ts`). Good first candidates: pure functions with clear inputs/outputs. |

## UI Components & Design

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 18 | ~~**Install Starwind UI and add core interactive components**~~ | ~~None — ready now~~ | Done. Installed Starwind UI (`npx starwind@latest init`) and added 8 components: accordion, card, badge, button, sheet, pagination, avatar, dialog (sheet dependency). Merged `global.css` into `src/styles/starwind.css`. Mapped brand colors (Hellenic Blue, Mediterranean Gold) to Starwind theme tokens. Renamed `accent-*` → `accent-gold-*` across all `.astro` files to avoid conflict with Starwind's `accent` (neutral) token. Added dependencies: `tw-animate-css`, `@tailwindcss/forms`, `tailwind-variants`, `tailwind-merge`. Components at `src/components/starwind/`. |
| 20 | ~~**Define color palette and visual identity tokens**~~ | ~~None — ready now~~ | Done. Semantic color tokens now in `src/styles/starwind.css` (migrated from `global.css`) using Tailwind CSS v4 `@theme`. Primary: Hellenic Blue (`#0D5EAF`, from Greek flag). Accent: Mediterranean Gold (`#FACC15`, now `accent-gold-*`). Each has dark/light/lighter variants. All `.astro` files use semantic tokens. Added `.vscode/settings.json` with `css.lint.unknownAtRules: "ignore"` to suppress false-positive linter warnings on `@theme`. |

## Developer Tooling

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 13 | **Add Cursor AI skills for the project stack** | Active development begins | Find or create Cursor skills (`.cursor/skills/`) for: Astro (priority — primary framework, beginner frontend level), Tailwind CSS, GitHub Actions, Python scripting, and Decap CMS patterns. Better skills = more accurate AI assistance for this specific stack. (e.g. [here](https://github.com/SpillwaveSolutions/publishing-astro-websites-agentic-skill)) |

## Infrastructure & Limits

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 14 | **Investigate traffic spike capacity** | Site is live on Cloudflare (done) | Research Cloudflare Workers free tier limits (bandwidth, requests/day, concurrent connections). Determine failure mode during a viral event (e.g. major news): does it throttle, bill overages, or shut down? Document the "safe" traffic ceiling. Prerequisite now met — site is deployed. |

## Content & Image Quality

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 21 | **Image technical QA (GitHub Action)** | Translation workflow stable, content collections in use | Add a CI step that validates uploaded images before merge. Uses Pillow (no AI). Checks: max file size (≤2 MB), min resolution (800×600), max resolution (≤4096×4096), allowed formats (JPEG, PNG, WebP). Prefer **auto-optimization** (resize + compress + convert to WebP) over blocking, with a hard block only for files that exceed absolute limits (e.g. >5 MB). Runs before the translation step so bad assets are caught early. Add to `.github/workflows/translate.yml` as a preceding job, or as a separate workflow triggered on `public/images/` changes. |
| 22 | ~~**Content character limits**~~ | ~~Phase A complete~~ | Done. Title ≤100, description ≤200, question ≤200 enforced in Zod schemas (.max()), Decap CMS (pattern regex), and Vitest (mirrored schemas). |
| 32 | **AI content review workflow** | `GEMINI_API_KEY` secret in GitHub repo | GitHub Action that invokes Gemini 2.0 Flash on PR content changes. Checks tone, language, and content against `docs/content-style-guide.md`. Posts PR comments with severity levels (critical/major/minor). Advisory only — does not block merge. Supersedes F2. |
| 33 | **Migrate legacy content from vvgn.eu** | Editor available to review migrated posts | Migrate 73 full-text posts from the old VVGN site (scraped in Task #4, inventory at `data/scrapes/vvgn/content-manager-post-inventory.csv`, dossier at `docs/vvgn-content-manager-dossier.md`). Migrate Greek originals only (64 posts) — Dutch and English versions auto-generated by the translate workflow. Map to new schema: cultural activities → events (`cultural`), courses/classes → events (`class`), workshops → events (`workshop`), community updates → news, announcements → news. Create via `/admin` or bulk script. Editor should review each post for relevance — not all 2017–2024 content needs to carry over. |

---

## UX-Driven Redesign (from `docs/UX_report.pdf`)

> These tasks implement the findings from the user survey. They are grouped into three phases with strict ordering: Phase A (schemas & information architecture) must complete before Phase C (page sections), because building UI on the old IA would cause rework. Phase B (navigation & content) can partially run in parallel with Phase A.

### Phase A — Schemas & Information Architecture (do first)

| # | Task | Priority | Prerequisite | Details |
|---|------|----------|-------------|---------|
| 23 | ~~**Add `category` tag to events schema**~~ | ~~HIGH~~ | ~~None~~ | Done. Added `category` enum (workshop/social/cultural/class/meetup/other) to events Zod schema and CMS config. Client-side category filter on events listing page. |
| 24 | ~~**Create `activities` content collection**~~ | ~~HIGH~~ | ~~None~~ | Done. CMS-managed collection replacing hardcoded teams. 6 activities migrated (3 languages × 6 = 18 files). Detail pages at `/[lang]/activities/[slug]`. |
| 25 | ~~**Add `price` and `registrationRequired` fields to events schema**~~ | ~~MEDIUM~~ | ~~None~~ | Done. Optional `price` (string) and `registrationRequired` (boolean) fields added to events schema, CMS config, and displayed on listing/detail pages. |
| 26 | ~~**Make FAQ a CMS-managed collection**~~ | ~~MEDIUM~~ | ~~None~~ | Done. `faq` collection with `question`, `answer`, `order`, `lang`. 6 original + 7 new Q&As = 13 per language (39 total files). Editors can manage via `/admin`. |
| 27 | ~~**Create "Useful Information" resource collection & page**~~ | ~~MEDIUM~~ | ~~None~~ | Done. `resources` collection with category grouping. Page at `/[lang]/resources`. Seeded with 1 example per language. |

### Phase B — Navigation & Content (can partially parallel Phase A)

| # | Task | Priority | Prerequisite | Details |
|---|------|----------|-------------|---------|
| 28 | ~~**Rename "Teams" → "Activities" and reorder navigation**~~ | ~~HIGH~~ | ~~Task #24~~ | Done. Nav reordered to: Home → Events → Activities → News → About → Resources → Contact (7 items). "Teams" renamed to "Activities" in all 3 languages. History moved to footer. |
| 29 | ~~**Expand FAQ content with UX report questions**~~ | ~~HIGH~~ | ~~Task #26~~ | Done. FAQ expanded from 6 to 13 Q&As per language. Added: annual fees, volunteering, joining mid-program, membership for events, visiting hours, membership types, updates beyond social media. |
| 30 | ~~**Fill placeholder links and content**~~ | ~~HIGH~~ | ~~Stakeholder input~~ | Partially done. Social links (Facebook, Instagram), email, Google Maps filled. **Still placeholder:** Google Form embed URL, phone number, physical address, become-a-member CTA link. |
| 31 | ~~**Replace mobile `<details>` menu with Starwind Sheet**~~ | ~~MEDIUM~~ | ~~Task #28~~ | Done. Slide-out drawer with overlay, focus trapping, ESC close, accessible close button. |

### Phase C — Page Sections (replaces old Task #19)

| # | Task | Priority | Prerequisite | Details |
|---|------|----------|-------------|---------|
| 19 | ~~**Build page sections with Starwind components**~~ | ~~HIGH~~ | ~~Phase A + #28~~ | Done. Selective integration: Accordion (FAQ — keyboard nav, ARIA, animations), Avatar (About — board member initials), Button (Events — filter focus states), Sheet (Header — mobile menu). Set `--radius: 0` globally. Skipped Card/Badge/Pagination where override burden > benefit. See `docs/design-system.md` for rationale. |

---

## Future / Optional Enhancements

> Features evaluated and deferred. Not blocked by prerequisites — deferred by design until there's evidence of need. Each includes a trigger condition for when to revisit.

| # | Feature | Trigger to revisit | Design notes |
|---|---------|-------------------|--------------|
| F1 | **AI Translation (Gemini 2.5 Flash)** | DeepL translations feel robotic, Markdown structure breaks frequently, or DeepL free tier (500K chars/mo) is exhausted | Replace DeepL as the primary translation backend. Use the same workflow architecture (GitHub Action, PR-based). AI models handle Markdown frontmatter more reliably via system prompts. Keep DeepL as a fallback. Requires a `GEMINI_API_KEY` secret. Supersedes Task #9. |
| F2 | ~~**AI-Assisted Content Alignment (opt-in)**~~ | ~~Superseded~~ | Replaced by Task #32 (AI Content Review). The opt-in approach was too passive — always-on PR comments with severity levels is more practical. |
| F3 | **AI Image Content QA (vision model)** | Editors frequently upload off-brand or inappropriate images, or the site adopts strict visual templates | Invoke a cheap vision model (e.g. Gemini 2.0 Flash) to check uploaded images against allowed content templates and brand guidelines. Runs as a CI step on PRs that modify `public/images/`. Would block merge if the image fails content policy checks. Deferred because editors are trusted org members with GitHub 2FA — the threat model doesn't currently justify this. |
| F4 | **Social media feed integration** | Manual double-posting becomes a burden for editors | API integration pulling recent Instagram/Facebook posts into a "Latest News" or "Social" feed on the site. Reduces manual effort. Consider Instagram Basic Display API or Facebook Graph API. |
| F5 | **Full-text search (Pagefind)** | Site content grows beyond ~50 pages, or users report difficulty finding content despite category filters | Add [Pagefind](https://pagefind.app/) — a static search library that indexes at build time. Zero runtime cost, works with Astro. Lightweight alternative to Algolia/ElasticSearch for static sites. |

---

*Last updated: Apr 14, 2026 (Phase A/B/C complete — tasks #19, #23–29, #31 done; #30 partially done)*
