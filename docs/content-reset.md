# Content reset to the approved Drive content (2026-11-15)

In November 2026 the Greek House managers reviewed the old content and gave us the content that should be on the site. It is in their shared Google Drive folder «Content ιστοσελίδας», downloaded locally to `docs/archive/content_webpage/` (not in git). Everything else in `src/content/` was removed or rewritten to match it.

## How to get removed content back

Everything removed is still in git history.

- **The commit before the reset:** `40a3d54279ad562068bc5f2fcabf2be58b3f61b7` (main, "fix(ui): small buttons sink into their shadow on hover…", #89).
- **A local tag on that commit:** `before-drive-content` (`git tag before-drive-content 40a3d54`). It exists only on the developer's laptop unless someone pushes it.

To restore one entry, in all three languages, on a new branch:

```bash
git checkout 40a3d54 -- src/content/news/gr/welcome.md src/content/news/nl/welcome.md src/content/news/en/welcome.md
```

Then open a pull request as usual. To see an old file without restoring it: `git show 40a3d54:src/content/news/gr/welcome.md`.

## What was removed, and why

Each entry was removed in Greek, Dutch and English.

| Entry | Why |
|---|---|
| `news/welcome` | Written during setup ("the new website is live"); not in the Drive. |
| `news/easter-2026` | A translation test post; not in the Drive. |
| `news/website-rollout` | A CMS test post; not in the Drive. |
| `activities/community-gatherings`, `dance-group`, `youth` | Placeholders written during setup; not in the Drive's activities list. |
| `resources/municipality-registration` | A one-line placeholder; not in the Drive. |
| `faq/01` to `faq/13` | Answers written during setup, some wrong (nationality, fees). Replaced by the Drive's questions. |
| `history-milestones/1969`, `1992`, `1994`, `2022` | No source in the Drive. The school entry is now `1965` ("1965-1971"), as the Drive's text says. |
| `history-sections/today` | The Drive's «Η Ένωση σήμερα» section is empty. |

## What was added or changed

- **Activities:** the 11 activities from the Drive's overview, word for word, with 6 photos from its folder. Kept file names: `cooking`, `art-workshop`, `dutch-classes`. Left out: «gyrokinisis (?)» and the «Open House» paragraph, which are marked unfinished in the Drive.
- **Useful information:** `resources/greek-consulate`, from «Πότε, πώς και γιατί απευθυνόμαστε στο Ελληνικό Προξενείο».
- **FAQ:** 7 of the Drive's 11 questions, answered only with facts from the Drive (membership PDF, activities overview, cultural group text) or about this website. The other 4 wait for the managers.
- **History and About:** already based on the same Drive texts. Removed sentences the Drive doesn't have, restored the Drive's wording in a few places, and added the 1780 view of Amsterdam embedded in the Drive's history document.
