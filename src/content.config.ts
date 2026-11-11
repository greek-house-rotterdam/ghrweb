import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";
import { URL_SLUG_MAX_LENGTH, URL_SLUG_PATTERN } from "./lib/entry-path";
import { loadEvents } from "./lib/ticket-tailor";

const langEnum = z.enum(["gr", "nl", "en"]);

// Fields added by the auto-translation pipeline (translate.py)
const translationMeta = {
  source_hash: z.string().optional(),
  translation_hash: z.string().optional(),
  translation_locked: z.boolean().optional(),
};

// Optional short Latin address for an entry's page. Shared between languages
// (the translation bot copies it from the Greek file). An empty value means
// "not set". See src/lib/entry-path.ts.
const urlSlug = z
  .string()
  .max(URL_SLUG_MAX_LENGTH)
  .regex(
    URL_SLUG_PATTERN,
    "url_slug: use only lowercase Latin letters, numbers and single hyphens, e.g. pascha-2026",
  )
  .or(z.literal(""))
  .optional();

const news = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/news" }),
  schema: z.object({
    title: z.string().max(100),
    description: z.string().max(200).optional(),
    date: z.coerce.date(),
    image: z.string().optional(),
    url_slug: urlSlug,
    lang: langEnum,
    ...translationMeta,
  }),
});

const events = defineCollection({
  // Ticket Tailor, at build time. See src/lib/ticket-tailor.ts for what
  // happens when it can't be reached.
  loader: () => loadEvents({ env: process.env }),
  schema: z.object({
    name: z.string(),
    description_html: z.string(),
    description_text: z.string(),
    start_iso: z.string(),
    end_iso: z.string().optional(),
    url: z.string(),
    checkout_url: z.string(),
    image_url: z.string().optional(),
    status: z.string(),
    venue: z.string().optional(),
    sold_out: z.boolean(),
  }),
});

const eventTranslations = defineCollection({
  loader: glob({
    pattern: "**/*.md",
    base: "./src/content/event-translations",
  }),
  schema: z.object({
    tt_event_id: z.string(),
    title: z.string().max(100),
    description: z.string().max(200).optional(),
    lang: langEnum,
    ...translationMeta,
  }),
});

const activities = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/activities" }),
  schema: z.object({
    title: z.string().max(100),
    description: z.string().max(200).optional(),
    image: z.string().optional(),
    emoji: z.string().optional(),
    schedule: z.string().optional(),
    order: z.number().default(100),
    url_slug: urlSlug,
    lang: langEnum,
    ...translationMeta,
  }),
});

const faq = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/faq" }),
  schema: z.object({
    question: z.string().max(200),
    answer: z.string(),
    order: z.number().default(100),
    lang: langEnum,
    ...translationMeta,
  }),
});

const resources = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/resources" }),
  schema: z.object({
    title: z.string().max(100),
    description: z.string().max(200).optional(),
    category: z.string(),
    order: z.number().default(100),
    lang: langEnum,
    ...translationMeta,
  }),
});

// Long-form detail-page content. Each entry is one detail page reached at
// /<lang>/history/<slug> or /<lang>/about/<slug>. Programmatic-only —
// not exposed in Decap CMS (see public/admin/config.yml).
const historySections = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/history-sections" }),
  schema: z.object({
    order: z.number().default(100),
    title: z.string().max(120),
    lang: langEnum,
    ...translationMeta,
  }),
});

const aboutSections = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/about-sections" }),
  schema: z.object({
    order: z.number().default(100),
    title: z.string().max(120),
    lang: langEnum,
    ...translationMeta,
  }),
});

// Timeline rows on /history. Year is the visual anchor and is locale-agnostic;
// only `title` is translated. Sorted by `year` ASC at render time.
//
// When `linkedSection` is set to a `history-sections` slug (filename without
// .md), the card on /history becomes a link to /<lang>/history/<slug>.
const historyMilestones = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/history-milestones" }),
  schema: z.object({
    year: z.string(),
    title: z.string().max(140),
    linkedSection: z.string().optional(),
    lang: langEnum,
    ...translationMeta,
  }),
});

export const collections = {
  news,
  events,
  eventTranslations,
  activities,
  faq,
  resources,
  historySections,
  aboutSections,
  historyMilestones,
};
