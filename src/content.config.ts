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

const eventCategory = z
  .enum(["workshop", "social", "cultural", "class", "meetup", "other"])
  .default("other");

const events = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/events" }),
  schema: z.object({
    title: z.string().max(100),
    description: z.string().max(200),
    date: z.coerce.date(),
    endDate: z.coerce.date().optional(),
    location: z.string().optional(),
    category: eventCategory,
    price: z.string().optional(),
    registrationRequired: z.boolean().default(false),
    image: z.string().optional(),
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

export const collections = { news, events, activities, faq, resources };
