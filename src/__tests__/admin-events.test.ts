// Choosing the event in /admin (#105). See src/lib/admin-events.ts.
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "fs";
import { join } from "path";
import { parse } from "yaml";
import {
  EVENT_COLLECTIONS,
  configYaml,
  HAS_TEXT_MARK,
  NOT_FOUND_MARK,
  PAST_MARK,
  PICK_HINT,
  optionLabel,
  pickerEvents,
  withEventPicker,
  type DecapConfig,
  type PickerEvent,
} from "../lib/admin-events";
import type { EventEntry } from "../lib/event-list";

const ROOT = join(__dirname, "../..");
const readConfig = (): DecapConfig =>
  parse(readFileSync(join(ROOT, "public/admin/config.yml"), "utf-8"));

const GREEK_THEN_ENGLISH = /^[^/]*[Ͱ-Ͽἀ-῿].* \/ .*[A-Za-z]/s;

function event(id: string, name: string, start_iso: string, end_iso?: string): EventEntry {
  return {
    id,
    data: { name, description_text: "", start_iso, end_iso, sold_out: false },
  };
}

const NOW = new Date("2026-11-17T12:00:00Z");
const EVENTS = [
  event("ev_old", "Πάσχα 2026", "2026-04-12T19:00:00+02:00"),
  event("ev_late", "Χριστούγεννα", "2026-12-19T19:00:00+01:00"),
  event("ev_recent", "Οκτώβρης", "2026-10-28T19:00:00+01:00"),
  event("ev_soon", "Board games", "2026-11-20T19:00:00+01:00"),
  // Started yesterday, ends tomorrow: still upcoming, like on the events page.
  event("ev_running", "Έκθεση", "2026-11-16T10:00:00+01:00", "2026-11-18T18:00:00+01:00"),
];

describe("admin events — the public list", () => {
  it("lists upcoming events soonest first, then past ones most recent first", () => {
    expect(pickerEvents(EVENTS, NOW).map((e) => [e.id, e.past])).toEqual([
      ["ev_running", false],
      ["ev_soon", false],
      ["ev_late", false],
      ["ev_recent", true],
      ["ev_old", true],
    ]);
  });

  it("keeps only the ID, name and start: nothing that isn't on the events pages already", () => {
    expect(pickerEvents([EVENTS[1]], NOW)).toEqual([
      { id: "ev_late", name: "Χριστούγεννα", start: "2026-12-19T19:00:00+01:00", past: false },
    ]);
  });
});

describe("admin events — dropdown labels", () => {
  const e: PickerEvent = { id: "ev_1", name: "Pascha", start: "2027-04-25T19:00:00+02:00", past: false };

  it("shows the Greek date and the name", () => {
    expect(optionLabel(e, false)).toBe("Κυρ 25 Απρ 2027 · Pascha");
  });

  it("uses the date in Rotterdam, not the build server's", () => {
    expect(optionLabel({ ...e, start: "2026-12-12T23:30:00Z" }, false)).toMatch(/^Κυρ 13 Δεκ 2026 · /);
  });

  it("marks past events and events that already have Greek text", () => {
    expect(optionLabel({ ...e, past: true }, true)).toBe(`Κυρ 25 Απρ 2027 · Pascha ${PAST_MARK} ${HAS_TEXT_MARK}`);
  });

  it("falls back to the name, or the ID, when a date or name is missing", () => {
    expect(optionLabel({ ...e, start: "" }, false)).toBe("Pascha");
    expect(optionLabel({ ...e, start: "", name: "" }, false)).toBe("ev_1");
  });

  it("writes every mark and the hint Greek / English, like all /admin texts", () => {
    for (const text of [PAST_MARK, HAS_TEXT_MARK, NOT_FOUND_MARK, PICK_HINT]) {
      expect(text).toMatch(GREEK_THEN_ENGLISH);
    }
  });
});

describe("admin events — the configuration /admin loads", () => {
  const events = pickerEvents(EVENTS, NOW);

  it("keeps the text box when there is no event list (no key, Ticket Tailor unreachable)", () => {
    const config = readConfig();
    expect(withEventPicker(config, [], ["ev_1"])).toBe(config);
  });

  it("turns the event field into a dropdown in all three languages", () => {
    const result = withEventPicker(readConfig(), events, []);
    for (const name of EVENT_COLLECTIONS) {
      const field = result.collections.find((c) => c.name === name)!.fields!.find((f) => f.name === "tt_event_id")!;
      expect(field.widget).toBe("select");
      expect(field.options!.map((o) => o.value)).toEqual(events.map((e) => e.id));
      expect(field.required).not.toBe(false);
    }
  });

  it("gives the Greek field the picking hint; Dutch and English still say to change it on the Greek", () => {
    const result = withEventPicker(readConfig(), events, []);
    const hint = (name: string) =>
      result.collections.find((c) => c.name === name)!.fields!.find((f) => f.name === "tt_event_id")!.hint;
    expect(hint("event-translations-gr")).toBe(PICK_HINT);
    expect(hint("event-translations-nl")).toMatch(/^Αλλάζει στην ελληνική καταχώρηση/);
    expect(hint("event-translations-en")).toMatch(/^Αλλάζει στην ελληνική καταχώρηση/);
  });

  it("marks events with a Greek entry, and keeps an entry's ID that Ticket Tailor no longer has", () => {
    const result = withEventPicker(readConfig(), events, ["ev_soon", "ev_gone"]);
    const options = result.collections
      .find((c) => c.name === "event-translations-gr")!
      .fields!.find((f) => f.name === "tt_event_id")!.options!;
    expect(options.find((o) => o.value === "ev_soon")!.label).toContain(HAS_TEXT_MARK);
    expect(options.find((o) => o.value === "ev_late")!.label).not.toContain(HAS_TEXT_MARK);
    expect(options.at(-1)).toEqual({ value: "ev_gone", label: `ev_gone ${NOT_FOUND_MARK}` });
  });

  it("changes nothing else", () => {
    const before = readConfig();
    const after = withEventPicker(before, events, []);
    const strip = (c: DecapConfig) => ({
      ...c,
      collections: c.collections.map((col) =>
        EVENT_COLLECTIONS.includes(col.name)
          ? { ...col, fields: col.fields!.filter((f) => f.name !== "tt_event_id") }
          : col,
      ),
    });
    expect(strip(after)).toEqual(strip(before));
  });

  it("survives being written as YAML and read back (as Decap reads it)", () => {
    const result = withEventPicker(readConfig(), events, ["ev_gone"]);
    const text = configYaml(result);
    expect(parse(text)).toEqual(result);
    // Each collection's list written out in full: no YAML references (&a1 / *a1).
    expect(text).not.toMatch(/[&*]a\d/);
    expect(text.startsWith("# Generated from public/admin/config.yml")).toBe(true);
  });

  it("writes the configuration unchanged when there are no events", () => {
    expect(parse(configYaml(withEventPicker(readConfig(), [], [])))).toEqual(readConfig());
  });

  it("is what /admin loads: index.html points Decap at the generated file", () => {
    const html = readFileSync(join(ROOT, "public/admin/index.html"), "utf-8");
    expect(html).toContain('<link href="/admin/config-with-events.yml" type="text/yaml" rel="cms-config-url" />');
    expect(existsSync(join(ROOT, "src/pages/admin/config-with-events.yml.ts"))).toBe(true);
    // The verify check reads this one from the live site.
    expect(existsSync(join(ROOT, "src/pages/admin/events.json.ts"))).toBe(true);
  });
});
