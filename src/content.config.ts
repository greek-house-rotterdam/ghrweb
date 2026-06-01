import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const langEnum = z.enum(["gr", "nl", "en"]);

// Fields added by the auto-translation pipeline (translate.py)
const translationMeta = {
  source_hash: z.string().optional(),
  translation_locked: z.boolean().optional(),
};

const news = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/news" }),
  schema: z.object({
    title: z.string().max(100),
    description: z.string().max(200),
    date: z.coerce.date(),
    image: z.string().optional(),
    lang: langEnum,
    ...translationMeta,
  }),
});

async function fetchTicketTailorEvents() {
  const key = process.env.TT_API_KEY;
  if (!key) {
    // CI builds (test smoke + Cloudflare preview) don't have the secret, and
    // shouldn't fail on its absence. Local dev sees the warning and remembers
    // to set it before they need real event data.
    console.warn(
      "[content.config] TT_API_KEY not set — returning an empty events list. " +
        "Set TT_API_KEY in .env to fetch from Ticket Tailor (see docs/events-ticket-tailor.md).",
    );
    return [];
  }
  const auth = "Basic " + Buffer.from(key).toString("base64");
  const url =
    "https://api.tickettailor.com/v1/events?status=published&limit=100";
  const res = await fetch(url, {
    headers: { Authorization: auth, Accept: "application/json" },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(
      `Ticket Tailor API ${res.status}: ${body.slice(0, 300)}`,
    );
  }
  const json = (await res.json()) as { data?: TTEvent[] };
  const items = Array.isArray(json.data) ? json.data : [];
  return items.map((e) => {
    const html = e.description ?? "";
    const plain = html
      .replace(/<[^>]+>/g, " ")
      .replace(/&nbsp;/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return {
      id: e.id,
      name: e.name ?? "",
      description_html: html,
      description_text: plain.length > 200 ? plain.slice(0, 197) + "…" : plain,
      start_iso: e.start?.iso ?? "",
      end_iso: e.end?.iso ?? undefined,
      url: e.url ?? "",
      checkout_url: e.checkout_url ?? e.url ?? "",
      image_url: e.images?.header ?? e.images?.thumbnail ?? undefined,
      status: e.status ?? "published",
      venue: e.venue?.name ?? undefined,
      sold_out: e.tickets_available === "false" || e.unavailable === "true",
    };
  });
}

interface TTEvent {
  id: string;
  name?: string;
  description?: string;
  start?: { iso?: string };
  end?: { iso?: string };
  url?: string;
  checkout_url?: string;
  images?: { header?: string; thumbnail?: string };
  status?: string;
  venue?: { name?: string };
  tickets_available?: string;
  unavailable?: string;
}

const events = defineCollection({
  loader: fetchTicketTailorEvents,
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
    description: z.string().max(200),
    lang: langEnum,
    ...translationMeta,
  }),
});

const activities = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/activities" }),
  schema: z.object({
    title: z.string().max(100),
    description: z.string().max(200),
    image: z.string().optional(),
    emoji: z.string().optional(),
    schedule: z.string().optional(),
    order: z.number().default(100),
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
    description: z.string().max(200),
    category: z.string(),
    order: z.number().default(100),
    lang: langEnum,
    ...translationMeta,
  }),
});

// Long-form prose sections rendered on the static pages (history, about, teams).
// Each entry is one section; the page concatenates them ordered by `order` ASC.
const pageSections = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/page-sections" }),
  schema: z.object({
    page: z.enum(["about", "history", "teams"]),
    order: z.number().default(100),
    title: z.string().max(120),
    lang: langEnum,
    ...translationMeta,
  }),
});

// Timeline rows on /history. Year is the visual anchor and is locale-agnostic;
// only `title` is translated. Sorted by `year` ASC at render time.
//
// When `linkedSection` is set to a `page-sections` slug (the filename without
// .md), the card on /history becomes a link that jumps to the matching
// long-form section further down the page.
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
  pageSections,
  historyMilestones,
};
