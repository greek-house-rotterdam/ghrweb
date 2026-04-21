# Workflows — Greek House in Rotterdam

> How content moves from draft to live on the GHR website.

---

## Overview

All content changes go through pull requests (PRs). Nothing reaches the live website without admin approval. Translations are generated automatically within the PR, and a preview of the full website is built for review.

```
Draft (save) → In Review (workflows run) → Approved → Publish (merge) → Live
```

---

## Decap CMS Editorial Statuses

Decap CMS uses three statuses to track content through the editorial pipeline. All three map to a single GitHub PR — the statuses are managed via **PR labels**, not separate PRs.

| CMS status | What the editor sees | What happens on GitHub | Workflows run? |
|---|---|---|---|
| **Draft** | "Saved" — content is stored but not ready | PR is created with `decap-cms/draft` label | **No** — workflows skip draft PRs |
| **In Review** | "Ready for review" — editor is done writing | Label changes to `decap-cms/pending_review` | **Yes** — translate, content review, image QA |
| **Ready** / **Publish** | "Approved, merge it" | PR is merged into `main` | Cloudflare deploys to production |

**Why drafts don't trigger workflows:** Decap CMS has no server-side storage — every "save" writes to a Git branch and opens a PR, even for drafts. Without draft gating, saving an unfinished post would immediately trigger translation and AI review, wasting API calls on incomplete content. All content workflows check for the `decap-cms/draft` label and skip if present.

**How it works technically:** Each workflow triggers on `pull_request` events of type `opened`, `synchronize`, and `labeled`. Each job has a condition:

```yaml
if: "!contains(github.event.pull_request.labels.*.name, 'decap-cms/draft')"
```

When the editor moves content from Draft to In Review, Decap CMS removes the `decap-cms/draft` label and adds `decap-cms/pending_review`. This fires a `labeled` event, the job condition passes (no draft label), and workflows run.

### GitHub event types explained

| Event type | When it fires | Example |
|---|---|---|
| `opened` | PR is first created | Editor saves a draft → PR created |
| `synchronize` | New commits are pushed to an existing PR | Editor edits content, or translation bot commits |
| `labeled` | A label is added to the PR | Editor moves status from Draft to In Review |

---

## Editor Workflow (via Decap CMS)

For non-technical team members who write content through the admin panel.

```
1. Visit yoursite.com/admin → Log in with GitHub

2. Write or edit a post in the visual editor

3. Click "Save" → status: Draft
     ↓
   Decap CMS creates a PR with the decap-cms/draft label
   Cloudflare builds a deploy preview (preview URL on the PR)
   ⏸ No other workflows run yet — content is still a draft
     ↓
4. Editor continues editing (optional — can save multiple times)
     ↓
5. Editor sets status to "In Review" when ready
     ↓
   Label changes → workflows trigger:
     - Image QA validates and optimizes images
     - Translation workflow translates to the other two languages
     - AI content review posts advisory comments
     ↓
6. Translators team is auto-requested for review (via CODEOWNERS)
     ⛔ PR is BLOCKED — cannot be merged until a CODEOWNER approves
     ↓
7. Reviewer opens the preview link → reviews the rendered website
     ↓
8. Reviewer approves the PR (CODEOWNER approval satisfies the merge gate)
     ↓
9. Admin clicks "Publish" (or merges the PR on GitHub)
     ↓
10. Cloudflare deploys to production → content is live
```

