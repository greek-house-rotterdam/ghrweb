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
- **Names are welcome** — community stories may name members, volunteers, artists, speakers or Greek entrepreneurs in the Netherlands, and say what they do or have achieved. A story about a person or their business is on topic; it only becomes commercial promotion when it reads as an advertisement.
- **No private contact details** — no private phone number or home address of an individual. The association's own contact details, a venue's address and a business's public website are fine.
- **No spam, scams or investment advice** — no links to suspicious or unrelated sites, and no tips to buy, sell or hold stocks, crypto or other investments.
- **Stay on topic** — every post is about the association, its activities, Greek culture or the Greek community.
- **Factual accuracy** — dates, times, locations, and prices must be verifiable. Do not publish speculative or unconfirmed information.
- **Consistent terminology** — use "Greek House" (en), "het Griekse Huis" (nl), "Ελληνικό Σπίτι" (gr). Not "Greek Association", "Griekse Vereniging", etc. unless referring to the legal entity name specifically.

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
| **Critical** | Content that must not be published | Harmful, hateful or discriminatory content, profanity, a private individual's phone number or home address, spam or scam links, investment advice, content clearly unrelated to the association and the Greek community | **Held:** the post can't go live until it's corrected |
| **Major** | Significant quality or policy issues | Political statements, commercial promotion, factually unverifiable claims, missing event details (date/time/location), title or description exceeding character limits | Should fix; doesn't hold the post |
| **Minor** | Style suggestions | Overly formal tone, passive voice, inconsistent terminology, long sentences that could be simplified | Nice to fix; doesn't hold the post |

Naming people is never a finding on its own.

---

## AI Content Review Workflow

The automated review runs on every PR that changes content files (`src/content/**/*.md`). It uses Gemini Flash with the above rules as a system prompt. The workflow runs `main`'s copy of the script and of this guide, so every draft is reviewed by the current rules, even one made before a rule changed.

**What it does:**
1. Reads changed/added `.md` files from the PR
2. Sends frontmatter + body to Gemini Flash with the style guide as context
3. Lists the findings per file, tagged with severity level, in the AI review section of the PR's status comment, shown open under each file's name (not folded, so editors see them)
4. **Holds the post on a critical finding:** the `ai-gate` check fails, so the post can't go live, even when it's set to Ready. Once the editor corrects the post and saves, the review runs again; when no critical finding is left, the post goes live by itself (if it's set to Ready). Major and minor findings are advice only and never hold a post. A review that couldn't run doesn't hold the post either.
5. Shows the result on the post's card in `/admin` → Workflow: an "AI review" badge coloured by the most serious finding (red critical, orange major, yellow minor, green none, grey when the review couldn't run), which opens the status comment (#135)
6. Mentions the admins in the status comment when a finding is critical. Only an admin can publish a held post anyway (if the AI is wrong), by merging the pull request on GitHub and bypassing the rules.

**What it does NOT do:**
- It does not modify content (no auto-fixes, no commits)
- It does not replace human review — it augments it
- It does not check grammar or spelling (editors and translators handle that)

**Configuration:**
- Requires `GEMINI_API_KEY` secret in GitHub repository settings
- Model: `gemini-3.8-flash` (stable). Set `GEMINI_MODEL_DEFAULT` in `.github/scripts/_common.py`, shared with translation.
- Workflow: `.github/workflows/content-review.yml`
- Script: `.github/scripts/content_review.py`
