# Design System — Greek House in Rotterdam

Current visual style, implementation details, and rationale. Reference this before making visual changes.

---

## Style: Neo-Brutalist

Flat, high-contrast, bold. No gradients, no soft shadows, no rounded corners.

### Core visual rules

| Property | Value | Where defined |
|----------|-------|---------------|
| Borders | `border-2 border-black` (cards, buttons), `border-4 border-black` (sections) | Inline Tailwind classes |
| Shadows | `shadow-[4px_4px_0_0_#000]` (cards), `shadow-[3px_3px_0_0_#000]` (small elements) | Inline Tailwind classes |
| Corners | Square everywhere — `--radius: 0` in Starwind theme | `src/styles/starwind.css:104` |
| Hover | Shadow removed + translate: `hover:shadow-none hover:translate-x-1 hover:translate-y-1` | Inline Tailwind classes |
| Typography | `font-extrabold` headings, `-0.025em` letter-spacing | `src/styles/starwind.css` `@layer base` |
| Font | `system-ui, -apple-system, sans-serif` | `src/styles/starwind.css` `@layer base` |

### Color tokens

Defined in `src/styles/starwind.css` via Tailwind CSS v4 `@theme`.

| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#0D5EAF` | Hellenic Blue — hero backgrounds, buttons, links |
| `primary-dark` | `#094A8D` | Button hover states |
| `primary-light` | `#DBEAFE` | Date badges, schedule labels |
| `primary-lighter` | `#EFF6FF` | Section backgrounds (mission box) |
| `accent-gold` | `#FACC15` | Mediterranean Gold — CTA buttons, hover states, highlights |
| `accent-gold-dark` | `#D4A90A` | (reserved) |
| `accent-gold-light` | `#FEF9C3` | FAQ hover, team cards |
| `accent-gold-lighter` | `#FEFCE8` | Section backgrounds (board, events) |

**Why `accent-gold` instead of `accent`:** Starwind reserves `accent` for a neutral gray used internally by its components. Our gold color was renamed to `accent-gold-*` to avoid collision. All `.astro` files use the `accent-gold-*` variants.

Starwind's own semantic tokens (`primary`, `secondary`, `muted`, `error`, etc.) are mapped in the `:root` and `.dark` blocks of `starwind.css`. The `--primary` variable points to `#0D5EAF` (our Hellenic Blue), not Starwind's default blue-700.

---

## Starwind UI Integration

8 components installed at `src/components/starwind/`. 4 are actively used. 4 are available but intentionally not used in current pages.

### Used

| Component | Where | Why |
|-----------|-------|-----|
| **Sheet** | `Header.astro` — mobile nav drawer | Overlay, focus trapping, ESC close, animation. Replaces `<details>` hack. |
| **Accordion** | `faq.astro` | Keyboard nav (Arrow Up/Down, Home, End), ARIA (`aria-expanded`, `aria-controls`), smooth height animation. Replaces native `<details>`. |
| **Avatar** | `about.astro` — board members | `AvatarFallback` for initials, `AvatarImage` ready for future photos, semantic `<figure>`. |
| **Button** | `events/index.astro` — category filters | Consistent `focus-visible` ring states. |

### Not used (and why)

| Component | Reason |
|-----------|--------|
| **Card** | Starwind Card uses `ring-1 ring-border rounded-xl`. Our cards use `border-2 border-black shadow-[4px_4px_0_0_#000]` with a hover-translate effect. Overriding every Card class would be more code than the current flat divs. No functional benefit — our cards are already semantic (`<a>` or `<div>` with clear structure). |
| **Badge** | Starwind Badge uses `rounded-full` (hardcoded `9999px`, not theme-derived). Our badges are square (`border border-black bg-accent-gold px-2 py-0.5`). Override would require `rounded-none` on every instance plus color remapping. Not worth it for simple inline spans. |
| **Pagination** | Content volume too low to need it. Revisit when any listing exceeds ~20 items. |
| **Dialog** | Installed as a Sheet dependency. No direct use case currently. |

### Global theme override

`--radius: 0` in `starwind.css` eliminates rounded corners on all Starwind components. This works because `rounded-sm` through `rounded-3xl` are all derived from `--radius` via `calc()`.

**Exception:** `rounded-full` is a fixed CSS value (`border-radius: 9999px`), not derived from `--radius`. Components that use it (Avatar, Badge) require explicit `class="rounded-none"` overrides.

---

## What it would take to change the style

### Scenario: Switch from brutalist to a softer/rounded aesthetic

1. **`starwind.css`**: Set `--radius` back to `0.625rem` (or desired value). This re-enables rounded corners on all Starwind components.

2. **Shadows**: Find-and-replace `shadow-[4px_4px_0_0_#000]` across all `.astro` files. Replace with Tailwind's `shadow-md` / `shadow-lg` or Starwind's default `ring-1 ring-border`.

3. **Borders**: Replace `border-2 border-black` with lighter borders (`border border-border` or `ring-1 ring-border`). This affects ~15 page files and 3 components (Header, Footer, LanguagePicker).

4. **Hover effects**: Replace `hover:shadow-none hover:translate-x-1 hover:translate-y-1` with standard hover states (`hover:bg-muted` or `hover:ring-2`).

5. **Starwind adoption**: With rounded corners restored, Card and Badge become usable without overrides. Migrate news/events cards to `<Card>`, date labels to `<Badge>`, and CTA links to `<Button href="...">`.

6. **Accent color naming**: The `accent-gold-*` tokens would remain valid regardless of style. However, if adopting Starwind's `accent` token for the gold color, you'd need to remap `--accent` in both `:root` and `.dark` blocks from neutral to `#FACC15`, then rename `accent-gold-*` back to `accent-*` across all files.

**Estimated scope**: ~20 files, mostly find-and-replace for Tailwind classes. The content, schemas, i18n, and page structure are style-independent.

### Scenario: Keep brutalist but adopt more Starwind components

Add a custom `brutalist` variant to Starwind's Button `tv()` definition in `src/components/starwind/button/Button.astro`:

```ts
brutalist: "border-2 border-black font-extrabold shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-x-1 hover:translate-y-1 transition-all"
```

Then use `<Button variant="brutalist" href="...">` for CTAs instead of raw `<a>` tags. Same approach could work for Card if desired — add a `brutalist` variant that applies thick borders and offset shadows.

---

## File reference

| File | Role |
|------|------|
| `src/styles/starwind.css` | All theme tokens, color definitions, radius, animations, base layer rules |
| `src/components/starwind/` | Starwind component source (editable — not a node_module) |
| `src/components/Header.astro` | Nav order, mobile Sheet, CTA button |
| `src/components/Footer.astro` | Footer links, social icons |
| `src/components/LanguagePicker.astro` | Language switcher |
| `src/layouts/Layout.astro` | Imports `starwind.css`, wraps all pages |
| `public/admin/config.yml` | Decap CMS collections and field definitions |
| `src/content.config.ts` | Zod schemas for all content collections |
| `src/i18n/ui.ts` | All UI translation keys (3 languages) |
