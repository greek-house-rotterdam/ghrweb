import { describe, it, expect, vi } from "vitest";
import { isProductionBuild, loadEvents } from "../lib/ticket-tailor";

const PRODUCTION = { WORKERS_CI: "1", WORKERS_CI_BRANCH: "main", TT_API_KEY: "sk_test" };
const PREVIEW = { WORKERS_CI: "1", WORKERS_CI_BRANCH: "cms/news-gr/pascha", TT_API_KEY: "sk_test" };
const LOCAL = { TT_API_KEY: "sk_test" };

const EVENT = {
  id: "ev_1",
  name: "Pascha",
  description: "<p>Easter&nbsp;party</p>",
  start: { iso: "2027-04-25T19:00:00+02:00" },
  url: "https://www.tickettailor.com/events/x/1",
  tickets_available: "true",
};

const ok = (data: unknown[] = [EVENT]) =>
  new Response(JSON.stringify({ data }), { status: 200 });
const status = (code: number) => new Response("oops", { status: code });

function run(env: Record<string, string>, ...responses: (Response | Error)[]) {
  const fetchImpl = vi.fn(async () => {
    const next = responses.shift();
    if (!next) throw new Error("no more responses");
    if (next instanceof Error) throw next;
    return next;
  });
  const sleep = vi.fn(async () => {});
  const warn = vi.fn();
  const result = loadEvents({ env, fetchImpl: fetchImpl as unknown as typeof fetch, sleep, warn });
  return { result, fetchImpl, sleep, warn };
}

describe("events — which build is production", () => {
  it("is production only on Cloudflare's build of main", () => {
    expect(isProductionBuild(PRODUCTION)).toBe(true);
    expect(isProductionBuild(PREVIEW)).toBe(false);
    expect(isProductionBuild(LOCAL)).toBe(false);
    expect(isProductionBuild({ CI: "true", WORKERS_CI_BRANCH: "main" })).toBe(false);
  });

  it("counts a Cloudflare build without a branch name as production (strict)", () => {
    expect(isProductionBuild({ WORKERS_CI: "1" })).toBe(true);
    expect(isProductionBuild({ WORKERS_CI: "1", WORKERS_CI_BRANCH: " " })).toBe(true);
  });
});

describe("events — Ticket Tailor answers", () => {
  it("maps the events", async () => {
    const { result, fetchImpl } = run(PRODUCTION, ok());
    expect(await result).toEqual([
      expect.objectContaining({
        id: "ev_1",
        name: "Pascha",
        description_text: "Easter party",
        start_iso: "2027-04-25T19:00:00+02:00",
        checkout_url: "https://www.tickettailor.com/events/x/1",
        sold_out: false,
      }),
    ]);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it("sends the key as Ticket Tailor documents it: Basic base64(key)", async () => {
    const { result, fetchImpl } = run(PRODUCTION, ok());
    await result;
    const init = (fetchImpl.mock.calls[0] as unknown[])[1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBe(
      "Basic " + Buffer.from("sk_test").toString("base64"),
    );
  });

  it("retries a server error or a network error, then succeeds", async () => {
    const { result, fetchImpl, sleep } = run(PRODUCTION, status(503), new Error("ECONNRESET"), ok());
    expect(await result).toHaveLength(1);
    expect(fetchImpl).toHaveBeenCalledTimes(3);
    expect(sleep).toHaveBeenCalledTimes(2);
  });

  it("does not retry a wrong key", async () => {
    const { result, fetchImpl } = run(PREVIEW, status(401));
    expect(await result).toEqual([]);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });
});

describe("events — Ticket Tailor can't be reached", () => {
  it("production: stops the build after three tries", async () => {
    const { result, fetchImpl } = run(PRODUCTION, status(500), status(502), status(503));
    await expect(result).rejects.toThrow(/Could not read events from Ticket Tailor: HTTP 503/);
    expect(fetchImpl).toHaveBeenCalledTimes(3);
  });

  it("production: stops the build on a wrong key", async () => {
    const { result } = run(PRODUCTION, status(401));
    await expect(result).rejects.toThrow(/HTTP 401/);
  });

  it("preview: warns and builds without events", async () => {
    const { result, warn } = run(PREVIEW, status(500), status(500), status(500));
    expect(await result).toEqual([]);
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("building this preview without events"));
  });

  it("local build: warns and builds without events", async () => {
    const { result, warn } = run(LOCAL, new Error("offline"), new Error("offline"), new Error("offline"));
    expect(await result).toEqual([]);
    expect(warn).toHaveBeenCalledOnce();
  });
});

describe("events — no key", () => {
  it("production: stops the build and says where to set the key", async () => {
    const { result, fetchImpl } = run({ WORKERS_CI: "1", WORKERS_CI_BRANCH: "main" });
    await expect(result).rejects.toThrow(/TT_API_KEY is not set.*Settings → Build → Variables and secrets/);
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("preview and local builds: warn and build without events", async () => {
    for (const env of [{ WORKERS_CI: "1", WORKERS_CI_BRANCH: "feat/x" }, {}]) {
      const { result, warn, fetchImpl } = run(env);
      expect(await result).toEqual([]);
      expect(warn).toHaveBeenCalledOnce();
      expect(fetchImpl).not.toHaveBeenCalled();
    }
  });
});
