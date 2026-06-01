# Events × Ticket Tailor — findings, options, recommendations

## What we built

Ticket Tailor is now the source of truth for event metadata. At build time, a custom Astro loader hits `GET https://api.tickettailor.com/v1/events` and feeds the `events` content collection. A thin per-language overlay collection (`eventTranslations`, markdown) carries translated title/description/body keyed by TT event ID. The existing Brutalist grid renders the merged result.

Routes:

- `/{lang}/events` — API-driven grid (3 cols on desktop). Falls back to TT name/description when no overlay exists.
- `/{lang}/events/{ev_*}` — detail page. Overlay-or-TT title/description, HTML body from TT or rich markdown body from overlay, "Buy tickets" linking to TT `checkout_url`.
- `/{lang}/events/calendar` — embeds the TT widget with `data-inline-lang` matching the locale. View (list / grid / calendar) is controlled in TT dashboard → *Promote → Widget settings*.

Files: `src/content.config.ts`, `src/pages/[lang]/events/{index,[slug],calendar}.astro`, `public/admin/config.yml`, `src/i18n/ui.ts`, `.env.example`, `.envrc` (gitignored — holds `TT_API_KEY`).

## Findings about the TT REST API

- Auth is `Authorization: Basic Base64(key:)` (HTTP Basic, key as username, empty password).
- API key permissions are per-key in TT dashboard. The `/v1/events` endpoint requires explicit "Events: Read" permission — not granted by default. Granting Events read does *not* automatically include Orders/Issued Tickets; check those boxes too if you want a single read-everything dev key.
- Event ID format is `ev_*` (e.g. `ev_8112397`), not the digits visible in the public URL (those are `event_series_id`).
- `event.start` / `event.end` are objects with `{iso, date, time, timezone, unix, formatted}`. We read `.iso`.
- `event.description` is **raw HTML** (`<p>`, `<br>`, `<b>`, etc.). The loader produces both `description_html` (for detail-page body) and `description_text` (HTML-stripped, 200-char snippet for cards).
- Many boolean-like fields are strings: `tickets_available` is `"true"` / `"false"`, same for `unavailable`, `hidden`, `online_event`, etc. We coerce explicitly.
- `event.url` is the public event page (`/events/grieksehuis/{event_series_id}`); `event.checkout_url` jumps straight to checkout. We use `url` for "see event" and `checkout_url` for the "Buy tickets" CTA.
- Rate limit: 5,000 requests / 30 min — effectively a non-issue for build-time use.

## Findings about the embed widget

- Widget JS is at `https://cdn.tickettailor.com/js/widgets/min/widget.js`.
- The auto-discovery loop requires either `class="tt-widget"` on the script's parent element, or literal `type="inline"` on the script tag (which would block JS execution, so use the parent class).
- `data-inline-lang` translates UI chrome only (button labels, date words, "Sold out"). Supported codes include `en`, `nl`, `el` (Greek). It does **not** translate event titles/descriptions stored in TT.
- Layout (list / 3-col grid / calendar) is configured globally per box office in TT dashboard → *Promote → Widget settings*. Cannot be overridden per-embed.
- "Event ticketing by Ticket Tailor" footer attribution is paid-plan-removable; `data-inline-show-logo="false"` only hides the logo image.

## Current dev-server noise (not a bug)

`getCollection("eventTranslations")` against an empty directory logs:

```
The collection "eventTranslations" does not exist or is empty. Please check your content config file for errors.
```

The page still renders and returns 200. The warning disappears as soon as one overlay file exists. **Fix options:**

1. **Seed a placeholder file** (e.g. `src/content/event-translations/en/.gitkeep.md` with frontmatter only) — silences the warning permanently. Mildly hacky but invisible to users.
2. **Wrap the calls** in a try/getEntries pattern that swallows the empty-collection case. More code, same end state.
3. **Live with it** — log noise only, no user impact.

Recommendation: defer until the first real overlay file is created in Decap. That naturally resolves it.

## Translation automation — options

The existing pipeline `.github/scripts/translate.py` already globs `src/content/{collection}/{lang}/*.md` and translates `title`, `description`, and `body` using Gemini Flash. The `eventTranslations` collection is automatically eligible — the only missing piece is **stub creation** (translate.py can only translate files that already exist).

### Option A — build-time seeding (recommended)

The Astro loader (or a small Node script in `npm run prebuild`) scans TT events and writes a stub `src/content/event-translations/en/{ev_*}.md` for any TT event missing one. The stub pre-fills `title` and `description` from TT's name/description_text. A GH Action runs translate.py on the resulting changes and commits the gr/nl files. Subsequent builds pick everything up.

