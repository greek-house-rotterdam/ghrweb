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
| 7 | **Set up DeepL / translation GitHub Action** | Translation API decision finalized (currently pending) | Create workflow in `.github/workflows/` that triggers on content changes in `src/content/` |
| 8 | **Connect custom domain** | Domain DNS access available | Cloudflare Pages → Custom domains → Add domain → Update DNS records |

---

*Last updated: Feb 15, 2026*
