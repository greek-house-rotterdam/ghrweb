# Developer guide

What the developer does, and what to do when the site asks for help. The editors' side is in [editor-guide.md](editor-guide.md) (in Greek). Accepted gaps are in [known-limitations.md](known-limitations.md).

**Keep this current:** when a pull request changes how editors or the developer work, update this guide and the editor guide in the same pull request.

---

## How a change reaches the site

```
editor saves in /admin ─► pull request (cms/<collection>/<slug>)
                           ├─ translate.yml: deletions, translations, image shrinking, verify,
                           │                 content tests, tidy (deletes the bot's held runs),
                           │                 preview (waits for Cloudflare's build, posts the link)
                           ├─ content-review.yml: advisory AI review
                           └─ Cloudflare: preview build (required check "Workers Builds: ghrweb")
editor sets Ready ─► auto-publish.yml turns on auto-merge ─► merged ─► Cloudflare deploys main
```

- Required checks on `main` (ruleset `main-protected`): `translate`, `verify`, `Workers Builds: ghrweb`.
- Content pull requests need no approval. Code pull requests need the developer's approval (decision D6, CODEOWNERS).
- Every pull request gets one status comment. Failures mention `ADMIN_MENTIONS` (repository variable, default `@PanoEvJ`).
- **Never commit content straight to `main`.** No workflow runs on a direct push: no translations, no checks. Deleting a published entry in Decap does exactly that, which is why `/admin` has no Delete button (see "Removing content" below).

## Content

### Importing or writing content in bulk

Use the `content-pipeline` skill (`.claude/skills/content-pipeline/`). Greek source files only. One pull request per page or topic. The pull request is merged by hand: auto-publish only reacts to Decap's Ready label.

### Page texts in code (`src/i18n/ui.ts`)

Decision D9: the home welcome, the About mission, the membership categories and **fees**, the activities intro, and the footer line stay in code.

- Change all three languages by hand; the bot doesn't translate `ui.ts`.
- The fees appear **only** on the Become a member page. Content entries (the FAQ) point there; keep it that way.
- The Greek House's opening hours are in three places: the Contact page (`contact.hours.*`), the FAQ entry `faq/gr/opening-hours.md`, and the Μπιζ Μπιζέ activity `activities/gr/biz-bize.md` (its `schedule` and its text). Change all three together.
- The mission's first paragraph is in two places: the About page's mission box (`about.mission.text`, three languages by hand) and the start of `about-sections/gr/mission-vision.md` (mission, vision, values; translated by the bot). Change both together.
- Use the glossary names (below).

### The translation glossary

`docs/tone-and-voice-guidelines.md` → "Terminology / Glossary" is read by the bot on every translation. Add names there before they spread. English: "Association of Greeks in the Netherlands", "Greek House in Rotterdam", "cultural group". Dutch: "Vereniging van Grieken in Nederland" (VvGiN), "Het Griekse Huis".

