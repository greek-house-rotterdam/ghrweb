import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const news = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/news" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.coerce.date(),
    image: z.string().optional(),
    lang: z.enum(["gr", "nl", "en"]),
  }),
});

const events = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/events" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.coerce.date(),
    endDate: z.coerce.date().optional(),
    location: z.string().optional(),
    image: z.string().optional(),
    lang: z.enum(["gr", "nl", "en"]),
  }),
});

export const collections = { news, events };
