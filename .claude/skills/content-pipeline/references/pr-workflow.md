# Git and PR workflow

What to run to turn your local changes into a PR that the translation pipeline picks up.

## Before you start

Make sure you're on a clean working tree and synced with `origin/main`:

```bash
git status                       # nothing else staged you don't want
git fetch origin
git checkout main && git pull --ff-only origin main
```

If there are unrelated dirty changes, ask the user how to handle them — don't sweep them into the content PR.

## Branch naming

Pattern: `content/<collection>-<short-slug>`

Examples:
- `content/news-kokoretsi-night`
- `content/activities-tai-chi`
- `content/event-translations-ev-8112397`
- `content/faq-how-to-cancel`

Update an existing post: `content/<collection>-<slug>-update` (or just reuse the slug — `git checkout -b` errors if a branch already exists, which is a useful signal).

```bash
git checkout -b content/news-<slug>
```

## Staging

Stage only files you actually changed. Don't `git add -A`:

```bash
git add src/content/<collection>/<lang>/<slug>.md
git add public/images/<file>.<ext>      # if applicable
```

If you accidentally created files outside `src/content/` or `public/images/` (e.g. test scratch files), don't stage them.

## Commit message

Conventional Commits format. The repo already uses `feat:` / `fix:` / `chore:` etc. — use `content:` (or `feat(content):`) for new content:

```bash
git commit -m "content(<collection>): <title or summary>"
```

Multi-file commits are fine — one commit per logical content unit is the right granularity, not one commit per file.

## Push

```bash
git push -u origin HEAD
```

If push fails because the branch already exists upstream, the user likely already started this work — stop and ask before force-pushing.

## Open the PR

```bash
gh pr create \
  --base main \
  --title "content(<collection>): <short title>" \
  --body "$(cat <<'EOF'
## Summary
- <one-line summary of what was added or changed>
- <why, if not obvious — source material, occasion, etc.>

## What's in this PR
- <list of files added/changed>

## Test plan
- [ ] Translation workflow runs and pushes auto-translated `nl` and `en` files
- [ ] AI content review posts no Critical or Major findings
- [ ] Cloudflare preview deploy renders all three languages
- [ ] CODEOWNERS (translators team / @PanoEvJ for infra) approves
EOF
)"
```

**Critical:**
- **Do not pass `--label decap-cms/draft`.** Decap would list the post as a Draft. (It used to block every content workflow; the workflows now run on every push regardless of labels.)
- **Do not pass `--draft`.** GitHub's "draft PR" state is separate from the Decap label, but it signals "not ready for review" and the codeowners team will ignore it. If the user explicitly says they want to land it later, prefer keeping the PR open and ready and just not merging yourself.

## After opening

Print the PR URL to the user and tell them what will happen next:

> Opened PR <URL>. Within a few minutes:
> - The translation workflow will commit `nl` and `en` versions back to the branch.
> - The image QA workflow will optimize any new images.
> - The content review workflow will post advisory comments.
> Once translators approve, merge and Cloudflare will deploy.

Then **stop**. Don't merge the PR yourself. Don't try to manually run the translation script — the workflow does that. Don't push more commits unless the user asks.

## Updating an existing PR

If the user wants to add more content to a still-open PR:

```bash
git checkout <existing-branch>
git pull --ff-only origin <existing-branch>     # in case the bot pushed translations
# ...make edits...
git add <paths>
git commit -m "content: <change>"
git push
```

A `synchronize` event will fire and the workflows re-run on the new files only.

## Gotchas

- **The translation bot will push to your branch.** If you have local commits the bot doesn't have, you'll need `git pull --rebase` before pushing again. This is normal.
- **CODEOWNERS blocks merge.** Even your own PR needs approval from `@greek-house-rotterdam/translators` (for content) or `@PanoEvJ` (for infra). The skill produces content-only PRs, so it's the translators team.
- **`verify_content.py` runs after translation.** If the bot fails to translate (e.g. Gemini outage), the PR will end up with the source file present but `nl`/`en` missing. The `verify` job fails the build until the translation completes. Re-running the workflow usually fixes transient failures.
- **Don't rename a file after it's been translated.** The `nl` and `en` filenames mirror the source; renaming the source orphans the translations. If you must rename, delete the old triple and recreate.
