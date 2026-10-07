---
name: content-pipeline
description: |
  Programmatically add or update content for the Greek House Rotterdam website (`src/content/{news,activities,faq,resources,event-translations}`), and open a PR that the auto-translation pipeline picks up. Use this skill whenever the user wants to ingest content from any source — Greek/Dutch/English text pasted into chat, files in `docs/archive/` (`.docx`, `.txt`, `.md`, scanned docs), bulk-import a list of activities, add an event translation by Ticket Tailor ID, copy historical material, fix a typo in an existing article, or update a description — and have it land on the site in all three languages. Trigger even when the user doesn't explicitly say "skill" or "pipeline": phrases like "add this as a news post", "let's get this into FAQ", "draft an activity for X", "translate this article", "import the contents of that docx", "update the welcome post", or "publish this" should all invoke it. Don't try to write to `src/content/` by hand or open a translation PR without this skill — there are non-obvious rules (no `source_hash` on source files, 100/200 char limits, image path conventions, Ticket Tailor coupling for event-translations) that the skill enforces end-to-end.
---

# Content pipeline — ingest, write, review, PR

Take raw content from anywhere (chat-pasted text, `.docx`, `.txt`, `.md`, images on disk), put it into the right collection under `src/content/`, make sure it'll pass the automated checks, and open a PR that the translation workflow will pick up automatically.

## The pipeline you are plugging into

```
You write: src/content/{collection}/gr/<slug>.md          (source — no source_hash)
           [+ public/images/<image>.jpg, if applicable]
                          ↓
PR opens on main, without the `decap-cms/draft` label
                          ↓
.github/workflows/translate.yml runs:
  - generates src/content/{collection}/nl/<slug>.md  (with source_hash)
  - generates src/content/{collection}/en/<slug>.md  (with source_hash)
  - commits back to the PR branch
                          ↓
.github/workflows/content-review.yml posts advisory comments
.github/workflows/image-qa.yml validates/optimizes any new images
                          ↓
CODEOWNERS (translators team / @PanoEvJ) approval → merge → Cloudflare deploys
```

You are only writing the **source** file (typically Greek, but Dutch or English work too). Everything else happens automatically once the PR opens without the draft label.

## Hard rules (these break things if you miss them)

1. **No `decap-cms/draft` label on the PR.** The workflows no longer check labels (they run on every push), but with the label Decap lists the post as a Draft. Default `gh pr create` doesn't apply labels, so just don't pass `--label decap-cms/draft`.
2. **Source files must not have `source_hash` in frontmatter.** Files with `source_hash` are treated as translations and skipped by `translate.py`. You're writing the source, so omit it.
3. **Title ≤ 100, description ≤ 200, FAQ question ≤ 200 characters.** Enforced by Zod schema and Decap CMS validation pattern. Truncate or rewrite before saving, not after.
4. **Image path is `/images/<name>.<ext>`** in frontmatter. The file itself goes to `public/images/<name>.<ext>`. Keep filenames URL-safe (ASCII kebab-case is safest, though Greek/Cyrillic names do work).
5. **Filename is the slug, and must be identical across the three language folders.** `verify_content.py` fails the build if `news/gr/foo.md` exists but `news/en/foo.md` doesn't. The translation workflow keeps these in sync by reusing the source filename, so name the file once correctly and don't rename later.
6. **`event-translations` are keyed by `tt_event_id`.** The filename and the `tt_event_id` field must match a real published event in Ticket Tailor — otherwise the translation has nothing to attach to on the events page. Treat unknown IDs as a blocker, not a guess.
7. **Don't include `translation_locked: true` unless the user explicitly asks** for a hand-crafted translation that should never be overwritten. The field defaults to absent; setting it makes the file immune to future re-translation.

## Workflow

### 1. Ingest

Identify what the user has given you:

| Input form | How to read it |
|---|---|
| Text pasted into chat | Use directly. |
| `.md` file | `Read` tool. Strip any existing frontmatter — you'll rebuild it. |
| `.txt` file | `Read` tool. |
| `.docx` file | `uv run python3 .claude/skills/content-pipeline/scripts/extract_docx.py <path>` — emits markdown (preserves headings/lists/tables). One-time setup: `uv sync --extra skills`. |
| Image (`.jpg`/`.png`) | `Read` the file (Claude is multimodal). Get a caption/alt-text from looking at it. |
| `.pdf` | Use the `Read` tool with `pages: "1-N"`. |
| A folder (e.g. `docs/archive/<thing>/`) | List it, then ingest each file. Group images with the text they belong to. |

Greek House content is most often Greek source. If the source language isn't obvious, ask the user once. Save the source under the language folder it's actually written in (`gr`/`nl`/`en`); the workflow will translate the other two.

### 2. Classify (which collection?)

Pick the most specific match:

- **`news`** — dated announcements, recaps, "we're happy to announce…", new initiatives. Requires `date`.
- **`activities`** — recurring or standing programs (language classes, dance group, cooking workshops). Has `schedule` and `order` fields; no `date`.
- **`event-translations`** — a translation overlay for a single Ticket Tailor event (the event itself comes from the TT API; this only translates title/description/body). Requires `tt_event_id`.
- **`faq`** — a single question with a single answer. Title-less; uses `question`/`answer` instead, body is hidden.
- **`resources`** — durable "useful information" pages (registering with the gemeente, healthcare, etc.). Has a `category` from a fixed list.

When uncertain between news and activities, ask: "is this a one-time event/announcement or a recurring program?" One-time → news. Recurring → activities.

Read `references/collections.md` for the exact frontmatter shape and validation rules for whichever collection you're writing.

