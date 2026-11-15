# Working in this repository

Read `README.md` and `docs/developer-guide.md` first.

## The backlog is GitHub issues

Planned features and later work are GitHub issues labelled `enhancement` (problems: `bug`). The open issues are the backlog: <https://github.com/greek-house-rotterdam/ghrweb/issues>.

- **New work agreed** (a feature, a follow-up, something to do later): open an issue with what, why and "done when". Search the open issues first, so you don't open a duplicate.
- **Starting an issue:** say which issue the work is for.
- **A pull request that finishes an issue** says `Closes #N` in its body. One that does part of it says `Part of #N`.
- **Scope or plan changes:** edit the issue's description, or comment on it.
- **Decided not to do it, or a decision issue is settled:** close it with a comment giving the reason (`gh issue close N --reason "not planned"` or `--reason completed`).
- **Never delete an issue.** Close it instead. Deleting one needs the repository owner's explicit OK.
- **Ask before** opening, closing or editing an issue the user hasn't agreed to.
- The repository is public: no secrets, account details or personal data in issues.

Issues created by the content pipeline's alerts ("The live site is not updating", "The content tests failed") are alerts, not backlog. Handle them as `docs/developer-guide.md` describes.

## Keep the guides current

When a change alters how editors or the developer work, update `docs/editor-guide.md` (in Greek) and `docs/developer-guide.md` in the same pull request.
