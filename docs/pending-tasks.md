# Pending Tasks — Greek House in Rotterdam

> Tasks that are defined but cannot be completed yet. Each has a clear trigger or prerequisite.

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
| 6 | **Configure Decap CMS OAuth** | Cloudflare connected (done) | **Code ready** — Worker OAuth proxy at `src/oauth.ts`, wrangler configured, admin UI dynamically sets `base_url`. **Remaining manual steps:** 1) Register GitHub OAuth App under the org (callback URL: `https://<site-url>/callback`). 2) Set Worker secrets: `npx wrangler secret put GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`. 3) Deploy and test `/admin` login. |
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
| 12 | **Add site-level tests** | Core site structure and build pipeline working | Build smoke test (Astro compiles without errors), content schema validation (frontmatter matches Zod schemas), internal link checking. Keep lightweight. |
| 17 | **Unit test i18n utilities** | Utility logic is stable and non-trivial enough to warrant tests | Test `getLangFromSlug`, `getStaticLangPaths` (from `src/i18n/utils.ts`) and `t()` (from `src/i18n/ui.ts`). Good first candidates: pure functions with clear inputs/outputs. |

## UI Components & Design

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 18 | **Install Starwind UI and add core interactive components** | None — ready now | `npx starwind-ui init` then `npx starwind-ui add accordion card badge button sheet pagination avatar`. These are needed for FAQ, news/event cards, mobile nav drawer, and listing pages. |
| 19 | **Build page sections using HyperUI patterns** | Task #18 complete (Starwind provides the interactive primitives) | Copy-paste and adapt Tailwind HTML from HyperUI for: hero section (Home), timeline (History), team cards (Teams), CTA blocks (Home, Become a Member), footer layout, contact section. Color tokens from Task #20 are now available (`primary-*`, `accent-*`) — use them instead of raw Tailwind palette colors. |
| 20 | ~~**Define color palette and visual identity tokens**~~ | ~~None — ready now~~ | Done. Defined semantic color tokens in `src/styles/global.css` using Tailwind CSS v4 `@theme`. Primary: Hellenic Blue (`#0D5EAF`, from Greek flag). Accent: Mediterranean Gold (`#FACC15`). Each has dark/light/lighter variants. All 15 `.astro` files updated from hardcoded `blue-*`/`yellow-*` classes to semantic `primary-*`/`accent-*` tokens. Neutrals (gray scale) kept as standard Tailwind. Added `.vscode/settings.json` with `css.lint.unknownAtRules: "ignore"` to suppress false-positive linter warnings on `@theme`. |

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
| 22 | **Content character limits** | Astro content collections defined (Zod schemas) | Enforce character limits: title ≤100 chars, description ≤200 chars, body ≤5000 chars (news) / ≤2000 chars (events). Enforce in three layers: Decap CMS `pattern` on string widgets, Zod `.max()` in Astro content collection schemas, and a CI validation step. |

---

## Future / Optional Enhancements

> Features evaluated and deferred. Not blocked by prerequisites — deferred by design until there's evidence of need. Each includes a trigger condition for when to revisit.

| # | Feature | Trigger to revisit | Design notes |
|---|---------|-------------------|--------------|
| F1 | **AI Translation (Gemini 2.5 Flash)** | DeepL translations feel robotic, Markdown structure breaks frequently, or DeepL free tier (500K chars/mo) is exhausted | Replace DeepL as the primary translation backend. Use the same workflow architecture (GitHub Action, PR-based). AI models handle Markdown frontmatter more reliably via system prompts. Keep DeepL as a fallback. Requires a `GEMINI_API_KEY` secret. Supersedes Task #9. |
| F2 | **AI-Assisted Content Alignment (opt-in)** | Editors request help with writing quality, or content tone/style becomes inconsistent | Add an `ai_assist` boolean checkbox to Decap CMS collections. When enabled, a GitHub Action step invokes an AI model (e.g. Gemini 2.5 Flash) with a standardized style guide prompt to suggest improvements to the source content before translation. The AI commits suggestions to the PR. Non-blocking — serves as a helper, not a gatekeeper. Runs before the translation step. Requires defining the style guide prompt and adding the CMS field. |
| F3 | **AI Image Content QA (vision model)** | Editors frequently upload off-brand or inappropriate images, or the site adopts strict visual templates | Invoke a cheap vision model (e.g. Gemini 2.0 Flash) to check uploaded images against allowed content templates and brand guidelines. Runs as a CI step on PRs that modify `public/images/`. Would block merge if the image fails content policy checks. Deferred because editors are trusted org members with GitHub 2FA — the threat model doesn't currently justify this. |

---

*Last updated: Mar 19, 2026 (Tasks #21–22 added, Future features F1–F3 defined)*
