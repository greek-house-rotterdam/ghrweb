// Events from Ticket Tailor, shaped for lists (the events page and the home
// page), and split into upcoming and past.
//
// The site is static: "now" is when the site was built. The nightly rebuild
// and the Ticket Tailor webhooks rebuild it, so an event moves from upcoming
// to past within a day of ending.

import { descriptionOrExcerpt } from "./excerpt";

/** The fields of a Ticket Tailor event that lists use (see content.config.ts). */
export interface EventEntry {
  id: string;
  data: {
    name: string;
    description_text: string;
    start_iso: string;
    end_iso?: string;
    venue?: string;
    image_url?: string;
    sold_out: boolean;
  };
}

/** A translation of an event's title and description (event-translations). */
export interface EventOverlay {
  data: { tt_event_id: string; lang: string; title: string; description?: string };
  body?: string;
}

export interface ListEvent {
  id: string;
  title: string;
  description: string;
  start: Date;
  end: Date | undefined;
  venue: string | undefined;
  imageUrl: string | undefined;
  soldOut: boolean;
}

function parseDate(iso: string | undefined): Date | undefined {
  if (!iso) return undefined;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? undefined : d;
}

/** Events in one language: a translation's title and description win over Ticket Tailor's. */
export function toListEvents(events: EventEntry[], overlays: EventOverlay[], lang: string): ListEvent[] {
  const byId = new Map(overlays.filter((o) => o.data.lang === lang).map((o) => [o.data.tt_event_id, o]));
  return events.map((e) => {
    const overlay = byId.get(e.id);
    return {
      id: e.id,
      title: overlay?.data.title ?? e.data.name,
      description: descriptionOrExcerpt(overlay?.data.description, overlay?.body) || e.data.description_text,
      // An event without a readable date counts as long past (time 0).
      start: parseDate(e.data.start_iso) ?? new Date(0),
      end: parseDate(e.data.end_iso),
      venue: e.data.venue,
      imageUrl: e.data.image_url,
      soldOut: e.data.sold_out,
    };
  });
}

const soonestFirst = (a: ListEvent, b: ListEvent) => a.start.getTime() - b.start.getTime();
const newestFirst = (a: ListEvent, b: ListEvent) => b.start.getTime() - a.start.getTime();

/**
 * Upcoming events (not yet ended at `now`), soonest first, so the next event
 * is at the top; and past events, the most recent first.
 * An event without an end time counts as ended when it starts.
 */
export function splitEvents(events: ListEvent[], now: Date): { upcoming: ListEvent[]; past: ListEvent[] } {
  const upcoming: ListEvent[] = [];
  const past: ListEvent[] = [];
  for (const e of events) {
    ((e.end ?? e.start).getTime() >= now.getTime() ? upcoming : past).push(e);
  }
  return { upcoming: upcoming.sort(soonestFirst), past: past.sort(newestFirst) };
}

/** The `count` soonest upcoming events, soonest first. */
export function nextEvents(upcoming: ListEvent[], count: number): ListEvent[] {
  return [...upcoming].sort(soonestFirst).slice(0, count);
}
