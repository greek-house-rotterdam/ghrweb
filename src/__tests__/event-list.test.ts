import { describe, it, expect } from "vitest";
import { nextEvents, splitEvents, toListEvents, type EventEntry, type ListEvent } from "../lib/event-list";

function entry(id: string, start: string, end?: string, extra: Partial<EventEntry["data"]> = {}): EventEntry {
  return {
    id,
    data: { name: `Event ${id}`, description_text: `About ${id}`, start_iso: start, end_iso: end, sold_out: false, ...extra },
  };
}

const NOW = new Date("2026-11-15T12:00:00Z");
const ids = (events: ListEvent[]) => events.map((e) => e.id);

describe("toListEvents", () => {
  it("uses the translation in the page's language, and Ticket Tailor's text otherwise", () => {
    const overlays = [
      { data: { tt_event_id: "a", lang: "en", title: "Title EN", description: "About EN" } },
      { data: { tt_event_id: "a", lang: "nl", title: "Titel NL" } },
    ];
    const [a, b] = toListEvents([entry("a", "2026-12-01T19:00:00Z"), entry("b", "2026-12-02T19:00:00Z")], overlays, "en");
    expect([a.title, a.description]).toEqual(["Title EN", "About EN"]);
    expect([b.title, b.description]).toEqual(["Event b", "About b"]);
  });

  it("treats an event without a readable start as long past", () => {
    const [e] = toListEvents([entry("x", "")], [], "gr");
    expect(splitEvents([e], NOW).past).toHaveLength(1);
  });
});

describe("splitEvents", () => {
  const events = toListEvents(
    [
      entry("past-old", "2026-05-21T18:00:00Z"),
      entry("future-near", "2026-11-21T19:00:00Z"),
      entry("past-recent", "2026-11-14T19:00:00Z"),
      entry("future-far", "2026-12-11T19:00:00Z"),
      // Started this morning, ends tonight: still upcoming until it ends.
      entry("running", "2026-11-15T09:00:00Z", "2026-11-15T22:00:00Z"),
    ],
    [],
    "gr",
  );

  it("puts events that haven't ended in upcoming, newest first", () => {
    expect(ids(splitEvents(events, NOW).upcoming)).toEqual(["future-far", "future-near", "running"]);
  });

  it("puts ended events in past, newest first", () => {
    expect(ids(splitEvents(events, NOW).past)).toEqual(["past-recent", "past-old"]);
  });

  it("counts an event without an end time as ended once it starts", () => {
    const [e] = toListEvents([entry("no-end", "2026-11-15T11:00:00Z")], [], "gr");
    expect(splitEvents([e], NOW).past).toHaveLength(1);
  });
});

describe("nextEvents", () => {
  it("takes the soonest upcoming events and shows them newest first", () => {
    const upcoming = toListEvents(
      ["2027-03-01", "2026-12-11", "2026-11-21", "2027-01-10"].map((d, i) => entry(`e${i}`, `${d}T19:00:00Z`)),
      [],
      "gr",
    );
    expect(ids(nextEvents(upcoming, 3))).toEqual(["e3", "e1", "e2"]);
  });
});
