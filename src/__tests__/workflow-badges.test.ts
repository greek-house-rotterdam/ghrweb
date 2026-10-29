import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";
import { parse as parseYaml } from "yaml";
import {
  REPO,
  FILE_COLLECTIONS,
  PREVIEW_PATHS,
  parseCardLink,
  previewUrl,
  requiredChecks,
  checkState,
  summarize,
} from "../../public/admin/workflow-badges.js";

const ROOT = join(__dirname, "../..");
const config = parseYaml(
  readFileSync(join(ROOT, "public/admin/config.yml"), "utf-8"),
);

const PREVIEW = "https://2c499e7e-ghrweb.enosi-ellinon-ollandias.workers.dev";
const REQUIRED = ["Workers Builds: ghrweb", "translate", "verify"];

const run = (name: string, status = "COMPLETED", conclusion: string | null = "SUCCESS") => ({
  __typename: "CheckRun",
  name,
  status,
  conclusion,
});
const status = (context: string, state = "SUCCESS", targetUrl: string | null = null) => ({
  __typename: "StatusContext",
  context,
  state,
  targetUrl,
});
const pr = (checks: object[], mergeStateStatus = "CLEAN") => ({
  url: "https://github.com/greek-house-rotterdam/ghrweb/pull/70",
  headRefName: "cms/news-en/easter-2026",
  mergeStateStatus,
  commits: { nodes: [{ commit: { statusCheckRollup: { contexts: { nodes: checks } } } }] },
});

// A content PR edited in the CMS: every check is a job run on the editor's commit.
const EDITOR_COMMIT = [
  run("translate"),
  run("review"),
  run("verify"),
  run("Workers Builds: ghrweb"),
  status("deploy/preview", "SUCCESS", PREVIEW),
];
// After the translation bot commits, translate and verify arrive as commit
// statuses set by our workflow, not as job runs.
const BOT_COMMIT = [
  run("Workers Builds: ghrweb"),
  status("translate"),
  status("verify"),
  status("deploy/preview", "SUCCESS", PREVIEW),
];

describe("workflow badges — matching a card to its pull request", () => {
  it("reads the collection, slug and branch from the card's link", () => {
    expect(parseCardLink("#/collections/news-en/entries/easter-2026?ref=workflow")).toEqual({
      collection: "news-en",
      slug: "easter-2026",
      branch: "cms/news-en/easter-2026",
    });
  });

  it("handles a Greek slug, raw or percent-encoded", () => {
    const slug = "καλο-χειμωνα";
    const expected = { collection: "news-gr", slug, branch: `cms/news-gr/${slug}` };
    expect(parseCardLink(`#/collections/news-gr/entries/${slug}`)).toEqual(expected);
    expect(
      parseCardLink(`#/collections/news-gr/entries/${encodeURIComponent(slug)}`),
    ).toEqual(expected);
  });

  it("ignores links that aren't to an entry", () => {
    expect(parseCardLink("#/collections/news-gr")).toBeNull();
    expect(parseCardLink("#/collections/news-gr/new")).toBeNull();
    expect(parseCardLink("#/workflow")).toBeNull();
    expect(parseCardLink(null)).toBeNull();
  });

  it("reads the same repo as the CMS", () => {
    expect(REPO).toBe(config.backend.repo);
  });
});

describe("workflow badges — preview link", () => {
  it("links to the entry's page on the preview", () => {
    expect(previewUrl(PREVIEW, "news-en", "easter-2026")).toBe(`${PREVIEW}/en/news/easter-2026`);
    expect(previewUrl(`${PREVIEW}/`, "faq-nl", "03-greek")).toBe(`${PREVIEW}/nl/faq`);
    expect(previewUrl(PREVIEW, "event-translations-gr", "pascha")).toBe(
      `${PREVIEW}/gr/events/pascha`,
    );
  });

  it("encodes a Greek slug", () => {
    expect(previewUrl(PREVIEW, "news-gr", "καλο-χειμωνα")).toBe(
      `${PREVIEW}/gr/news/${encodeURIComponent("καλο-χειμωνα")}`,
    );
  });

  it("falls back to the preview's home page for an unknown collection", () => {
    expect(previewUrl(PREVIEW, "other-gr", "x")).toBe(PREVIEW);
  });

  // The badge must open the same page as Decap's own View Preview button.
  for (const collection of config.collections.filter((c: { folder?: string }) => c.folder)) {
    it(`matches the preview_path of ${collection.name}`, () => {
      const dash = collection.name.lastIndexOf("-");
      const type = collection.name.slice(0, dash) as keyof typeof PREVIEW_PATHS;
      const lang = collection.name.slice(dash + 1);
      expect(PREVIEW_PATHS[type]).toBeDefined();
      expect(`${lang}/${PREVIEW_PATHS[type].replace("{slug}", "{{slug}}")}`).toBe(
        collection.preview_path,
      );
    });
  }
});

