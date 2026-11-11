// When and from which commit the live site was built. The nightly rebuild
// (.github/workflows/nightly-rebuild.yml) reads it to check that the live site
// really updated, and opens an issue if it didn't.
import type { APIRoute } from "astro";
import { getCollection } from "astro:content";

export const prerender = true;

export const GET: APIRoute = async () => {
  const events = await getCollection("events");
  return new Response(
    JSON.stringify({
      built_at: new Date().toISOString(),
      commit: process.env.WORKERS_CI_COMMIT_SHA ?? null,
      branch: process.env.WORKERS_CI_BRANCH ?? null,
      events: events.length,
    }),
    { headers: { "Content-Type": "application/json" } },
  );
};
