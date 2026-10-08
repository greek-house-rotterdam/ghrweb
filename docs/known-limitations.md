# Known Limitations

Limitations of the publishing pipeline (Decap CMS → pull request → GitHub Actions → Cloudflare) that we know about and accept for now. Each entry says what happens, what to do about it, and whether it has been seen in practice.

Update this file when a limitation is fixed or a new one is found.

_Last updated: 2026-10-08_

## Images

**How it works:** the Content Pipeline workflow (`.github/workflows/translate.yml`) handles images in `public/images/` that the PR adds or changes:

- The `translate` job shrinks images over 2560 px on either side or over 2 MB. They are resized to fit 2560×2560 and keep their filename and format, so links to them keep working.
- The `verify` job, a required check, blocks publishing for an image in a format other than JPEG, PNG or WebP, a file that can't be read as an image, or a file still over 5 MB after shrinking. The PR gets an "Image problem" notice listing the files.

### A replaced image may keep blocking publishing

If an editor uploads an image the site can't use (for example a HEIC file) and then picks a different image in Decap, the first file probably stays on the PR branch. The check looks at every image the PR adds, so it keeps failing and the notice stays.

- **What to do:** the admin deletes the file from the PR branch: on GitHub, open the PR's branch, find the file under `public/images/`, and delete it. The notice tells the editor the admin will help if the message doesn't go away.
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

### A fixed translation is replaced when the Greek changes

When an editor changes the Greek text of an entry, its Dutch and English versions are translated again, and any fixes made to them by hand are lost. This also applies to the original hand-written Dutch and English of the older activities, FAQs, resources and news posts.

- **What to do:** to keep a hand-written translation for good, tick "Lock translation" on it (news, events, activities and resources), or ask the admin to add `translation_locked: true`. A locked translation is no longer updated when the Greek changes.
- **Possible fix:** detect hand edits and flag them instead of overwriting (A9 in the plan).

### Changing only the image, date or order doesn't reach Dutch and English

Each language has its own file. Translation only runs when the Greek *text* changes, so a new image, date or display order on the Greek entry alone leaves the Dutch and English pages as they were.

- **What to do:** make the same change in the Dutch and English entries, or change some Greek text in the same save.
- **Possible fix:** copy these fields from the Greek on every run (A3 in the plan).

## Checks and notices

### A failure after the bot's commit shows as "waiting", not as a red ✗

The `translate` job pushes the translations (and shrunk images) as a bot commit, which becomes the PR head. If the `verify` job then fails, that commit never gets its `translate`/`verify` statuses. GitHub shows "Expected — Waiting for status to be reported" instead of a red ✗. Publishing is still blocked, and the PR notice says what failed. The failed run is attached to the editor's commit just before.

### Image problems aren't reported when the content check fails

In the `verify` job, "Check images" runs after "Verify content integrity". If the content check fails, image problems only show up on the next run, after the content is fixed.

### A crash in the image step shows the "Translation failed" notice

The `translate` job has a single failure notice. If "Optimize changed images" crashes (a bug, not a bad image), the notice says the translation failed. The run log shows the step that actually failed.

### The bot's commits create runs that wait for approval

First seen on 2026-10-07: GitHub creates Content Pipeline and Content Review runs for the bot's own pushes and holds them as "action_required" (awaiting approval). They aren't needed and don't block publishing. Don't approve them: they would only check the bot's commit again, which has no new content.

### Translations aren't reviewed separately

Content Review only reviews the files in the editor's own commits. The bot's commit gets the same result carried over ("translations not separately reviewed"), so the AI never reviews the generated Dutch and English text.

### Local CMS works in file mode only

`package.json` pins `simple-git` to 4.x through `overrides`, because 3.x has security advisories with no 3.x fix. `decap-server` (even 3.11.3) still expects simple-git 3, and its **git mode** (`MODE=git npx decap-server`) crashes on start with "`(0, l.default) is not a function`". The default **file mode**, which `npm run dev:cms` uses, works: local edits are written straight to `src/content/`.

- **What to do:** use `npm run dev:cms` as documented. Drop the pin once `decap-server` supports simple-git 4.
- **Status:** both modes tested on 2026-10-07.

### Pushing straight to `main` skips every check

All workflows run on pull requests only. Content pushed straight to `main` isn't translated and its translations go stale, with no alarm. To recover, open a small PR that saves the source file again.

## Not yet verified in CI

- **A real Gemini failure.** The failure notices were tested on PR #45, but never triggered by an actual API error.
- **Cancelling a superseded run.** When an editor saves twice quickly, the older run should be cancelled. In the live test (PR #46) the bot finished before the second save, so this didn't happen.
