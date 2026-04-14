import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const langEnum = z.enum(["gr", "nl", "en"]);

const news = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/news" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.coerce.date(),
    image: z.string().optional(),
    lang: langEnum,
  }),
});

const eventCategory = z
  .enum(["workshop", "social", "cultural", "class", "meetup", "other"])
  .default("other");

const events = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/events" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.coerce.date(),
    endDate: z.coerce.date().optional(),
    location: z.string().optional(),
    category: eventCategory,
    price: z.string().optional(),
    registrationRequired: z.boolean().default(false),
    image: z.string().optional(),
    lang: langEnum,
  }),
});

const activities = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/activities" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    emoji: z.string().optional(),
    schedule: z.string().optional(),
    image: z.string().optional(),
    order: z.number().default(100),
    lang: langEnum,
  }),
});

const faq = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/faq" }),
  schema: z.object({
    question: z.string(),
    answer: z.string(),
    order: z.number().default(100),
    lang: langEnum,
  }),
});

const resources = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/resources" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.string(),
    order: z.number().default(100),
    lang: langEnum,
  }),
});

export const collections = { news, events, activities, faq, resources };