**Key points:**
- Editors never see Git, terminals, or raw files
- Saving a draft does NOT trigger translation or review — only moving to "In Review" does
- Translations appear automatically — no manual translation step
- After auto-translation, reviewers can edit individual languages without triggering retranslation (see [Manual Translation Edits](#manual-translation-edits-source-hash-protection))
- The reviewer checks the actual rendered website, not Markdown
- **The PR is blocked until a CODEOWNER approves** — this is enforced by the repository ruleset, not just convention

---

## Developer Workflow (via Git)

For the developer making code or content changes locally.

```
1. Create a branch and make changes locally

2. Push the branch and open a PR to main
     ↓
3. If the PR contains content files (src/content/**/*.md):
     - Translation workflow runs and adds translations
     - Translators team is requested for review (CODEOWNERS)
     ⛔ PR blocked until translators approve
   If the PR contains infrastructure files (.github/, src/pages/, configs):
     - Developer (@PanoEvJ) is requested for review (CODEOWNERS)
     ⛔ PR blocked until developer approves
     ↓
4. Cloudflare builds a deploy preview
     ↓
5. Reviewer approves → Admin merges the PR
     ↓
6. Cloudflare deploys to production
```

---

## Legacy Content Ingestion (One-Time)

For migration from the legacy VVGN site into this repo.

1. Run `scripts/scrape_vvgn.py` (start URL: `https://vvgn.eu/nl/`)
2. Review output in `data/scrapes/vvgn/`:
   - `records/` (per-page JSON)
   - `manifest.json` and `crawl-report.md` (coverage and failures)
   - `content-manager-post-inventory.csv` (spreadsheet-friendly post inventory)
3. Use `docs/vvgn-content-manager-dossier.md` as the non-technical handoff to content managers
4. Migrate content into `src/content/` after editorial review

Note: many Dutch post URLs are placeholders that point to Greek/English content. Prioritize full-text posts first during migration.

---

## Translation Workflow (GitHub Action)

**Trigger:** PR targeting `main` with changes in `src/content/**/*.md`, **only when the PR is not a draft** (no `decap-cms/draft` label). Fires on PR open, new commits, or label change (Draft → In Review).

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
- Deletion sync: `.github/scripts/sync_deletions.py`
- Integrity check: `.github/scripts/verify_content.py`
- DeepL API key: stored as `DEEPL_API_KEY` in repository secrets

### Manual Translation Edits (source hash protection)

After auto-translation, reviewers and editors can safely edit translations in individual languages without those edits being overwritten on the next workflow run.

**How it works:** Every translated file receives a `source_hash` field in its frontmatter — a fingerprint of the source content it was translated from. On subsequent runs, the script compares this hash against the current source. If the source hasn't changed, the translation is skipped, preserving any manual edits.

```
1. Editor creates Greek post        → workflow translates to NL + EN (with source_hash)
2. Reviewer fixes a word in NL      → pushes to the PR
3. Workflow re-runs (synchronize)    → sees source_hash unchanged → skips NL (edit preserved)
4. Editor later updates the Greek    → source_hash changes → NL is retranslated (expected)
```

**The `source_hash` field also prevents cascade translation.** When the workflow picks up a translated file (e.g. the Dutch version) as a changed file, it detects `source_hash` in the frontmatter and skips it — only original source files (which lack `source_hash`) trigger translation.

### Locking a Translation (`translation_locked`)

For cases where a translation should **never** be overwritten by auto-translation — even when the source changes — editors can add `translation_locked: true` to a translated file's frontmatter:

```yaml
---
title: "Handmatig vertaalde titel"
description: "Deze vertaling is handmatig geschreven"
lang: nl
source_hash: abc123def456
translation_locked: true
---
```

The workflow will skip this file unconditionally. Use this for hand-crafted translations that should be maintained independently of the source.

**When to use `translation_locked`:**
- A professional translator has provided a high-quality translation that shouldn't be overwritten
- The translated version has been intentionally adapted (not just translated) for the target audience
- The source language version changes frequently but the translation should remain stable

**When NOT to use it:**
- For routine wording fixes — `source_hash` handles this automatically without locking
- On source files — `translation_locked` is only meaningful on translated files (those with `source_hash`)

### "Manually translated" badge

Locked translations display a **"Manually translated"** badge on their detail page (news, events, activities). The badge appears in the metadata row alongside date, location, and category badges.

**When the badge appears:**
- The content file has `translation_locked: true` in its frontmatter
- This means someone has explicitly marked this translation as hand-maintained

**When the badge does NOT appear:**
- **Source files** (e.g. the Greek original) — they are not translations, so there is nothing to flag
- **Auto-translated files** — even though they have `source_hash`, they were machine-generated and don't need a visual indicator
- **Manually edited translations without `translation_locked`** — these edits are silently protected by `source_hash` (the workflow skips retranslation as long as the source is unchanged). No badge is shown because the edit is considered a minor correction, not a permanent override. If the source is later updated, these files will be retranslated normally.
- **Listing pages and cards** — the badge only appears on detail pages to avoid visual clutter in card grids

The badge is translated: "Χειροκίνητη μετάφραση" (GR), "Handmatig vertaald" (NL), "Manually translated" (EN).

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

## Image QA Workflow *(Planned)*

**Trigger:** PR opened or updated, targeting `main`, with changes in `public/images/`

**What it does:**

1. Scans all new/changed image files in the PR
2. Validates each image against quality rules:
   - File size ≤2 MB (hard block at >5 MB)
   - Resolution between 800×600 and 4096×4096
   - Allowed formats: JPEG, PNG, WebP
3. Auto-optimizes where possible:
   - Resizes oversized images to max dimensions
   - Compresses to target file size
   - Converts to WebP for optimal web performance
4. Commits optimized images to the PR branch
5. Fails the check (blocks merge) only for hard limit violations that can't be auto-fixed

**Design principle:** Prefer auto-fixing over blocking. Non-technical editors shouldn't have to manually resize images.

**Dependencies:** Pillow (Python). No AI model needed — this is pure metadata validation.

**Ordering:** Runs before the translation workflow so bad assets are caught early.

---

## Content Review Workflow (GitHub Action)

**Trigger:** PR targeting `main` with changes in `src/content/**/*.md`, **only when the PR is not a draft** (no `decap-cms/draft` label).

**What it does:**

1. Detects content files changed in the PR
2. Sends each file to Gemini 2.0 Flash for review against the content style guide (`docs/content-style-guide.md`)
3. Posts PR comments with findings, grouped by severity (critical, major, minor)

**Advisory only — does not block merge.** The review is informational. Editors and reviewers decide whether to act on the findings.

**Only reviews human-authored changes.** The workflow uses event-aware diffing to avoid reviewing auto-translated content:

| Event | What gets reviewed | Why |
|-------|--------------------|-----|
| `opened` | All content files in the PR vs `main` | Initial review of all new/changed content |
| `synchronize` | Only files changed in the latest push | Avoids re-reviewing auto-translations and previously reviewed content |

This means:
- When an editor creates a Greek post and opens a PR → the Greek post is reviewed
- When the translation bot pushes NL + EN translations → no new review (bot uses `GITHUB_TOKEN`, which does not trigger workflows)
- When a reviewer later edits the English translation → only the English file is reviewed

**Files involved:**
- Workflow: `.github/workflows/content-review.yml`
- Review script: `.github/scripts/content_review.py`
- Style guide: `docs/content-style-guide.md`
- Gemini API key: stored as `GEMINI_API_KEY` in repository secrets

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

### Merge Gates

A PR targeting `main` **cannot be merged** until all of the following pass:

| Gate | Type | What it checks |
|------|------|----------------|
| **CODEOWNER approval** | Human review | The designated CODEOWNER for the changed files must approve the PR. This is enforced by the repository ruleset ("Require review from Code Owners"). Without their approval, the merge button is disabled. |
| **Cloudflare Pages build** | Automated | The site must build successfully. This is the only required status check — it runs on every PR regardless of which files changed. |
| **At least 1 approval** | Human review | The ruleset requires a minimum of 1 PR approval. CODEOWNER approval satisfies this. |

**Other workflow checks** (`test-node`, `test-python`, `translate`, `verify`, `image-qa`, `content-review`) are **not required** in the ruleset. They still run and report results on the PR, but do not block merging. This is intentional — each workflow uses path filters and only triggers on relevant PRs. Making them required would permanently block PRs that don't match their path filters, because a check that never runs never reports a status. See `docs/github-access-control.md` for the full rationale.

### Who Must Approve

The `CODEOWNERS` file determines who **must** approve based on which files are changed:

| Files changed | Required approver | PR is blocked until... |
|---------------|-------------------|------------------------|
| `src/content/` | `@greek-house-rotterdam/translators` | A member of the translators team approves |
| `.github/`, configs, `src/layouts/`, `src/pages/`, `package.json` | `@PanoEvJ` (developer) | The developer approves |

This means:
- **Content PRs** — translators team is auto-requested. The PR **cannot be merged** until a translator approves. Editors can freely create content without bothering the developer.
- **Infrastructure PRs** — developer is auto-requested. The PR **cannot be merged** until the developer approves. Editors cannot accidentally break the site's engine, deployment pipeline, or dependencies.
- **Mixed PRs** (content + infrastructure) — both approvals are required.

### What to Review

**Content PRs (translators):**
- Open the Cloudflare deploy preview link
- Check the content reads well in all three languages
- Check that images and formatting look correct
- Approve the PR (this unblocks the merge)

**Infrastructure PRs (developer):**
- Check the code changes are safe and correct
- Verify the preview site still works
- Approve the PR (this unblocks the merge)

**Who merges:** Any member of the `admins` team (bypass actors on the ruleset) can merge after all gates pass.

---

## Local Development

Two ways to run the site locally:

| Command | Runtime | When to use |
|---------|---------|-------------|
| `npm run dev` | Node.js (via Astro) | Day-to-day development. Fast, hot-reload. |
| `npx wrangler dev` | Cloudflare workerd | Testing deployment behavior. Simulates Cloudflare's edge runtime. |

For a static site, both behave identically. Wrangler only matters if you add server-side logic (SSR, API routes on Workers).

---

## Direct Deploy (via Wrangler CLI)

You can deploy directly from your local terminal without going through GitHub/CI.

**Setup (one-time):**

```
npx wrangler login
```

This opens a browser window to authenticate with your Cloudflare account and stores an API token locally.

**Deploy:**

```
npm run build && npx wrangler deploy
```

**When to use:**
- Emergency fix that needs to go live immediately
- Debugging a deployment issue that only reproduces on Cloudflare
- Deploying before the GitHub CI pipeline is fully set up

**When NOT to use:**
- Normal workflow — always go through PRs so translations run and reviews happen
- The next GitHub-triggered deploy will overwrite whatever you deployed manually

---

## Summary

| Step | Who | What happens | Blocks merge? |
|------|-----|-------------|---------------|
| Create content | Editor or Admin | Write in Decap CMS or locally | — |
| PR opened | Decap CMS or developer | Automatic (editorial workflow) or manual | — |
| Image QA | GitHub Action | Validates and auto-optimizes images | No — informational |
| Translation | GitHub Action | Detects changes, translates, commits | No — informational |
| Tests | GitHub Action | Runs Node + Python test suites (code PRs only) | No — informational |
| Content Review | GitHub Action | AI review of human-authored content only | No — advisory comments only |
| Preview | Cloudflare Pages | Builds and links preview URL | **Yes — required status check** |
| CODEOWNER review | Translators / Developer | Auto-requested based on changed files | **Yes — PR cannot merge without CODEOWNER approval** |
| Merge | Admin | Squash and merge (after all gates pass) | — |
| Deploy | Cloudflare Pages | Deploys to production (~30 seconds) | — |

---

_Last updated: April 2026 (added draft gating — workflows skip Decap CMS drafts, only run when editor moves to "In Review")_
