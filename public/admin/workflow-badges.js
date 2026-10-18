// Badges on the Workflow board: for each card, a link to its preview and the
// state of its translation and checks, read from the card's pull request.
//
// Decap has no way to add things to its cards, so this script finds the cards
// on the page and adds a row of badges to each. It depends on how Decap draws
// the board: a card is a <div> whose first child is a link to the entry. After
// upgrading Decap (see index.html), open the Workflow board on the preview and
// check that the badges still appear. If they break, only the badges go
// missing; the board itself keeps working.

export const REPO = "greek-house-rotterdam/ghrweb";
const API = "https://api.github.com";
const REFRESH_MS = 60_000;
// The shortest time between two reads of GitHub, outside the regular refresh.
const MIN_GAP_MS = 10_000;

// Each content type's preview_path in config.yml, without the language.
export const PREVIEW_PATHS = {
  news: "news/{slug}",
  "event-translations": "events/{slug}",
  activities: "activities/{slug}",
  faq: "faq",
  resources: "resources",
};

// "#/collections/news-gr/entries/easter-2026?ref=workflow" →
// { collection: "news-gr", slug: "easter-2026", branch: "cms/news-gr/easter-2026" }
// Decap names the branch of each unpublished entry cms/<collection>/<slug>.
export function parseCardLink(href) {
  const match = /^#\/collections\/([^/?#]+)\/entries\/([^?#]+)/.exec(href || "");
  if (!match) return null;
  const collection = decode(match[1]);
  const slug = decode(match[2]);
  return { collection, slug, branch: `cms/${collection}/${slug}` };
}

function decode(text) {
  try {
    return decodeURIComponent(text);
  } catch {
    return text;
  }
}

// The entry's page on the preview site, like Decap's own "View Preview".
export function previewUrl(base, collection, slug) {
  const dash = collection.lastIndexOf("-");
  const path = PREVIEW_PATHS[collection.slice(0, dash)];
  const root = base.replace(/\/+$/, "");
  if (path === undefined) return root;
  const lang = collection.slice(dash + 1);
  return `${root}/${lang}/${path.replace("{slug}", encodeURIComponent(slug))}`;
}

// Names of the checks that must pass before a pull request can merge into
// main, from GitHub's "rules for a branch" response.
export function requiredChecks(rules) {
  return rules
    .filter((rule) => rule.type === "required_status_checks")
    .flatMap((rule) => rule.parameters.required_status_checks.map((c) => c.context));
}

// A check reaches GitHub either as a check run (a job in a workflow, or an app
// such as Cloudflare) or as a commit status (what our workflows set on the
// translation bot's commits). Both become "ok", "pending" or "fail".
function checkName(check) {
  return check.__typename === "CheckRun" ? check.name : check.context;
}

export function checkState(check) {
  if (check.__typename === "CheckRun") {
    if (check.status !== "COMPLETED") return "pending";
    return ["SUCCESS", "NEUTRAL", "SKIPPED"].includes(check.conclusion) ? "ok" : "fail";
  }
  if (check.state === "SUCCESS") return "ok";
  return ["PENDING", "EXPECTED"].includes(check.state) ? "pending" : "fail";
}

function worst(states) {
  if (states.includes("fail")) return "fail";
  if (states.includes("pending")) return "pending";
  return "ok";
}

// What the badges show for one pull request (a node of QUERY below).
// `required` is the list from requiredChecks(), or null if it couldn't be read.
export function summarize(pr, required) {
  const checks = pr.commits?.nodes?.[0]?.commit?.statusCheckRollup?.contexts?.nodes ?? [];
  // Decap finds the preview the same way: a commit status whose name
  // contains "deploy" (ours is deploy/preview).
  const isPreview = (c) => c.__typename === "StatusContext" && c.context.includes("deploy");
  const preview = checks.find(isPreview);
  const translate = checks.filter((c) => checkName(c) === "translate");
  const others = checks.filter(
    (c) =>
      !isPreview(c) &&
      checkName(c) !== "translate" &&
      (required === null || required.includes(checkName(c))),
  );

  // The Checks badge answers one question: will Publish work? A required
  // check may not have started yet, so we can't see it; GitHub's own merge
  // state can, and a blocked pull request is never shown as ready.
  let state = worst(others.map(checkState));
  if (pr.mergeStateStatus === "DIRTY") state = "conflict";
  else if (state === "ok" && ["BLOCKED", "UNKNOWN"].includes(pr.mergeStateStatus)) state = "pending";

  return {
    url: pr.url,
    preview: preview
      ? { state: checkState(preview), url: preview.targetUrl }
      : { state: "pending", url: null },
    translation: translate.length ? worst(translate.map(checkState)) : "pending",
    checks: state,
  };
}

const QUERY = `query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: OPEN, first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        url
        headRefName
        mergeStateStatus
        commits(last: 1) { nodes { commit { statusCheckRollup { contexts(first: 50) { nodes {
          __typename
          ... on CheckRun { name status conclusion }
          ... on StatusContext { context state targetUrl }
        } } } } } }
      }
    }
  }
}`;

const TEXT = {
  preview: {
    ok: ["Preview ↗", "Open this entry on the preview site."],
    pending: ["Preview …", "The preview is being built. This takes a few minutes."],
    fail: ["Preview ✗", "The preview could not be built. Open Details."],
  },
  translation: {
    ok: ["Translation ✓", "The translation step is done."],
    pending: ["Translation …", "The translation step is still running."],
    fail: ["Translation ✗", "The translation step failed. Open Details."],
  },
  checks: {
    ok: ["Checks ✓", "All checks passed. Publish will work."],
    pending: ["Checks …", "Checks are still running. Wait before you publish."],
    fail: ["Checks ✗", "A check failed, so Publish won't work. Open Details."],
    conflict: ["Conflict ✗", "This edit conflicts with another change. Ask the web team."],
  },
  details: ["Details ↗", "Open the pull request on GitHub."],
};

