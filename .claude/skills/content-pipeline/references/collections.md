# Collection schemas

Authoritative shapes for each collection under `src/content/`. The Zod schema in `src/content.config.ts` validates these at build time; the Decap CMS config (`public/admin/config.yml`) enforces the same constraints in the visual editor. If you write a frontmatter field that's not listed here for a given collection, Zod will error.

All collections also accept (and the auto-translator may add) these meta fields. **Never set them yourself on a source file:**

- `source_hash: string` — set by `translate.py` on translations only.
- `translation_locked: boolean` — only set on a *translation* you want to protect from re-translation.

---

## `news`

Dated announcements, recaps, blog-style posts.

**Path:** `src/content/news/<lang>/<slug>.md`
**Slug:** kebab-case derived from the title (ASCII recommended; Greek/Dutch characters technically work).

```yaml
title: string                    # required, ≤ 100 chars
description: string              # required, ≤ 200 chars
date: date                       # required, ISO 8601 — "2026-02-09" or "2026-04-05T20:00:00.000+03:00"
image: string                    # optional, e.g. "/images/welcome-event.jpg"
lang: "gr" | "nl" | "en"         # required, must match the folder
```

Body: free markdown. Lead paragraph should answer "what, when, where, who" for newsy posts.

---

## `activities`

Recurring/standing programs (language classes, dance group, cooking workshops). Listed on `/activities` ordered by the `order` field.

**Path:** `src/content/activities/<lang>/<slug>.md`
**Slug:** kebab-case of the activity name.

```yaml
title: string                    # required, ≤ 100 chars
description: string              # required, ≤ 200 chars
emoji: string                    # optional, e.g. "💃" "📚" "🎨" — shown in the listing
schedule: string                 # optional, e.g. "Every Thursday 19:00"
image: string                    # optional
order: number                    # default 100 — lower numbers appear first
lang: "gr" | "nl" | "en"         # required
```

Body: free markdown. Often a brief description (no body is fine for very simple listings).

---

## `event-translations`

A translation overlay for a **single Ticket Tailor event**. The event itself (dates, location, prices, tickets) is fetched at build time from the Ticket Tailor API and is *not* in markdown. This collection only translates the event's user-facing copy.

**Path:** `src/content/event-translations/<lang>/<tt_event_id>.md`
**Filename:** must equal `<tt_event_id>.md` (e.g. `ev_8112397.md`). The Decap CMS slug template is `{{tt_event_id}}` for the same reason.

```yaml
tt_event_id: string              # required, e.g. "ev_8112397"
title: string                    # required, ≤ 100 chars
description: string              # required, ≤ 200 chars
lang: "gr" | "nl" | "en"         # required
```

Body: optional. Renders as rich text below the description on the event detail page.

**Verifying `tt_event_id`:** The user must supply it. If they didn't, ask. You can sanity-check that it looks like `ev_<digits>` but you can't fully verify against the API without `TT_API_KEY`. If the user gave you the event name instead of an ID, ask for the ID — the events page in Ticket Tailor shows it in the URL.

---

## `faq`

A single question/answer pair. Body is hidden in the schema and ignored.

**Path:** `src/content/faq/<lang>/<slug>.md`
**Slug:** kebab-case of the question (or a short topic — `how-to-join.md`, `cancellation-policy.md`).

```yaml
question: string                 # required, ≤ 200 chars
answer: string                   # required (no upper bound, but keep it tight)
order: number                    # default 100 — lower numbers appear first
lang: "gr" | "nl" | "en"         # required
```

Body: leave empty after the closing `---`. The Decap CMS config defines a hidden `body: ""` default; the Astro page only reads `answer`.

---

## `page-sections`

Long-form prose sections rendered on the static pages (`/about`, `/history`, `/teams`). One markdown file = one section. The page concatenates entries filtered by `page === <page>` ordered by `order` ascending.

**Path:** `src/content/page-sections/<lang>/<slug>.md`
**Slug:** kebab-case of the section title (e.g. `founding.md`, `cultural-group.md`).

```yaml
page: "about" | "history" | "teams"   # required — which static page renders this section
order: number                          # default 100 — lower numbers render first
title: string                          # required, ≤ 120 chars (a bit longer than other collections — these are section H2 headings)
lang: "gr" | "nl" | "en"               # required
```

Body: markdown — this is the actual long-form content. Headings (`##`), lists, links, emphasis all work.

Use this collection when the content is long enough to want body markdown. For very short labels and intro paragraphs already in `src/i18n/ui.ts`, leave them in i18n.

---

## `history-milestones`

Year/title pairs rendered as the timeline on `/history`. Each entry is one timeline card. Sorted by `year` ascending at render time.

**Path:** `src/content/history-milestones/<lang>/<slug>.md`
**Slug:** the year itself (e.g. `1946.md`). The slug is what `verify_content.py` checks for parity across languages, so keep it consistent.

```yaml
year: string          # required, e.g. "1946" (string, not number — supports ranges like "1965-1971")
title: string         # required, ≤ 140 chars
linkedSection: string # optional — slug of a page-sections entry on /history. When set, the card becomes a link that jumps to that section.
lang: "gr" | "nl" | "en"
```

Body: leave empty — the timeline card only renders year + title (and an optional "read more →" affordance when `linkedSection` is set).

---

## `resources`

Durable "useful information" pages (gemeente registration, healthcare, education, etc.). Listed on `/resources` grouped by `category`.

**Path:** `src/content/resources/<lang>/<slug>.md`
**Slug:** kebab-case of the resource title.

```yaml
title: string                    # required, ≤ 100 chars
description: string              # required, ≤ 200 chars
category: "legal" | "healthcare" | "education" | "housing" | "finance" | "culture" | "other"
order: number                    # default 100
lang: "gr" | "nl" | "en"         # required
```

Body: free markdown. This is the actual reference content the reader is here for — be thorough.

---

## Field types and quirks

- **Dates** use Zod's `z.coerce.date()`, so `"2026-02-09"`, `"2026-02-09T10:00:00Z"`, and `"2026-04-05T20:00:00.000+03:00"` all work. Prefer ISO with timezone when the time-of-day matters.
- **`lang`** must equal the folder name. Mismatch → Zod error.
- **`image`** path always starts with `/images/` (no `public/` prefix). The file must exist at `public/images/<rest>`.
- **`order`** is a number, not a string. Don't quote it.
- **`emoji`** can be any unicode emoji (multi-codepoint is fine). Don't surround with quotes that confuse YAML — use single quotes or unquoted if safe.
