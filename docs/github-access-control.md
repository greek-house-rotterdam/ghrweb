# GitHub Access Control — Greek House in Rotterdam

> How permissions work in the `greek-house-rotterdam` GitHub Organization.

---

## Permission Systems

GitHub has several **independent** permission systems. Each controls a different resource type.

### Repository Access

How members access code. The **highest permission wins** across all sources.

| Layer | What it controls | Scope | Current setting |
|-------|-----------------|-------|-----------------|
| **Organization role** | Org-level powers (billing, settings, teams) — not repo access directly | Per member | Owner or Member |
| **Base permissions** | Default repo access for all members | All repos | **Read** |
| **Team permissions** | Repo access granted to team members | Per team, per repo | admins → Maintain, editors → Write |

```
Effective repo access = MAX(base permission, team permission, individual permission)
```

Owners bypass this entirely — they always have full access to every repo.

**Minimum 2 Owners required** to prevent lockout.

#### Team Permissions (per repo)

The primary access control mechanism. Each team gets a specific access level on each repo.

| Team | Repo access | What they can do |
|------|-------------|-----------------|
| **admins** | Maintain | Push to `main` (via bypass), merge PRs, manage repo settings |
| **editors** | Write | Create branches, open PRs — changes require admin approval (via ruleset) |
| **translators** | Write | Review auto-translated content — required via CODEOWNERS on `src/content/` |

Note: Infrastructure changes (`.github/`, configs, `src/layouts/`, `src/pages/`, `package.json`) require review from `@PanoEvJ` via CODEOWNERS. This protects the site's engine from accidental changes by editors.

### GitHub Projects Access

Controls access to GitHub Projects (kanban boards, task tracking) — **completely separate** from repository access.

| Layer | Current setting |
|-------|-----------------|
| **Projects base permissions** | **Read** |

Not used in GHR. Set to Read as a safe default — has no effect on repo access or Decap CMS.

### Member Privilege Restrictions

Org-wide toggles that limit what members can do structurally, regardless of their repo role. Set in **Settings → Member privileges**.

| Setting | Current value | Effect |
|---------|--------------|--------|
| Repository creation (private) | **Disabled** | Members cannot create private repos — Owners only |
| Repository visibility change | **Disabled** | Members cannot change public/private — Owners only |
| Repository deletion/transfer | **Disabled** | Members cannot delete or transfer repos — Owners only |
| Team creation | **Disabled** | Members cannot create teams — Owners only |
| OAuth/GitHub App requests | **Members only** | Only org members can request app access (Owners approve) |

---

## Current Setup

### Organization

- **Name:** `greek-house-rotterdam`
- **Plan:** Free
- **Repo visibility:** Public (enables branch protection, unlimited Actions minutes, $0 cost)

### Teams

| Team | Purpose | Repo access level |
|------|---------|-------------------|
| **admins** | Board of Directors, developer | Maintain |
| **editors** | Cultural team, content writers | Write |
| **translators** | Admins who speak the relevant languages | Write |

### Members

| Person | Org role | Team | Effective repo access |
|--------|----------|------|-----------------------|
| PanoEvJ | Owner | admins | Full (Owner) |
| t.a.klouvas | Owner | admins | Full (Owner) |
| jschistos | Member | editors | Write |
| aretizoi | Member | editors | Write |

### Ruleset on `main` (`main-protected`)

Repository-level ruleset — replaces classic branch protection.

- **Bypass actors:** Organization admin + admins team (Always allow)
- **Require pull request before merging** — 1 approval, dismiss stale approvals, require conversation resolution
- **Require status checks to pass** — `translate` (and `verify`), `Cloudflare Pages`
- **Require review from Code Owners** — `CODEOWNERS` file requires `translators` team review on `src/content/` changes
- **Allowed merge method:** Squash only — keeps history clean, simplifies the merge button for non-technical users
- **Require linear history** — enforces squash-only at the Git level
- **Restrict deletions** — prevents branch deletion
- **Block force pushes** — except bypass actors

This enforces the editorial workflow: editors create content via Decap CMS → PR is opened → translation workflow runs → translators review → admin merges → site deploys

### 2FA

Required for all organization members.

---

## Key Implications

- **Editors** can create and edit content freely via Decap CMS, but nothing goes live until an admin approves
- **Translators** must approve any PR that touches content files (auto-requested via CODEOWNERS)
- **Admins** can bypass the ruleset — push directly to `main` and merge PRs
- **Owners** can do everything, including destructive actions (delete repo, remove members, change billing)
- If both Owners lose access, the organization and all its repos are unrecoverable
