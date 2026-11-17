// The public list of Ticket Tailor events (ID, name, start), written at build
// time. The `verify` check reads it from the live site to catch an event text
// whose ID matches no event (#105). See src/lib/admin-events.ts.
import type { APIRoute } from "astro";
import { getCollection } from "astro:content";
import { pickerEvents } from "../../lib/admin-events";

export const prerender = true;

export const GET: APIRoute = async () => {
  const events = pickerEvents(await getCollection("events"), new Date());
  return new Response(JSON.stringify({ built_at: new Date().toISOString(), events }, null, 2), {
    headers: { "Content-Type": "application/json" },
  });
};
