// Choosing the event in /admin (#105).
//
// Editors used to type a Ticket Tailor event ID (ev_…) by hand, and a typo
// attached the text to no event. Now the build writes two files from the
// events it loaded for the site:
// - /admin/events.json: every event's ID, name and start (all already public
//   on the events pages). The `verify` check reads it from the live site to
//   catch an entry whose ID matches no event (.github/scripts/check_event_ids.py).
// - /admin/config-with-events.yml: public/admin/config.yml with the event field
//   of the event-translations collections turned into a dropdown. Decap loads
//   it instead of config.yml (the cms-config-url link in public/admin/index.html).
//
// The Ticket Tailor key never leaves the build: only these lists do.
//
// An empty list means "not known": the build had no key or couldn't reach
// Ticket Tailor (previews, local dev; production stops instead, see
// ticket-tailor.ts). The field then stays a text box, as in config.yml.

import { stringify } from "yaml";
import { splitEvents, toListEvents, type EventEntry } from "./event-list";

/** One event in /admin/events.json, in the dropdown's order. */
export interface PickerEvent {
  id: string;
  name: string;
  start: string;
  past: boolean;
}

/** The public event list: upcoming events soonest first, then past ones, most recent first. */
export function pickerEvents(events: EventEntry[], now: Date): PickerEvent[] {
  const byId = new Map(events.map((e) => [e.id, e]));
  const { upcoming, past } = splitEvents(toListEvents(events, [], "gr"), now);
  const entry = (id: string, isPast: boolean): PickerEvent => {
    const e = byId.get(id)!;
    return { id, name: e.data.name, start: e.data.start_iso, past: isPast };
  };
  return [...upcoming.map((e) => entry(e.id, false)), ...past.map((e) => entry(e.id, true))];
}

// Dates as the Greek House's visitors read them, e.g. «Κυρ 25 Απρ 2027».
const DATE = new Intl.DateTimeFormat("el-GR", {
  weekday: "short",
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "Europe/Amsterdam",
});

export const PAST_MARK = "(έγινε / past)";
export const HAS_TEXT_MARK = "✓ έχει ελληνικό κείμενο / has Greek text";
export const NOT_FOUND_MARK = "(δεν βρέθηκε στο Ticket Tailor / not found in Ticket Tailor)";

/** «Κυρ 25 Απρ 2027 · Pascha», plus marks for a past event and one that already has Greek text. */
export function optionLabel(event: PickerEvent, hasGreekText: boolean): string {
  const start = new Date(event.start);
  const parts = [Number.isNaN(start.getTime()) ? "" : DATE.format(start), event.name || event.id].filter(Boolean);
  let label = parts.join(" · ");
  if (event.past) label += ` ${PAST_MARK}`;
  if (hasGreekText) label += ` ${HAS_TEXT_MARK}`;
  return label;
}

export const EVENT_COLLECTIONS = ["event-translations-gr", "event-translations-nl", "event-translations-en"];
export const EVENT_FIELD = "tt_event_id";

export const PICK_HINT =
  "Διάλεξε την εκδήλωση· γράψε μέρος του ονόματος για να τη βρεις. Αν δεν είναι στη λίστα, δεν είναι ακόμα ούτε " +
  "στη σελίδα «Εκδηλώσεις»: δημοσίευσέ τη στο Ticket Tailor, περίμενε λίγα λεπτά και ξαναφόρτωσε το /admin. " +
  "Η εκδήλωση δεν αλλάζει αργότερα: για άλλη εκδήλωση, φτιάξε νέα καταχώρηση. / " +
  "Pick the event; type part of its name to find it. If it isn't in the list, it isn't on the Events page yet " +
  "either: publish it in Ticket Tailor, wait a few minutes and reload /admin. The event can't be changed later: " +
  "for another event, create a new entry.";

interface Field {
  name: string;
  widget: string;
  hint?: string;
  pattern?: unknown;
  options?: { label: string; value: string }[];
  [key: string]: unknown;
}
interface Collection {
  name: string;
  fields?: Field[];
  [key: string]: unknown;
}
export interface DecapConfig {
  collections: Collection[];
  [key: string]: unknown;
}

/**
 * config.yml with the event field as a dropdown, in all three languages, so
 * every entry shows its event's name. Events that already have a Greek entry
 * are marked. An entry whose event left Ticket Tailor keeps its ID as an extra
 * option, so opening it doesn't show an empty field. Without events, the
 * config is returned as it is (a text box).
 */
export function withEventPicker(
  config: DecapConfig,
  events: PickerEvent[],
  greekEntryIds: Iterable<string>,
): DecapConfig {
  if (events.length === 0) return config;
  const withText = new Set(greekEntryIds);
  const known = new Set(events.map((e) => e.id));
  const options = [
    ...events.map((e) => ({ label: optionLabel(e, withText.has(e.id)), value: e.id })),
    ...[...withText]
      .filter((id) => !known.has(id))
      .sort()
      .map((id) => ({ label: `${id} ${NOT_FOUND_MARK}`, value: id })),
  ];
  return {
    ...config,
    collections: config.collections.map((c) =>
      !EVENT_COLLECTIONS.includes(c.name)
        ? c
        : {
            ...c,
            fields: c.fields?.map((f) => {
              if (f.name !== EVENT_FIELD) return f;
              // The text box's ev_… pattern doesn't apply to a choice.
              const { pattern: _pattern, ...rest } = f;
              return {
                ...rest,
                widget: "select",
                options,
                // Dutch and English keep "change this on the Greek entry".
                hint: c.name === "event-translations-gr" ? PICK_HINT : f.hint,
              };
            }),
          },
    ),
  };
}

/** The file /admin loads. Each collection's option list is written out in full, without YAML references. */
export function configYaml(config: DecapConfig): string {
  return (
    "# Generated from public/admin/config.yml when the site is built, with the\n" +
    "# Ticket Tailor events as a dropdown (src/lib/admin-events.ts). Edit config.yml.\n" +
    stringify(config, { lineWidth: 0, aliasDuplicateObjects: false })
  );
}
