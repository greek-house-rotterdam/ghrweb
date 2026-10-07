# Known Limitations

Limitations of the publishing pipeline (Decap CMS → pull request → GitHub Actions → Cloudflare) that we know about and accept for now. Each entry says what happens, what to do about it, and whether it has been seen in practice.

Update this file when a limitation is fixed or a new one is found.

_Last updated: 2026-10-07_

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

### Pushing straight to `main` skips every check

All workflows run on pull requests only. Content pushed straight to `main` isn't translated and its translations go stale, with no alarm. To recover, open a small PR that saves the source file again.

## Not yet verified in CI

- **A real Gemini failure.** The failure notices were tested on PR #45, but never triggered by an actual API error.
- **Cancelling a superseded run.** When an editor saves twice quickly, the older run should be cancelled. In the live test (PR #46) the bot finished before the second save, so this didn't happen.
