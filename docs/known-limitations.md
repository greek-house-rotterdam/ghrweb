# Known Limitations

Limitations of the publishing pipeline (Decap CMS → pull request → GitHub Actions → Cloudflare) that we know about and accept for now. Each entry says what happens, what to do about it, and whether it has been seen in practice.

Update this file when a limitation is fixed or a new one is found.

_Last updated: 2026-10-10_

## Images

**How it works:** the Content Pipeline workflow (`.github/workflows/translate.yml`) handles images in `public/images/` that the PR adds or changes:

- The `translate` job shrinks images over 2560 px on either side or over 2 MB. They are resized to fit 2560×2560 and keep their filename and format, so links to them keep working.
- The `verify` job, a required check, blocks publishing for an image in a format other than JPEG, PNG or WebP, a file that can't be read as an image, or a file still over 5 MB after shrinking. The PR's status comment lists the files in its Images section.

### A replaced image may keep blocking publishing

If an editor uploads an image the site can't use (for example a HEIC file) and then picks a different image in Decap, the first file probably stays on the PR branch. The check looks at every image the PR adds, so it keeps failing and the notice stays.

- **What to do:** the admin deletes the file from the PR branch: on GitHub, open the PR's branch, find the file under `public/images/`, and delete it. The status comment tells the editor the admin will help if the message doesn't go away.
- **Status:** not tested. We don't know yet whether deleting the file in Decap's media library removes it from the PR branch.

### Large PNG photos may stay over 5 MB

PNG files are only compressed losslessly, because the format is kept. A photo saved as PNG can still be over 5 MB after resizing to 2560 px, and then it blocks publishing.

- **What to do:** save photos as JPEG. PNG is fine for graphics, logos and screenshots.

### Photos that don't need shrinking keep their EXIF data, including GPS location

Re-encoding drops EXIF metadata, so shrunk photos lose it. Photos that are already within 2560 px and 2 MB are committed exactly as uploaded, including any GPS location the phone recorded.

- **What to do:** nothing automatic yet. Editors can turn off location for the photo on their phone before uploading. A possible fix is to strip metadata from every uploaded JPEG.

### Animated images aren't shrunk

Animated WebP and PNG files are skipped by the shrinking step, because re-saving would keep only the first frame. They are still checked, so one over 5 MB blocks publishing.

### Only images the PR adds or changes are checked

Images already on `main` are not checked again. To check all of them locally, run `python .github/scripts/image_qa.py` from the repo root (with the dependencies in `pyproject.toml` installed).

## Translations

Editors write every entry in Greek; `/admin` only offers new entries in the Greek collections. Dutch and English are generated from the Greek, and editors can still open them to fix a translation.

### A kept translation may be out of date, and the flag only shows on GitHub

When the bot writes a translation it also stores `translation_hash`, a fingerprint of the text it wrote. If an editor later corrects the Dutch or English by hand, the text no longer matches it. When the Greek then changes, that translation is **kept**, not re-translated: its text stays, its `source_hash` is brought up to date, and the PR's status comment lists the file under Translation (the job log has a `Kept a hand-corrected translation` warning). The list mentions nobody and is not cleared by later runs; kept files from several runs are collected in it. Shared fields (image, date, order, ...) are still synced.

- **Limitation:** a kept translation may no longer match the new Greek until someone updates it by hand in `/admin`. It stays "hand-edited", so the next Greek change keeps it again and flags it again. Nothing re-translates it unless the admin removes `translation_hash` from the file (or deletes the file), which hands it back to automatic translation.
- **Limitation:** the flag shows only on the PR on GitHub, which editors may not read. The notice is Greek and English, but there is no sign in `/admin`.
- **Files without `translation_hash`** (unknown history, or the field was removed) are re-translated when the Greek changes, so a fix to such a file is lost. The existing Dutch and English files were given a `translation_hash` from their content at the time A9 was added, so a fix made after that is detected.
- **Locked files** (`translation_locked: true`, added by the admin; there is no checkbox in the CMS) are never re-translated, with or without a hash, and are not flagged.
- **Edge case:** if a run is cancelled by a newer save after the bot pushed but before the list was recorded, it can be missing, because the next run sees the current `source_hash` and does not flag the file again. It is recorded before the push to keep this window small.

### The job fails on a Dutch or English source file

Entries are written in Greek. If a PR changes a Dutch or English file that has no `source_hash`, it looks like a source, and the "translate" job fails with a message naming the file: create the entry in the Greek collection instead. A file like that with `translation_locked: true` is a hand-written translation and is skipped. The status comment says why in plain Greek and English and shows the message from the job log.