### 3. Write (or update) the source file

**Filename** — kebab-case slug derived from the title. ASCII preferred. For `event-translations`, the filename is the `tt_event_id` (e.g. `ev_8112397.md`).

**Path** — `src/content/<collection>/<source-lang>/<slug>.md`.

**Frontmatter** — build it according to `references/collections.md`. Required fields are non-negotiable; optional fields should be included when the user gave you the information.

**Body** — clean markdown. Headings, lists, links, emphasis are all fine. Keep paragraphs short. If you ingested from a `.docx`, sanitize the output: strip Word artifacts, fix smart-quote inconsistencies, collapse multiple blank lines.

**Images** — if the user supplied images and they're relevant:

1. Copy/move the image into `public/images/<kebab-name>.<ext>` (preserve extension; `image-qa.yml` will optimize it).
2. Set `image: /images/<kebab-name>.<ext>` in frontmatter (collections that support `image`: news, activities).
3. Include the image inline in the body only if it adds value beyond the hero image — most don't need it.

**Updating existing content** — if the user is editing an existing post:

- Find the source file (the one without `source_hash`) by grepping `src/content/<collection>/<lang>/`.
- Edit it in place. Do **not** touch the translated counterparts; the workflow will regenerate them because the source hash changes.
- Exception: if the user explicitly wants to *only* change the English (or Dutch) version without affecting the Greek source, edit that language's file and add `translation_locked: true` to its frontmatter so the next source change won't overwrite it.

### 4. Review your own work

Before opening a PR, run the validator and read what you wrote:

```bash
python3 .claude/skills/content-pipeline/scripts/validate_content.py <path-to-new-or-changed-files>

# When you only expect source files (no source_hash anywhere), add --strict:
python3 .claude/skills/content-pipeline/scripts/validate_content.py --strict src/content/news/gr/my-new-post.md
```

It checks: frontmatter parses, required fields present, title/description lengths, `source_hash` is absent on source files, image referenced in frontmatter exists at `public/images/...`, `tt_event_id` filename match. Fix anything it flags.

Then do a quick read pass:

- Does the title actually describe what's in the body?
- Is the description a real one-sentence summary, not just the title repeated?
- Does the body match the [content style guide](../../docs/content-style-guide.md) (warm/welcoming, no political content, no commercial promotion, factual)?
- For events: are date/time/location actually in the body, not buried at the end?
- Are line breaks and lists rendering correctly (no stray `\n`, no Word smart quotes that look bad in monospace)?

If anything is off, fix it before pushing. This is a soft self-review — the `content-review.yml` workflow does a more thorough automated review with Gemini once the PR opens.

### 5. Push and open the PR

Read `references/pr-workflow.md` for the exact git commands. The short version:

```bash
# Branch from main with a descriptive name
git checkout -b content/<collection>-<slug>

# Stage only what changed under src/content/ and public/images/
git add src/content/<collection>/<lang>/<slug>.md
git add public/images/<image-files-if-any>

# Commit — short conventional-commit prefix
git commit -m "content(<collection>): <short description>"

# Push and open the PR — no labels, base=main
git push -u origin HEAD
gh pr create \
  --base main \
  --title "content(<collection>): <short description>" \
  --body "$(cat <<'EOF'
## Summary
- <what was added/changed and why>

## Test plan
- [ ] Translation workflow opens auto-commit on this PR
- [ ] Preview deploy renders all three languages
- [ ] CODEOWNERS approval received
EOF
)"
```

Don't pass `--label decap-cms/draft` (it no longer blocks the workflows, but Decap would list the post as a Draft). Do not pass `--draft` either (that's a separate GitHub-native concept and won't block our workflows — but the user's reviewers expect non-draft PRs unless told otherwise; ask if unsure).

After opening, report the PR URL to the user and tell them what happens next:

> Opened PR #N. The translation workflow will push translated `nl` and `en` files within a few minutes. After CODEOWNERS approval, merge → Cloudflare deploys.

## What you don't need to do

- **Don't pre-translate.** The Gemini-backed workflow handles `nl` and `en` from the source. Pre-translating creates inconsistencies and gets overwritten.
- **Don't write `source_hash` yourself.** Only `translate.py` writes that field.
- **Don't optimize images.** `image-qa.yml` does that on the PR.
- **Don't write a stylistic review.** `content-review.yml` does that on the PR.

## Don't push content changes directly to `main`

The translation, image-QA, and content-review workflows trigger on `pull_request` events only. A direct push to `main` (even one that touches `src/content/`) skips all of them. That means:

- The Greek source updates, but `nl/<file>.md` and `en/<file>.md` stay on the old translation. Source-hash mismatches sit there silently until the next PR happens to touch the file.
- Editors who land on `/nl/...` or `/en/...` see stale content.
- `verify_content.py` still passes (all three language folders exist), so there's no automated alarm.

This has happened in practice (commit `1037c8b` added two images to `founding.md` directly on main and the translations went stale). The recovery is to open a tiny "no-op" PR that re-saves the source file, which re-triggers `translate.yml` and refreshes the translations.

**Always go through a PR, even for one-line content edits.**

## Reference index

- `references/collections.md` — frontmatter shapes, required fields, length limits, slug rules per collection.
- `references/ingestion.md` — handling `.docx`, image batches, dirty Word exports, bulk imports from `docs/archive/`.
- `references/pr-workflow.md` — exact git/gh commands, branch naming, what to put in the PR body, how to handle a pre-existing branch.
- `scripts/extract_docx.py` — stdlib-only `.docx` → text/markdown.
- `scripts/validate_content.py` — pre-PR linter that runs the full set of hard rules.
