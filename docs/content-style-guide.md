# Content Style Guide — Greek House in Rotterdam

Rules for writing and reviewing content published on the website. Used by editors directly and by the automated AI content review workflow (`.github/workflows/content-review.yml`).

---

## Tone & Voice

- **Warm and welcoming** — the reader may be a newcomer to the Netherlands, unfamiliar with the association, or not a Greek speaker. Write as if welcoming someone into your home.
- **Clear and direct** — avoid bureaucratic language, jargon, or overly formal phrasing. Simple sentences over complex ones.
- **Inclusive** — the association welcomes all nationalities. Avoid language that implies membership is only for Greeks.
- **Positive and community-oriented** — focus on what the association offers, not what it restricts.

## Language Rules

- **No profanity, slurs, or discriminatory language** — in any language. This is a critical violation.
- **No political statements or partisan content** — the association is a cultural organization, not a political one.
- **No commercial promotion** — events may have sponsors, but posts should not read as advertisements.
- **Factual accuracy** — dates, times, locations, and prices must be verifiable. Do not publish speculative or unconfirmed information.
- **Consistent terminology** — use "Greek House" (en), "Grieks Huis" (nl), "Ελληνικό Σπίτι" (gr). Not "Greek Association", "Griekse Vereniging", etc. unless referring to the legal entity name specifically.

## Structure Rules

- **Title**: Action-oriented or descriptive. Not clickbait. Max 100 characters.
- **Description**: One clear sentence summarizing the post. Max 200 characters. This appears in search results and social previews.
- **Body**: Lead with the most important information. Date/time/location for events should appear in the first paragraph, not buried at the end.
- **Images**: Must be relevant to the content. No stock photos of unrelated subjects.

## Event-Specific Rules

- Always include: date, time, location.
- State whether registration is required and whether membership is needed.
- Include price if applicable (or explicitly state "free" / "free for members").
- If the event has passed, do not edit or delete it — it serves as a record.

## Severity Levels (for AI review)

Used by the automated content review workflow when posting PR comments:

| Severity | Meaning | Examples | Action |
|----------|---------|----------|--------|
| **Critical** | Content that must not be published | Discriminatory language, profanity, harmful content, personally identifiable information (phone numbers, addresses of individuals) | Must fix before merge |
| **Major** | Significant quality or policy issues | Political statements, commercial promotion, factually unverifiable claims, missing event details (date/time/location), title or description exceeding character limits | Should fix before merge |
| **Minor** | Style suggestions, not blocking | Overly formal tone, passive voice, inconsistent terminology, long sentences that could be simplified | Nice to fix, not required |

---

## AI Content Review Workflow

The automated review runs on every PR that changes content files (`src/content/**/*.md`). It uses Gemini 2.0 Flash with the above rules as a system prompt.

**What it does:**
1. Reads changed/added `.md` files from the PR
2. Sends frontmatter + body to Gemini Flash with the style guide as context
3. Posts PR comments for each finding, tagged with severity level
4. Does **not** block the PR — findings are advisory

**What it does NOT do:**
- It does not modify content (no auto-fixes, no commits)
- It does not replace human review — it augments it
- It does not check grammar or spelling (editors and translators handle that)

**Configuration:**
- Requires `GEMINI_API_KEY` secret in GitHub repository settings
- Model: `gemini-2.0-flash` (or latest Flash variant)
- Workflow: `.github/workflows/content-review.yml`
- Script: `.github/scripts/content_review.py`
