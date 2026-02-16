# Website Access Protocol — Greek House in Rotterdam

> Who can do what on the GHR website.

---

## Members & Roles

| Name | Role |
|------|------|
| PanoEvJ | Owner + Admin |
| t.a.klouvas | Owner + Admin |
| jschistos | Editor |
| aretizoi | Editor |

---

## Before You Start — Prerequisites

To join the website team you need to complete these steps **before** an Owner can grant you access:

1. **Create a free GitHub account** at [github.com/signup](https://github.com/signup)
   - Use a personal email you control long-term (this is your login to the admin panel)
   - Pick a username — share it with an Owner so they can send you an invitation

2. **Enable two-factor authentication (2FA)** on your GitHub account
   - Go to [github.com/settings/security](https://github.com/settings/security) → enable 2FA
   - Use an authenticator app (e.g. Google Authenticator, Authy) — SMS is less secure
   - 2FA is **mandatory** — the organization enforces it. You will be removed automatically if you disable it

3. **Accept the organization invitation**
   - Once an Owner adds you, you'll receive an email invitation from GitHub
   - Click "Join" to become a member of the `greek-house-rotterdam` organization

After these three steps, you'll have access to the admin panel at `yoursite.com/admin` using the "Login with GitHub" button.

---

## What Each Role Can Do

### Editors

- Create new content (articles, events, pages) through the admin panel (`/admin`)
- Edit existing content
- **Cannot publish directly** — all changes go into a review queue for an Admin to approve

> Think of it as: _you write the draft, an Admin hits "publish."_

### Admins

Everything Editors can do, **plus:**

- Review and approve content submitted by Editors
- Publish approved content (makes it live on the website)
- Manage website settings and structure

### Owners

Everything Admins can do, **plus:**

- Add or remove members and change their roles
- Delete the website or the organization
- Full control over billing, security, and all organization settings

> There must always be **at least 2 Owners**. If both lose access, the organization and website are unrecoverable.

---

## How Content Gets Published

```
Editor writes/edits content in /admin  →  Clicks "Publish"
        ↓
  Decap CMS opens a review request (pull request)
        ↓
  Translations are generated automatically (GitHub Action + DeepL)
        ↓
  A preview of the website is built automatically (Cloudflare Pages)
        ↓
  Translators team is requested to review (automatic)
        ↓
  Admin reviews the preview website  →  Approves and merges
        ↓
  Content + translations go live on the website
```

Nothing goes live without Admin approval. The admin reviews a **rendered preview** of the website — not raw files. This protects the website from accidental or unreviewed changes, and ensures translations are checked before publishing.

---

## Security Rules

- **Two-factor authentication (2FA) is required** for all members — no exceptions.
- Only Owners can add/remove people or change organization settings.
- Editors cannot delete the website, change its visibility, or alter its structure.

---

## Quick Reference

| Action | Editor | Admin/Translator | Owner |
|--------|:------:|:----------------:|:-----:|
| Create/edit content | Yes | Yes | Yes |
| Review translations | No | Yes | Yes |
| Approve & publish content | No | Yes | Yes |
| Manage website settings | No | Yes | Yes |
| Add or remove members | No | No | Yes |
| Change organization settings | No | No | Yes |
| Delete the website | No | No | Yes |

---

_Last updated: February 2026_