// Decap 3.16.3 links a files-collection card like any other:
// #/collections/<collection>/entries/<file name>?ref=workflow, on the branch
// cms/<collection>/<file name>. Checked in decap-cms@3.16.3/dist/decap-cms.js.
describe("workflow badges — site settings cards", () => {
  it("matches a settings card to its branch", () => {
    expect(parseCardLink("#/collections/settings/entries/board?ref=workflow")).toEqual({
      collection: "settings",
      slug: "board",
      branch: "cms/settings/board",
    });
  });

  it("opens the preview's home page, since a settings file has no page of its own", () => {
    expect(previewUrl(PREVIEW, "settings", "contact")).toBe(PREVIEW);
    expect(previewUrl(`${PREVIEW}/`, "settings", "forms")).toBe(PREVIEW);
  });

  it("knows every files collection in config.yml", () => {
    const files = config.collections
      .filter((c: { files?: unknown }) => c.files)
      .map((c: { name: string }) => c.name);
    expect(FILE_COLLECTIONS).toEqual(files);
  });
});

describe("workflow badges — check states", () => {
  it("reads job runs", () => {
    expect(checkState(run("verify"))).toBe("ok");
    expect(checkState(run("verify", "COMPLETED", "SKIPPED"))).toBe("ok");
    expect(checkState(run("verify", "IN_PROGRESS", null))).toBe("pending");
    expect(checkState(run("verify", "QUEUED", null))).toBe("pending");
    expect(checkState(run("verify", "COMPLETED", "FAILURE"))).toBe("fail");
    expect(checkState(run("verify", "COMPLETED", "CANCELLED"))).toBe("fail");
  });

  it("reads commit statuses", () => {
    expect(checkState(status("verify"))).toBe("ok");
    expect(checkState(status("verify", "PENDING"))).toBe("pending");
    expect(checkState(status("verify", "FAILURE"))).toBe("fail");
    expect(checkState(status("verify", "ERROR"))).toBe("fail");
  });

  it("reads the required checks from GitHub's branch rules", () => {
    const rules = [
      { type: "pull_request", parameters: {} },
      {
        type: "required_status_checks",
        parameters: {
          required_status_checks: [
            { context: "Workers Builds: ghrweb", integration_id: 85455 },
            { context: "translate" },
            { context: "verify" },
          ],
        },
      },
    ];
    expect(requiredChecks(rules)).toEqual(REQUIRED);
  });
});

describe("workflow badges — what a card shows", () => {
  it("all green on the editor's commit", () => {
    expect(summarize(pr(EDITOR_COMMIT), REQUIRED)).toEqual({
      url: "https://github.com/greek-house-rotterdam/ghrweb/pull/70",
      preview: { state: "ok", url: PREVIEW },
      translation: "ok",
      checks: "ok",
    });
  });

  it("all green on the translation bot's commit", () => {
    const summary = summarize(pr(BOT_COMMIT), REQUIRED);
    expect(summary.translation).toBe("ok");
    expect(summary.checks).toBe("ok");
  });

  it("everything waiting before any check has started", () => {
    expect(summarize(pr([], "BLOCKED"), REQUIRED)).toMatchObject({
      preview: { state: "pending" },
      translation: "pending",
      checks: "pending",
    });
  });

  it("checks waiting while a required check runs", () => {
    const checks = [run("translate"), run("verify"), run("Workers Builds: ghrweb", "IN_PROGRESS", null)];
    expect(summarize(pr(checks, "BLOCKED"), REQUIRED).checks).toBe("pending");
  });

  it("checks waiting when GitHub blocks the merge, even if every visible check passed", () => {
    // Workers Builds hasn't reported yet, so it isn't in the list at all.
    const checks = [run("translate"), run("verify")];
    expect(summarize(pr(checks, "BLOCKED"), REQUIRED).checks).toBe("pending");
  });

  it("checks failed when a required check failed", () => {
    const checks = [run("translate"), run("verify", "COMPLETED", "FAILURE"), run("Workers Builds: ghrweb")];
    expect(summarize(pr(checks, "BLOCKED"), REQUIRED).checks).toBe("fail");
  });

  it("ignores a failed check that isn't required", () => {
    const checks = [...EDITOR_COMMIT, run("review", "COMPLETED", "FAILURE")];
    expect(summarize(pr(checks, "UNSTABLE"), REQUIRED).checks).toBe("ok");
  });

  it("counts every check when the required list couldn't be read", () => {
    const checks = [...EDITOR_COMMIT, run("review", "COMPLETED", "FAILURE")];
    expect(summarize(pr(checks, "UNSTABLE"), null).checks).toBe("fail");
  });

  it("shows a conflict", () => {
    expect(summarize(pr(EDITOR_COMMIT, "DIRTY"), REQUIRED).checks).toBe("conflict");
  });

  it("shows a failed translation", () => {
    const checks = [run("translate", "COMPLETED", "FAILURE")];
    expect(summarize(pr(checks, "BLOCKED"), REQUIRED).translation).toBe("fail");
  });

  it("keeps the preview waiting until its status succeeds", () => {
    const building = [run("translate"), status("deploy/preview", "PENDING")];
    expect(summarize(pr(building), REQUIRED).preview).toEqual({ state: "pending", url: null });
  });
});
