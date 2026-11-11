// Events from Ticket Tailor, fetched while Cloudflare builds the site.
//
// What happens when Ticket Tailor can't be reached (an outage, or a missing,
// wrong or revoked key) depends on the build:
// - Production (Cloudflare building `main`): the build stops with an error.
//   Cloudflare then keeps the current live site, events included, and the next
//   good build (the nightly rebuild, or the next merge) publishes.
// - Everything else (PR previews, local builds, the test build): a warning, and
//   the site is built without events, so editors can keep saving and
//   publishing posts.

const EVENTS_URL = "https://api.tickettailor.com/v1/events?status=published&limit=100";
const TIMEOUT_MS = 15_000;
// Waits between attempts: three tries in all.
const RETRY_DELAYS_MS = [2_000, 5_000];

export interface TTEvent {
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

export interface SiteEvent {
  id: string;
  name: string;
  description_html: string;
  description_text: string;
  start_iso: string;
  end_iso?: string;
  url: string;
  checkout_url: string;
  image_url?: string;
  status: string;
  venue?: string;
  sold_out: boolean;
}

type Env = Record<string, string | undefined>;

interface Options {
  env: Env;
  fetchImpl?: typeof fetch;
  sleep?: (ms: number) => Promise<void>;
  warn?: (message: string) => void;
}

/**
 * True when Cloudflare is building the live site. Cloudflare sets WORKERS_CI=1
 * and WORKERS_CI_BRANCH on every build. A build without a branch name (such
 * as one started by a deploy hook, if Cloudflare leaves it out) counts as
 * production: being strict there keeps an empty events page off the live site.
 */
export function isProductionBuild(env: Env): boolean {
  if (env.WORKERS_CI !== "1") return false;
  const branch = env.WORKERS_CI_BRANCH?.trim();
  return !branch || branch === "main";
}

export async function loadEvents({
  env,
  fetchImpl = fetch,
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  warn = (message) => console.warn(message),
}: Options): Promise<SiteEvent[]> {
  const production = isProductionBuild(env);
  const key = env.TT_API_KEY?.trim();

  if (!key) {
    if (production) {
      throw new Error(
        "[events] TT_API_KEY is not set, so the live site would have no events. " +
          "Set it in Cloudflare: ghrweb → Settings → Build → Variables and secrets.",
      );
    }
    warn("[events] TT_API_KEY is not set: building without events (fine for previews and local builds).");
    return [];
  }

  try {
    const items = await fetchEvents(key, fetchImpl, sleep);
    return items.map(toSiteEvent);
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    if (production) {
      throw new Error(
        `[events] Could not read events from Ticket Tailor: ${reason}. ` +
          "The live site stays as it is; the next build tries again.",
      );
    }
    warn(`[events] Could not read events from Ticket Tailor (${reason}): building this preview without events.`);
    return [];
  }
}

/** A failed request worth trying again: a timeout, a network error, 429 or 5xx. */
class RetryableError extends Error {}

async function fetchEvents(
  key: string,
  fetchImpl: typeof fetch,
  sleep: (ms: number) => Promise<void>,
): Promise<TTEvent[]> {
  // Ticket Tailor's docs: "Authorization: Basic Base64Encode(api_key)".
  const auth = "Basic " + Buffer.from(key).toString("base64");
  let lastError: unknown;
  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
    if (attempt > 0) await sleep(RETRY_DELAYS_MS[attempt - 1]);
    try {
      return await fetchOnce(auth, fetchImpl);
    } catch (error) {
      lastError = error;
      if (!(error instanceof RetryableError)) break;
    }
  }
  throw lastError;
}

async function fetchOnce(auth: string, fetchImpl: typeof fetch): Promise<TTEvent[]> {
  let res: Response;
  try {
    res = await fetchImpl(EVENTS_URL, {
      headers: { Authorization: auth, Accept: "application/json" },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    throw new RetryableError(`no answer (${reason})`);
  }
  if (!res.ok) {
    const body = (await res.text()).slice(0, 300);
    const message = `HTTP ${res.status}: ${body}`;
    // 401/403: a wrong or revoked key. Trying again won't help.
    if (res.status === 429 || res.status >= 500) throw new RetryableError(message);
    throw new Error(message);
  }
  const json = (await res.json()) as { data?: TTEvent[] };
  return Array.isArray(json.data) ? json.data : [];
}

export function toSiteEvent(e: TTEvent): SiteEvent {
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
}
