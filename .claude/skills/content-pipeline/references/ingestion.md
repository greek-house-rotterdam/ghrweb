# Ingestion notes

How to get raw material into a clean, Astro-ready markdown body.

## `.docx` files (Word documents)

Use the bundled extractor — `python-docx` is not in the project's `pyproject.toml`, and `pandoc` is not guaranteed to be installed on the user's machine:

```bash
# First time on a fresh checkout:
uv sync --extra skills

# Then for each docx:
uv run python3 .claude/skills/content-pipeline/scripts/extract_docx.py path/to/file.docx
```

Output is plain text with paragraph breaks. After extraction:

1. **Detect language.** First paragraph usually tells you. If a doc is bilingual (Greek + Dutch side by side, as in `docs/archive/ποιοι_ειμαστε/`), split it: each language becomes its own source file, NOT a single bilingual file. Then the workflow generates the third language for each.
2. **Strip junk.** Word headers/footers, page numbers, "Page 1 of 4", revision marks.
3. **Reflow paragraphs.** Word exports often break mid-paragraph. Join lines that aren't separated by a real blank line.
4. **Fix typography.** Smart quotes (` ‘ ’ “ ” `) are fine and look better than ASCII straight quotes for prose. But fix obvious export glitches (double spaces, stray tabs).
5. **Promote headings.** Word's "Heading 1/2/3" styles are lost by the extractor. If the doc was clearly structured, re-add `## Heading` markers manually based on context.
6. **Lists.** Bullets render as `•` or `-` in plain text — replace with markdown `- ` (single dash + space).
7. **Embedded images** are not extracted by the script. They sit inside the `.docx`'s `word/media/` zip entry. If the user wants them, unzip the docx with `unzip -d /tmp/<name> file.docx` and grab from `word/media/`.

## Images

**Source-of-truth path:** `public/images/<kebab-name>.<ext>`

- Always rename to ASCII kebab-case before copying in. Unicode filenames technically work (a couple already exist), but they break cleanly in URLs and confuse some tooling.
- Don't resize or optimize — `.github/workflows/translate.yml` runs `image_qa.py` on the PR and handles that. Use JPEG, PNG or WebP; any other format blocks publishing.
- Frontmatter reference is `image: /images/<name>.<ext>` (note the leading slash and no `public/`).
- Per-collection support:
  - `news`, `activities`, `resources` (via Decap config) → `image` field accepted.
  - `faq`, `event-translations` → no image field. Don't add one.

If the user gave you a folder of images and one piece of text, pick the single most relevant image as the hero. Don't try to embed all of them — most posts look better with one strong header image.

## PDFs

For short PDFs (≤10 pages), use the `Read` tool directly with the file path. For longer PDFs, pass `pages: "1-N"` to read in chunks. PDFs from `docs/UX_report.pdf` etc. are reference material, not content to publish — confirm with the user before turning a PDF into a news post.

## Bulk imports (folder ingestion)

When the user points at a folder like `docs/archive/ποιοι_ειμαστε/`:

1. List the folder. Group files by topic (text + its accompanying images).
2. For each group, decide which collection it belongs to. Historical "who we are" material usually fits `news` (one post per topic) or a long-form `resources` entry if the user wants it on the about page — ask.
3. Process one item at a time. Don't try to batch the whole folder into one PR unless the user explicitly says so — smaller PRs are easier to review and roll back.

## When the material isn't in Greek

Greek is the only source language, so the source always goes under `gr/`.

Heuristics:
- Greek script (Ελ, Ολ, Σπ…) → use it as the source.
- Dutch / English: look for `ij`, `aa`, `oe`, `het/de/een/zijn` (Dutch) vs. `the/of/and/that` (English).
- Mixed → the Greek part is the source.

If there's no Greek, tell the user and offer to draft the Greek source from the material, for a Greek speaker to check. To keep a hand-written Dutch or English version word for word, put its text into the generated file after the bot has translated. Keep the file's `source_hash` (without it the file counts as a source) and add `translation_locked: true`.

## Length compliance

Title (≤100) and description (≤200) are *hard* limits. If the source material's headline is longer:

- For `title`: trim to the essential noun phrase. Move detail into the body.
- For `description`: write a fresh one-sentence summary. Don't truncate mid-word.

Don't translate-then-truncate — Gemini doesn't know about the limit and writing a 150-char Greek description that becomes a 220-char Dutch translation will fail validation downstream. Keep the source comfortably under the cap (say, 90/180) so translations have headroom.

## Style guide alignment

`docs/content-style-guide.md` is enforced by the AI review workflow. Common violations to avoid up front:

- Political statements or partisan content → critical violation.
- Commercial promotion / ad-style copy → major violation.
- Missing event details (date/time/location) → major violation.
- Overly formal / bureaucratic prose → minor, but fix it anyway.
- "Greek Association" instead of "Greek House" in English copy → minor.

Read the style guide for the full list before producing anything novel.
