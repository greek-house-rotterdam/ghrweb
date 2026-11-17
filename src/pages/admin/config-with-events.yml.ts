// The Decap configuration /admin loads: public/admin/config.yml with the
// event field as a dropdown of Ticket Tailor events (#105). Edit config.yml,
// not this. See src/lib/admin-events.ts.
import type { APIRoute } from "astro";
import { getCollection } from "astro:content";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parse } from "yaml";
import { configYaml, pickerEvents, withEventPicker, type DecapConfig } from "../../lib/admin-events";

export const prerender = true;

export const GET: APIRoute = async () => {
  // Read on every request, so `astro dev` shows config.yml changes at once.
  const config = parse(readFileSync(join(process.cwd(), "public/admin/config.yml"), "utf-8")) as DecapConfig;
  const [events, translations] = await Promise.all([getCollection("events"), getCollection("eventTranslations")]);
  const greekEntryIds = translations.filter((t) => t.data.lang === "gr").map((t) => t.data.tt_event_id);
  const result = withEventPicker(config, pickerEvents(events, new Date()), greekEntryIds);
  return new Response(configYaml(result), {
    headers: { "Content-Type": "text/yaml; charset=utf-8" },
  });
};