### A hand-written Dutch or English file without `source_hash` stops the job

On every run the Greek entry's image, date, order and other non-text fields are copied to its Dutch and English files, locked or not. The lock only protects the translated text. The text itself is translated again only when the Greek text changes.

A Dutch or English file that has no `source_hash` and no `translation_locked: true` counts as hand-written. Instead of overwriting it, the "translate" job fails with a message naming the file. The status comment shows "Translation did not finish" with the reason.

- **What to do:** the admin reads the message in the status comment, then either adds `translation_locked: true` to the file to keep it as it is, or deletes the file (or adds the `source_hash` from the message) to have it generated again from the Greek.

## Checks and notices

### A failure after the bot's commit shows as "waiting", not as a red ✗

The `translate` job pushes the translations (and shrunk images) as a bot commit, which becomes the PR head. If the `verify` job then fails, that commit never gets its `translate`/`verify` statuses. GitHub shows "Expected — Waiting for status to be reported" instead of a red ✗. Publishing is still blocked, and the PR's status comment says what failed. The failed run is attached to the editor's commit just before.

### A crash in the image step shows as "Translation did not finish"

The status comment has no separate message for a crash in "Optimize changed images" (a bug, not a bad image): it shows "Translation did not finish: a technical problem came up". The run log shows the step that actually failed.

### The bot's commits create runs that wait for approval

First seen on 2026-10-07: GitHub creates Content Pipeline and Content Review runs for the bot's own pushes and holds them as "action_required" (awaiting approval). They aren't needed and don't block publishing. Don't approve them: they would only check the bot's commit again, which has no new content.

### Translations aren't reviewed separately

Content Review only reviews the files in the editor's own commits. The bot's commit gets the same result carried over ("translations not separately reviewed"), so the AI never reviews the generated Dutch and English text.

### The PR status comment

Each content PR has one status comment (`.github/scripts/pr_status.py`) with Translation, Images, Preview, AI review and a next step. PRs that change no content and no images get none.

- **Edits don't notify.** GitHub's docs don't say whether an @mention added by editing a comment notifies, so the pipeline never relies on it. When a failure appears that the admins haven't been told about, the comment is re-created (new one first, then the old one deleted) with a `cc @admins` line: a new comment notifies the mentioned admins and emails the PR author. While the failure persists, later updates edit the comment in place and don't notify again. If the failure goes away and comes back, it notifies again. The comment's link changes when this happens.
- **A rare lost update is possible.** Parallel jobs read the comment, change their own section, write it back, wait two seconds, re-read and retry (up to 5 times) if their section is gone. A writer whose read is older than that window can still overwrite another job's section without noticing. The affected section is rewritten by that job's next run; the Preview section is rewritten by the next Cloudflare comment edit.
- **The Preview section needs the Preview Status workflow, which runs from `main`.** A change to `preview-status.yml` only takes effect after it is merged. Until Cloudflare's comment shows a finished build for the PR's latest commit, the section says "building". If Cloudflare's comment format changes or the build fails, it stays that way, and "Next step" keeps saying to wait; the Workers Builds check shows the failure.
- **The comment is not essential.** A failure to update it only logs a warning; it never fails a check. In that case it can be missing or out of date.
- **AI review notes can go stale** for a file that was reviewed in an earlier commit: each note shows the short commit it refers to.

### Local CMS works in file mode only

`package.json` pins `simple-git` to 4.x through `overrides`, because 3.x has security advisories with no 3.x fix. `decap-server` (even 3.11.3) still expects simple-git 3, and its **git mode** (`MODE=git npx decap-server`) crashes on start with "`(0, l.default) is not a function`". The default **file mode**, which `npm run dev:cms` uses, works: local edits are written straight to `src/content/`.

- **What to do:** use `npm run dev:cms` as documented. Drop the pin once `decap-server` supports simple-git 4.
- **Status:** both modes tested on 2026-10-07.

### Pushing straight to `main` skips every check

All workflows run on pull requests only. Content pushed straight to `main` isn't translated and its translations go stale, with no alarm. To recover, open a small PR that saves the source file again.

## Not yet verified in CI

- **A real Gemini failure.** The failure notices were tested on PR #45, but never triggered by an actual API error.
- **Cancelling a superseded run.** When an editor saves twice quickly, the older run should be cancelled. In the live test (PR #46) the bot finished before the second save, so this didn't happen.
