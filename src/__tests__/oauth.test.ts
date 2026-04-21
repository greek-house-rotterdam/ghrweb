import { describe, it, expect, vi, beforeEach } from "vitest";
import handler from "../oauth";

function createEnv() {
  return {
    ASSETS: {
      fetch: vi.fn().mockResolvedValue(new Response("static asset")),
    },
    GITHUB_CLIENT_ID: "test-client-id",
    GITHUB_CLIENT_SECRET: "test-client-secret",
  };
}

describe("OAuth handler — routing", () => {
  let env: ReturnType<typeof createEnv>;

  beforeEach(() => {
    env = createEnv();
    vi.restoreAllMocks();
  });

  it("routes /auth to the auth handler", async () => {
    const req = new Request("https://example.com/auth");
    const res = await handler.fetch(req, env);
    expect(res.headers.get("Content-Type")).toContain("text/html");
    const html = await res.text();
    expect(html).toContain("authorizing:");
  });

  it("routes /callback to the callback handler", async () => {
    const req = new Request("https://example.com/callback");
    const res = await handler.fetch(req, env);
    // Missing code param → 400
    expect(res.status).toBe(400);
  });

  it("falls through to ASSETS.fetch for other paths", async () => {
    const req = new Request("https://example.com/admin/index.html");
    await handler.fetch(req, env);
    expect(env.ASSETS.fetch).toHaveBeenCalledWith(req);
  });

  it("falls through to ASSETS.fetch for root path", async () => {
    const req = new Request("https://example.com/");
    await handler.fetch(req, env);
    expect(env.ASSETS.fetch).toHaveBeenCalledWith(req);
  });
});

describe("OAuth handler — /auth", () => {
  let env: ReturnType<typeof createEnv>;

  beforeEach(() => {
    env = createEnv();
  });

  it("sends the Decap CMS handshake message", async () => {
    const req = new Request("https://example.com/auth");
    const res = await handler.fetch(req, env);
    const html = await res.text();
    expect(html).toContain('postMessage("authorizing:github"');
  });

  it("redirects to GitHub OAuth with correct client_id", async () => {
    const req = new Request("https://example.com/auth");
    const res = await handler.fetch(req, env);
    const html = await res.text();
    expect(html).toContain("github.com/login/oauth/authorize");
    expect(html).toContain("client_id=test-client-id");
  });

  it("includes the callback redirect_uri", async () => {
    const req = new Request("https://example.com/auth");
    const res = await handler.fetch(req, env);
    const html = await res.text();
    expect(html).toContain(
      encodeURIComponent("https://example.com/callback"),
    );
  });

  it("uses default scope repo,user", async () => {
    const req = new Request("https://example.com/auth");
    const res = await handler.fetch(req, env);
    const html = await res.text();
    expect(html).toContain("scope=repo%2Cuser");
  });

  it("respects custom scope parameter", async () => {
    const req = new Request("https://example.com/auth?scope=repo");
    const res = await handler.fetch(req, env);
    const html = await res.text();
    expect(html).toContain("scope=repo");
  });

  it("respects custom provider parameter in handshake", async () => {
    const req = new Request(
      "https://example.com/auth?provider=custom-provider",
    );
    const res = await handler.fetch(req, env);
    const html = await res.text();
    expect(html).toContain("authorizing:custom-provider");
  });
});

describe("OAuth handler — /callback", () => {
  let env: ReturnType<typeof createEnv>;

  beforeEach(() => {
    env = createEnv();
    vi.restoreAllMocks();
  });

  it("returns 400 when code parameter is missing", async () => {
    const req = new Request("https://example.com/callback");
    const res = await handler.fetch(req, env);
    expect(res.status).toBe(400);
    const text = await res.text();
    expect(text).toContain("Missing code");
  });

  it("exchanges code for token on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ access_token: "gho_test_token_123" }), {
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    const req = new Request("https://example.com/callback?code=test-code");
    const res = await handler.fetch(req, env);
    const html = await res.text();

    expect(html).toContain("authorization:github:success:");
    expect(html).toContain("gho_test_token_123");
  });

  it("sends token via postMessage and BroadcastChannel", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ access_token: "gho_abc" }), {
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    const req = new Request("https://example.com/callback?code=test-code");
    const res = await handler.fetch(req, env);
    const html = await res.text();

    expect(html).toContain("window.opener.postMessage");
    expect(html).toContain('BroadcastChannel("decap-cms-auth")');
  });

  it("posts to GitHub token endpoint with correct credentials", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ access_token: "gho_abc" }), {
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", mockFetch);

    const req = new Request("https://example.com/callback?code=my-code");
    await handler.fetch(req, env);

    expect(mockFetch).toHaveBeenCalledWith(
      "https://github.com/login/oauth/access_token",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          client_id: "test-client-id",
          client_secret: "test-client-secret",
          code: "my-code",
        }),
      }),
    );
  });

  it("returns error page when GitHub returns error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: "bad_verification_code",
            error_description: "The code passed is incorrect or expired.",
          }),
          { headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    const req = new Request("https://example.com/callback?code=expired");
    const res = await handler.fetch(req, env);
    const html = await res.text();

    expect(html).toContain("OAuth error");
    expect(html).toContain("The code passed is incorrect or expired.");
    expect(html).not.toContain("authorization:github:success:");
  });

  it("returns error page when token is missing from response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({}), {
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    const req = new Request("https://example.com/callback?code=test");
    const res = await handler.fetch(req, env);
    const html = await res.text();

    expect(html).toContain("OAuth error");
  });
});
