import { describe, it, expect, vi } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";
import { parse as parseYaml } from "yaml";

// #126: reopening a translated draft in /admin opened the English file.
// public/admin/open-own-language.js keeps only the draft's own collection
// files before Decap picks one. It is a classic script (it must run between
// decap-cms.js and Decap's start), so the tests load it into a fake window.

const ROOT = join(__dirname, "../..");
const SOURCE = readFileSync(join(ROOT, "public/admin/open-own-language.js"), "utf-8");
const config = parseYaml(readFileSync(join(ROOT, "public/admin/config.yml"), "utf-8"));

type Diff = { path: string; id?: string };
type Data = { collection: string; slug: string; diffs: Diff[] };
interface Api {
  ownFiles: (data: Data, collections: unknown) => Data;
  patch: (cms: unknown) => boolean;
}

function load(cms?: unknown): { api: Api; win: Record<string, unknown> } {
  const win: Record<string, unknown> = { CMS: cms };
  new Function("window", SOURCE)(win);
  return { api: win.ghrOpenOwnLanguage as Api, win };
}

// What Decap 3.16.3 does in processUnpublishedEntry: the shortest `.md` path
// wins, ties keep GitHub's (alphabetical) order.
function decapPick(diffs: Diff[]): string {
  const md = diffs.filter((d) => d.path.endsWith(".md"));
  return [...md].sort((a, b) => a.path.length - b.path.length)[0].path;
}

const draft = (collection: string, type: string): Data => ({
  collection,
  slug: "post",
  // GitHub lists a branch's changed files alphabetically.
  diffs: [
    { path: "public/images/photo.png" },
    { path: `src/content/${type}/en/post.md` },
    { path: `src/content/${type}/gr/post.md` },
    { path: `src/content/${type}/nl/post.md` },
  ],
});

describe("ownFiles", () => {
  const { api } = load();

  it("reproduces the bug: without the fix Decap opens the English file", () => {
    expect(decapPick(draft("news-gr", "news").diffs)).toBe("src/content/news/en/post.md");
  });

  it("keeps the Greek file (and the image) for a Greek draft", () => {
    const out = api.ownFiles(draft("news-gr", "news"), config.collections);
    expect(out.diffs.map((d) => d.path)).toEqual([
      "public/images/photo.png",
      "src/content/news/gr/post.md",
    ]);
    expect(decapPick(out.diffs)).toBe("src/content/news/gr/post.md");
  });

  it("keeps the English file for an English correction", () => {
    const out = api.ownFiles(draft("news-en", "news"), config.collections);
    expect(decapPick(out.diffs)).toBe("src/content/news/en/post.md");
  });

  it("works for every folder collection in config.yml", () => {
    for (const col of config.collections.filter((c: { folder?: string }) => c.folder)) {
      const [type, lang] = [col.folder.split("/")[2], col.folder.split("/")[3]];
      const out = api.ownFiles(draft(col.name, type), config.collections);
      expect(decapPick(out.diffs)).toBe(`src/content/${type}/${lang}/post.md`);
    }
  });

  it("leaves data alone when it can't tell which files belong", () => {
    const unknown = draft("no-such-collection", "news");
    expect(api.ownFiles(unknown, config.collections)).toBe(unknown);
    const settings = { collection: "settings", slug: "contact", diffs: [{ path: "src/data/contact.yml" }] };
    expect(api.ownFiles(settings, config.collections)).toBe(settings);
    const elsewhere = { collection: "news-gr", slug: "x", diffs: [{ path: "src/content/news/en/x.md" }] };
    expect(api.ownFiles(elsewhere, config.collections)).toBe(elsewhere);
  });
});

describe("patching Decap and starting it", () => {
  function fakeCms() {
    const impl = { unpublishedEntry: vi.fn(async () => draft("news-gr", "news")) };
    const github = { init: vi.fn(() => impl) };
    const cms = { getBackend: vi.fn(() => github), init: vi.fn() };
    return { cms, github, impl };
  }

  it("wraps the GitHub backend so drafts open the collection's own file, then starts Decap", async () => {
    const { cms, github } = fakeCms();
    load(cms);
    expect(cms.init).toHaveBeenCalledTimes(1);
    const impl = github.init({ collections: config.collections }, {}) as {
      unpublishedEntry: (a: unknown) => Promise<Data>;
    };
    const data = await impl.unpublishedEntry({ collection: "news-gr", slug: "post" });
    expect(decapPick(data.diffs)).toBe("src/content/news/gr/post.md");
  });

  it("still starts Decap when the GitHub backend is missing", () => {
    const cms = { getBackend: () => undefined, init: vi.fn() };
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    load(cms);
    expect(cms.init).toHaveBeenCalledTimes(1);
    expect(error).toHaveBeenCalled();
    error.mockRestore();
  });

  it("still starts Decap when patching throws", () => {
    const cms = {
      getBackend: () => {
        throw new Error("boom");
      },
      init: vi.fn(),
    };
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    load(cms);
    expect(cms.init).toHaveBeenCalledTimes(1);
    error.mockRestore();
  });
});

describe("index.html loads it in the right order", () => {
  const html = readFileSync(join(ROOT, "public/admin/index.html"), "utf-8");
  const at = (needle: string) => {
    const i = html.indexOf(needle);
    expect(i, needle).toBeGreaterThan(-1);
    return i;
  };

  it("stops Decap's automatic start, loads Decap, then the fix", () => {
    const manual = at("window.CMS_MANUAL_INIT = true");
    const decap = at('src="https://unpkg.com/decap-cms@');
    const fix = at('<script src="/admin/open-own-language.js"></script>');
    expect(manual).toBeLessThan(decap);
    expect(decap).toBeLessThan(fix);
  });

  it("loads the fix as a classic script, not deferred or async", () => {
    expect(html).not.toMatch(/<script[^>]*(defer|async|type="module")[^>]*open-own-language/);
  });
});
