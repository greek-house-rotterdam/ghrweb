# Workflows — Greek House in Rotterdam

> How content moves from draft to live on the GHR website.

---

## Overview

All content changes go through pull requests (PRs). Nothing reaches the live website without admin approval. Translations are generated automatically within the PR, and a preview of the full website is built for review.

```
Content created → PR opened → Translations added → Preview built → Review → Merge → Live
```

---

## Editor Workflow (via Decap CMS)

For non-technical team members who write content through the admin panel.

```
1. Visit yoursite.com/admin → Log in with GitHub

2. Write or edit a post in the visual editor

3. Click "Publish"
     ↓
   Decap CMS creates a PR automatically (editorial workflow)
     ↓
4. Translation workflow runs
     - Detects new/changed content files
     - Translates to the other two languages via DeepL
     - Commits translations to the same PR
     ↓
5. Cloudflare builds a deploy preview
     - Preview URL appears as a status check on the PR
     ↓
6. Translators team is auto-requested for review (via CODEOWNERS)
     ↓
7. Admin opens the preview link → reviews the rendered website
     ↓
8. Admin approves and merges the PR
     ↓
9. Cloudflare deploys to production → content is live
```

**Key points:**
- Editors never see Git, terminals, or raw files
- Translations appear automatically — no manual translation step
- The admin reviews the actual rendered website, not Markdown

---

## Developer Workflow (via Git)

For the developer making code or content changes locally.

```
1. Create a branch and make changes locally

2. Push the branch and open a PR to main
     ↓
3. If the PR contains content files (src/content/**/*.md):
     - Translation workflow runs and adds translations
     - Translators team is requested for review
     ↓
4. Cloudflare builds a deploy preview
     ↓
5. Review the preview → Merge the PR
     ↓
6. Cloudflare deploys to production
```

---

## Translation Workflow (GitHub Action)

**Trigger:** PR opened or updated, targeting `main`, with changes in `src/content/**/*.md`

**What it does:**

1. Checks out the PR branch
2. Compares the PR branch to `main` to find changed content files
3. For each new/changed file:
   - Detects the source language from the file path (e.g., `news/gr/` → Greek)
   - Translates the title, description, and body to the other two languages using DeepL API
   - Writes the translated files to the corresponding language directories
4. For each deleted file:
   - Removes the corresponding files in the other two language directories
5. Commits all changes to the PR branch

**Only changed files are translated.** Files that haven't changed in the PR are not touched. This prevents unnecessary API calls and avoids overwriting content that hasn't been modified.

**No infinite loops.** The workflow commits using `GITHUB_TOKEN`, which does not trigger new workflow runs (GitHub's built-in safety rule).

**Integrity Check:**
After translation, a second job `verify` runs to ensure that every content file exists in all three languages (`gr`, `nl`, `en`). If any file is missing (e.g. if translation failed), this check fails, blocking the PR.

**Files involved:**
- Workflow: `.github/workflows/translate.yml`
- Translation script: `.github/scripts/translate.py`
- DeepL API key: stored as `DEEPL_API_KEY` in repository secrets

---

## Deletion Sync

When content is deleted in a PR, the translation workflow removes the corresponding files in the other two languages. This prevents "ghost posts" — translations that outlive their source content.

```
Delete src/content/news/gr/old-post.md in a PR
  ↓
Workflow detects the deletion
  ↓
Removes src/content/news/nl/old-post.md
Removes src/content/news/en/old-post.md
  ↓
Commits deletions to the same PR
```

---

## Deploy Previews (Cloudflare Pages)

Cloudflare Pages automatically builds a preview for every PR. The preview URL appears as a commit status check on the PR in GitHub.

**How to use:**
1. Open the PR in GitHub
2. Scroll to the status checks at the bottom
3. Find the Cloudflare Pages check → click "Details"
4. Browse the preview site — it's a full working copy of the website with the PR's changes

The preview updates every time new commits are pushed to the PR (including when the translation workflow adds translations).

**Production deploys** happen automatically when a PR is merged to `main`.

---

## Review Process

The `CODEOWNERS` file determines who must approve based on which files are changed:

| Files changed | Required reviewer |
|---------------|-------------------|
| `src/content/` | `translators` team |
| `.github/`, configs, `src/layouts/`, `src/pages/`, `package.json` | `@PanoEvJ` (developer) |

This means:
- **Content PRs** — translators team is auto-requested. Editors can freely create content without bothering the developer.
- **Infrastructure PRs** — developer is auto-requested. Editors cannot accidentally break the site's engine, deployment pipeline, or dependencies.

The ruleset on `main` also requires at least 1 approval to merge.

**What to review (content PRs):**
- Open the Cloudflare deploy preview link
- Check the content reads well in all three languages
- Check that images and formatting look correct
- Approve the PR and merge

**What to review (infrastructure PRs):**
- Check the code changes are safe and correct
- Verify the preview site still works
- Approve the PR and merge

---

## Summary

| Step | Who | What happens |
|------|-----|-------------|
| Create content | Editor or Admin | Write in Decap CMS or locally |
| PR opened | Decap CMS or developer | Automatic (editorial workflow) or manual |
| Translation | GitHub Action | Automatic — detects changes, translates, commits |
| Preview | Cloudflare Pages | Automatic — builds and links preview URL |
| Review request | CODEOWNERS | Automatic — requests translators team |
| Review | Admin/Translator | Manual — check preview, approve |
| Merge | Admin | Manual — squash and merge |
| Deploy | Cloudflare Pages | Automatic — live in ~30 seconds |

---

_Last updated: February 2026_