const STYLE = `
.ghr-badges { display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 8px 0; }
@media (min-width: 800px) { .ghr-badges { padding: 12px 18px 0; } }
.ghr-badge {
  font-size: 12px; line-height: 18px; padding: 1px 8px; border-radius: 9px;
  white-space: nowrap; text-decoration: none;
}
a.ghr-badge:hover { text-decoration: underline; }
.ghr-ok { background: #e3f4e8; color: #1d6b35; }
.ghr-pending { background: #eceef3; color: #555b69; }
.ghr-fail, .ghr-conflict { background: #fdece8; color: #b42318; }
.ghr-link { background: #e6eefc; color: #1d4fbf; }
`;

function badge([text, title], kind, href) {
  const el = document.createElement(href ? "a" : "span");
  el.className = `ghr-badge ghr-${kind}`;
  el.textContent = text;
  el.title = title;
  if (href) {
    el.href = href;
    el.target = "_blank";
    el.rel = "noopener noreferrer";
  }
  return el;
}

function renderRow(summary, card) {
  const row = document.createElement("div");
  row.className = "ghr-badges";
  row.dataset.sig = JSON.stringify([summary, card.branch]);
  const { state, url } = summary.preview;
  // Only link to an https address: a commit status's link is set by whoever
  // wrote the status.
  const href =
    state === "ok" && /^https:\/\//.test(url ?? "")
      ? previewUrl(url, card.collection, card.slug)
      : null;
  const preview = href ? "ok" : state === "ok" ? "pending" : state;
  row.append(
    badge(TEXT.preview[preview], preview, href),
    badge(TEXT.translation[summary.translation], summary.translation),
    badge(TEXT.checks[summary.checks], summary.checks),
    badge(TEXT.details, "link", summary.url),
  );
  return row;
}

const state = {
  byBranch: new Map(),
  required: undefined,
  lastFetch: 0,
  running: false,
  timer: null,
  asked: new Set(),
  warned: false,
};

function onWorkflowPage() {
  return location.hash.startsWith("#/workflow");
}

// Decap keeps the logged-in editor's GitHub token in localStorage.
function readToken() {
  try {
    return JSON.parse(localStorage.getItem("decap-cms-user") || "null")?.token || null;
  } catch {
    return null;
  }
}

async function github(token, path, init = {}) {
  const res = await fetch(API + path, {
    ...init,
    headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" },
  });
  if (!res.ok) throw new Error(`GitHub answered ${res.status} for ${path}`);
  return res.json();
}

async function refresh() {
  const token = readToken();
  if (!token || state.running) return;
  state.running = true;
  state.lastFetch = Date.now();
  try {
    if (state.required === undefined) {
      state.required = await github(token, `/repos/${REPO}/rules/branches/main`).then(
        requiredChecks,
        () => undefined, // Try again next time; meanwhile count every check.
      );
    }
    const [owner, name] = REPO.split("/");
    const body = await github(token, "/graphql", {
      method: "POST",
      body: JSON.stringify({ query: QUERY, variables: { owner, name } }),
    });
    if (body.errors) throw new Error(body.errors[0].message);
    const prs = body.data.repository.pullRequests.nodes;
    state.byBranch = new Map(
      prs.map((pr) => [pr.headRefName, summarize(pr, state.required ?? null)]),
    );
    decorate();
  } catch (error) {
    if (!state.warned) console.warn("Workflow badges: could not read GitHub.", error);
    state.warned = true;
  } finally {
    state.running = false;
  }
}

function refreshSoon() {
  if (state.timer) return;
  const wait = Math.max(0, state.lastFetch + MIN_GAP_MS - Date.now());
  state.timer = setTimeout(() => {
    state.timer = null;
    refresh();
  }, wait);
}

function decorate() {
  if (!onWorkflowPage()) return;
  let unseen = false;
  for (const link of document.querySelectorAll('a[href^="#/collections/"]')) {
    const card = parseCardLink(link.getAttribute("href"));
    if (!card) continue;
    const summary = state.byBranch.get(card.branch);
    if (!summary) {
      // A card we have no pull request for, most likely an entry that was
      // just saved. Read GitHub again, once per card.
      if (!state.asked.has(card.branch)) unseen = true;
      state.asked.add(card.branch);
      continue;
    }
    const row = renderRow(summary, card);
    const old = link.parentElement.querySelector(":scope > .ghr-badges");
    if (old?.dataset.sig === row.dataset.sig) continue;
    // Above the link, not below it: the card's Delete and Publish buttons
    // sit invisibly over its bottom edge until you hover.
    if (old) old.replaceWith(row);
    else link.before(row);
  }
  if (unseen) refreshSoon();
}

function start() {
  const style = document.createElement("style");
  style.textContent = STYLE;
  document.head.append(style);

  let frame = 0;
  new MutationObserver(() => {
    if (frame || !onWorkflowPage()) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      decorate();
    });
  }).observe(document.body, { childList: true, subtree: true });

  const visible = () => onWorkflowPage() && document.visibilityState === "visible";
  setInterval(() => visible() && refresh(), REFRESH_MS);
  const soon = () => visible() && refreshSoon();
  window.addEventListener("hashchange", soon);
  document.addEventListener("visibilitychange", soon);
  soon();
}

if (typeof document !== "undefined") start();