- **Pros:** zero new infrastructure, reuses existing translate.py + GH Actions. Stays declarative: state of `src/content/event-translations/` always reflects TT reality.
- **Cons:** stub generation runs at build/script time, so a freshly-created TT event won't appear on the live site until the next deploy. Acceptable if events change weekly, not hourly.
- **Effort:** ~half day. Net new code: ~50 lines (seed script) + a few lines in the existing translation GH Action.

### Option B — webhook-driven PR

TT fires `event.created` → Cloudflare Worker → GitHub `repository_dispatch` (or PR API) → Worker opens a PR adding the en stub file → existing translate.py CI fills gr/nl → admin reviews + merges → Cloudflare Pages redeploys.

- **Pros:** fully automated end-to-end; site updates within minutes of a TT change.
- **Cons:** more moving parts (Worker, webhook auth, GH bot token, PR review etiquette). Failure modes are remote.
- **Effort:** ~1 day. New: ~80 lines of Worker code, GH secret rotation, optional Slack notification.

### Option C — AI splitter for bilingual TT descriptions

Today TT descriptions cram Greek + English into one HTML field separated by `<hr />`. An LLM step (Gemini Flash) can split that into canonical en + gr texts and seed both overlays directly, skipping translate.py for the source pair. Pair with Option A or B.

- **Pros:** no double-editing in TT.
- **Cons:** extra LLM call per event, splitting heuristics can be wrong on edge cases (events with only one language, with multiple `<hr />`s).

## Authoring pipeline — recommended convention

Today event descriptions in TT are bilingual concatenations. We should pick a single canonical authoring language going forward.

**Recommendation: English in TT.** Reasons:

- Gemini Flash translates *from* English to gr/nl cleanest in our experience.
- TT's own UI chrome (buttons, emails to ticket buyers) is English by default for international audiences anyway.
- The overlay system carries gr/nl. The TT detail page (for visitors who go directly there, bypassing our site) is single-language English — acceptable trade-off.

If preserving Greek-first authoring matters (e.g. for direct TT visitors), invert: canonical Greek in TT, overlay carries en/nl. translate.py handles either direction.

## UX redesign — issues to address

Surfaced during the integration; worth a follow-up pass on `/{lang}/events`:

1. **Past events are not filtered.** The TT API returns all published events including past ones. Index page should hide `start < now` by default and offer a "Past events" toggle or separate route.
2. **Date format lacks time of day.** Currently shows `15/03/2026`. Events are time-sensitive — show `Sat 15 Mar, 19:00`. `formatDate` in `src/i18n/utils.ts` needs a time variant.
3. **Card snippets degrade without overlays.** With TT's bilingual HTML descriptions, the 200-char `description_text` is half Greek, half English on every card. Once Option A/B is in, the en overlay fixes this.
4. **No pricing on cards.** TT exposes `ticket_types[].price` (in cents). "From €8" is a small change that helps decisions.
5. **CTA state is binary.** Today: "Buy tickets" or "Sold out". TT also signals "Select tickets" (multiple types), "Free entry" (€0 ticket), "Tickets unavailable" (date-gated). Map them to the badge color system.
6. **Category filter was removed.** TT doesn't carry our `workshop/social/cultural/...` enum. Two paths: add a `category` field to the overlay schema (admin tags during translation), or use `event_series_id` for grouping recurring events (theater performances, etc.).
7. **Hero / featured event.** With a real event roster, the next upcoming event deserves a hero treatment above the grid — image, full description, prominent CTA.
8. **Calendar view is a separate route.** Could be inlined as a tab on `/events` if the widget supports being put alongside other content (it does, via `class="tt-widget"`).
9. **Venue context is thin.** "KINO" alone isn't navigable. TT API has `venue.country`, `venue.postal_code`. A small "📍 KINO, 3014 PM Rotterdam" pattern is a quick win.

## Recommended next steps

1. **Seed one English overlay manually** via Decap admin (~5 min) to silence the dev-server warning and validate the round-trip.
2. **Implement Option A** (build-time seed + translate.py) — ~half day. Stop authoring two languages in TT.
3. **Switch to English authoring in TT**; translate.py owns gr/nl going forward.
4. **UX pass on the events page** (items 1, 2, 5, 8 above are highest-value, lowest-effort).
5. **Webhook rebuild (Option B)** — only if events start changing more often than the natural deploy cadence.

Defer: pricing on cards (item 4), category filter (6), hero treatment (7), venue context (9) — all worthwhile but not blocking.