If an existing translation uses an off-glossary name and the Greek didn't change, the bot won't redo it. Correct the file and recompute its `translation_hash` with `translate.compute_source_hash` (see #96), or delete the translation file in a pull request, and the bot writes it again.

### A translation the bot keeps or flags

- Hand-corrected translations (text ≠ `translation_hash`) are kept when the Greek changes, and flagged in the status comment.
- Editors correct a **draft's** translation through the "Correct the English / Correct the Dutch" links in the status comment (#131). They open GitHub's editor on that file in the pull request's branch; the editor commits straight to the branch, and the correction counts as a hand correction like any other. `pr_status.py` builds the links (`edit_paths`, `render_edit_links`) from the content files that differ from `main`, once their Dutch and English files exist on the branch. Editor guide, section 5.
- To hand one back to the bot: delete that one file in a pull request (rewritten right away), or remove `translation_hash` (rewritten at the next Greek change).
- To freeze one: `translation_locked: true`.

## Removing content

| Goal | How | Result |
|---|---|---|
| Take a post off the site (editors) | «Απόκρυψη από τον ιστότοπο» on the Greek entry → Ready | Hidden in all 3 languages; reversible. Pages read through `getVisible()` (`src/lib/visible.ts`). |
| Discard a never-published draft | "Delete changes" on its Workflow card | Pull request closed; nothing on the site. |
| Delete a post's files | Pull request deleting the **Greek** file | `sync_deletions.py` removes its translations (#98). |
| Have one translation rewritten | Pull request deleting that **Dutch or English** file | Greek stays; the bot writes the translation again. |
| Erase text for good (personal data) | Rewrite git history (below) | Gone from the repository. |

Hiding is not erasing: the repository is **public**, and hidden or deleted text stays readable in files and history.

### Erasing something from the history

Only for real need (personal data, a secret). It rewrites `main` for everyone.

1. Hide the post first (immediate), so it leaves the site.
2. If it's a secret (key, token), **rotate it**: erasing doesn't make it safe again.
3. Rewrite with `git filter-repo` (e.g. `--path <file> --invert-paths`, or `--replace-text`), then force-push `main`. This needs the ruleset to allow it temporarily.
4. Ask GitHub Support to purge cached views of the old commits and pull requests if needed. Forks and clones keep their copies.
5. Tell editors to reload `/admin`.

### Rolling back the November 2026 content reset

Everything before the reset is at commit `40a3d54`, tag `before-drive-content` (on GitHub). `docs/content-reset.md` lists every removed entry and the `git checkout 40a3d54 -- <files>` command to restore one, through a pull request.

## When an alert arrives

### Issue "The live site is not updating"

From `nightly-rebuild.yml` (03:17 UTC). A production build didn't go live within 20 minutes. Usually the Ticket Tailor key: Cloudflare → ghrweb → Settings → Build → Variables and secrets → `TT_API_KEY`. Production builds stop on purpose when Ticket Tailor fails, so the live site stays as it was. The issue closes itself after a good nightly run.

### Issue "The content tests failed"

From the `content-tests` job (#95). A test that reads the real content failed on a pull request. It doesn't block publishing. Usually a test expects today's values: make it check the content's shape instead. Close the issue when fixed.

### "Workflows awaiting approval" on a pull request

Should no longer appear: the `tidy` job deletes the bot's own held runs within about 2 minutes (#94). If one remains, ignore or delete it. Never approve runs from forks.

### A pull request's `verify` fails with "has no Greek source"

A Dutch or English file exists without its Greek file, usually after something was deleted straight on `main` (as in #99/#100). Remove the leftover translations in a pull request.

## Events (Ticket Tailor)

- Loaded at build time (`src/lib/ticket-tailor.ts`). Ticket Tailor webhooks call the Cloudflare deploy hook (secret `CF_DEPLOY_HOOK_URL`), and the nightly rebuild is the safety net.
- Lists: upcoming events soonest first, then past events most recent first, judged at build time (`src/lib/event-list.ts`). The home page shows the 3 soonest.
- Test events must stay unpublished in Ticket Tailor; published ones appear on the site.
- Event translations (`event-translations`) are keyed by the Ticket Tailor ID (`ev_…`).

## Code rules that protect editors

- Pages and components read `news`, `activities`, `resources` and `faq` through `getVisible()`, never `getCollection()` (a test enforces it).
- The header and footer link News only while there is a post in that language (`hasNews()` in `src/lib/visible.ts`; `visible.test.ts` enforces it). Menu order and footer columns were agreed with the managers on 2026-11-17: no "Home" item on desktop (the logo leads home), FAQ in the top menu, white header, blue footer. (A gold header was tried the same day; the managers preferred white, and the yellow logo also disappeared on gold.)
- The home page hero shows the association's logo (`vvgn-logo.png`) and "The cultural group of the Association of Greeks in the Netherlands" (`home.hero.union`), linking to About. The managers asked for it so the link between the Greek House and the association stays visible. The badge is transparent around its ring text, so it sits on a white disc.
- Tests that read real content check its shape, never its current values (#88, #90 broke such tests).
- `ui.ts` changes need all three languages.
- **Raised = clickable, flat = read (#122).** Only links and buttons have the hard offset shadow and press in. `<BrutCard href=…>` is a link card; without `href` it is static: `variant="rule"` (default, cards in grids) or `variant="slab"` (one framed, tinted box with a thick left bar). Never wrap a card in your own `<a>`. `cards.test.ts` enforces this.
- Every label, hint and validation message in `/admin` is Greek, then ` / `, then English (`admin.test.ts` checks it). Decap's own buttons stay in English: its Greek translation is poor ("Saving…" becomes «Εξοικονόμηση…») and the editor guide names the English buttons.
- The membership page has no application form, on purpose (#115): the managers send the form to people who get in touch. `membership.test.ts` fails if a Google Form link appears in the code or the site settings. Ask the managers before changing this.
- Keep `/admin` without Delete and Publish buttons (`delete: false`, `publish: false`; tests enforce both). Your account may skip the ruleset, so either button would bypass the translations and checks. Publish with Ready, like editors; in an emergency, merge on GitHub.
- The Workflow card badges come from `public/admin/workflow-badges.js` (tests in `src/__tests__/workflow-badges.test.ts`). The "AI review" badge (#135) reads the review section of the PR's status comment, the base64url JSON in `<!-- pr-status:begin review … -->`. If you change that section's format in `pr_status.py`, update `reviewSummary()` too. The AI review stays advice only: a critical finding mentions the admins but doesn't block publishing.
- `/admin` starts Decap by hand (`window.CMS_MANUAL_INIT`), after `public/admin/open-own-language.js` patches the GitHub backend. Without it, reopening a translated draft opens the English file, because Decap opens the alphabetically first `.md` file on the branch (#126). The patch depends on Decap internals: after any Decap upgrade, reopen a translated draft and check that the Greek shows.

## Planned work: GitHub issues

The backlog is the open [GitHub issues](https://github.com/greek-house-rotterdam/ghrweb/issues) labelled `enhancement`.

- Open an issue for each agreed feature or follow-up: what, why, and "done when".
- A pull request that finishes an issue says `Closes #N` in its body, so merging it closes the issue. One that does part of the work says `Part of #N`.
- Close an issue you decide not to do, or a settled decision, with a comment giving the reason. Don't delete issues.
- The repository is public: no secrets, account details or personal data in issues.

The alert issues opened by workflows ("The live site is not updating", "The content tests failed") are not backlog; see [When an alert arrives](#when-an-alert-arrives).

## Secrets and settings

| Where | Name | What |
|---|---|---|
| GitHub secret | `GEMINI_API_KEY` | Translation and AI review |
| GitHub secret | `CF_DEPLOY_HOOK_URL` | Nightly rebuild |
| GitHub variable | `ADMIN_MENTIONS` | Who failures mention |
| Cloudflare build variable | `TT_API_KEY` | Ticket Tailor events (production and preview) |
| Repository settings | Allow auto-merge; approval for all outside contributors | Auto-publish; forks stay blocked |
