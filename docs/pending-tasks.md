# Pending Tasks — Greek House in Rotterdam

> Tasks that are defined but cannot be completed yet. Each has a clear trigger or prerequisite.

---

## GitHub Organization Setup

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 1 | **Enforce 2FA** for all org members | Members must enable 2FA on their personal GitHub accounts first | Org Settings → Authentication security → Require 2FA. Anyone without 2FA will be removed from the org. Inform members before enabling. |
| 2 | **Elevate t.a.klouvas to Owner** | t.a.klouvas must accept the org invitation | People → find user → Change role → Owner. Currently invited as Owner but invitation is pending. |
| 3 | **Assign members to teams** | All 3 invitees must accept their invitations | Add t.a.klouvas to **admins** team. Add jschistos and aretizoi to **editors** team. (Teams → team name → Add a member) |

## Content & Launch

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 5 | **Connect Cloudflare Pages** to org repo | Repo transfer complete (done) | Cloudflare dashboard → Pages → Create project → Connect `greek-house-rotterdam/ghrweb` |
| 6 | **Configure Decap CMS OAuth** | Cloudflare Pages connected, GitHub OAuth app created | Decap CMS needs a GitHub OAuth app registered under the org for admin login at `/admin` |
| 7 | ~~**Set up DeepL / translation GitHub Action**~~ | ~~Translation API decision finalized~~ | Done. Workflow at `.github/workflows/translate.yml`, script at `.github/scripts/translate.py`. Requires `DEEPL_API_KEY` secret in GitHub repo settings. |
| 9 | **Evaluate OpenAI for translation** | Content volume or complexity increases | Consider switching from DeepL to OpenAI API if translations feel "robotic" or if Markdown structure (frontmatter) is frequently broken. OpenAI offers better contextual control and structural integrity via system prompts. |
| 8 | **Connect custom domain** | Domain DNS access available | Cloudflare Pages → Custom domains → Add domain → Update DNS records |

## Security Hardening

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 10 | **Audit org-level security settings** | Org fully operational (all members joined, 2FA enforced) | Review what's not yet configured beyond current setup: rulesets, tag protection, Actions permissions, secret scanning, Dependabot alerts, deploy key policies. Free-tier limits apply — focus on what's available and meaningful. |
| 11 | **Add CODEOWNERS with mandatory review for infrastructure paths** | Repo structure stabilized | Create a `CODEOWNERS` file requiring PanoEvJ approval for non-content paths: `.github/`, `src/layouts/`, `src/pages/`, `astro.config.*`, `tailwind.config.*`, `package.json`. Content paths (`src/content/`) remain unblocked so editors can self-serve via Decap CMS. |

## Testing

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 12 | **Add site tests** | Core site structure and build pipeline working | Build smoke test (Astro compiles without errors), content schema validation (frontmatter structure), internal link checking, and basic integration tests (pages render expected content). Use Astro-compatible tooling (Vitest or similar). Keep lightweight — the site is static, not a SaaS app. |

## Developer Tooling

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 13 | **Add Cursor AI skills for the project stack** | Active development begins | Find or create Cursor skills (`.cursor/skills/`) for: Astro (priority — primary framework, beginner frontend level), Tailwind CSS, GitHub Actions, Python scripting, and Decap CMS patterns. Better skills = more accurate AI assistance for this specific stack. (e.g. [here](https://github.com/SpillwaveSolutions/publishing-astro-websites-agentic-skill)) |

## Infrastructure & Limits

| # | Task | Prerequisite | Details |
|---|------|-------------|---------|
| 14 | **Investigate traffic spike capacity** | Site is live on Cloudflare Pages | Research Cloudflare Pages free tier limits (bandwidth, requests/day, concurrent connections). Determine failure mode during a viral event (e.g. major news): does it throttle, bill overages, or shut down? Document the "safe" traffic ceiling. |

---

*Last updated: Feb 17, 2026*
