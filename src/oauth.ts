interface Env {
  ASSETS: { fetch: (request: Request) => Promise<Response> };
  GITHUB_CLIENT_ID: string;
  GITHUB_CLIENT_SECRET: string;
}

const GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize";
const GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/auth") {
      return handleAuth(url, env);
    }

    if (url.pathname === "/callback") {
      return handleCallback(url, env);
    }

    return env.ASSETS.fetch(request);
  },
};

function handleAuth(url: URL, env: Env): Response {
  const scope = url.searchParams.get("scope") || "repo,user";
  const provider = url.searchParams.get("provider") || "github";
  const params = new URLSearchParams({
    client_id: env.GITHUB_CLIENT_ID,
    redirect_uri: `${url.origin}/callback`,
    scope,
  });

  const redirectUrl = `${GITHUB_AUTHORIZE_URL}?${params}`;

  // Decap CMS expects a handshake message ("authorizing:<provider>") before
  // it starts listening for the auth token. We must send this from the popup
  // before redirecting to GitHub.
  return new Response(
    `<!doctype html><html><body>
<script>
(function() {
  window.opener.postMessage("authorizing:${provider}", window.location.origin);
  window.location.href = ${JSON.stringify(redirectUrl)};
})();
</script></body></html>`,
    { headers: { "Content-Type": "text/html;charset=utf-8" } },
  );
}

async function handleCallback(url: URL, env: Env): Promise<Response> {
  const code = url.searchParams.get("code");

  if (!code) {
    return new Response("Missing code parameter", { status: 400 });
  }

  const tokenResponse = await fetch(GITHUB_TOKEN_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
    }),
  });

  const data = (await tokenResponse.json()) as {
    access_token?: string;
    error?: string;
    error_description?: string;
  };

  if (data.error || !data.access_token) {
    const message = data.error_description || data.error || "Unknown error";
    return new Response(authResultPage("error", message), {
      headers: { "Content-Type": "text/html;charset=utf-8" },
    });
  }

  return new Response(authResultPage("success", data.access_token), {
    headers: { "Content-Type": "text/html;charset=utf-8" },
  });
}

function authResultPage(status: "success" | "error", content: string): string {
  const escaped = JSON.stringify(content);

  if (status === "error") {
    return `<!doctype html><html><body>
<p>OAuth error: ${content}</p>
</body></html>`;
  }

  // After GitHub redirects back, window.opener is often null due to
  // Cross-Origin-Opener-Policy headers. We try multiple delivery methods:
  // 1. window.opener.postMessage (works when COOP doesn't block it)
  // 2. BroadcastChannel (works same-origin across browsing contexts)
  // 3. localStorage + storage event (most reliable cross-window fallback)
  return `<!doctype html><html><body>
<p>Authenticating...</p>
<script>
(function() {
  var msg = "authorization:github:success:" + JSON.stringify({ token: ${escaped}, provider: "github" });

  // Deliver token to admin page via window.opener (primary)
  // and BroadcastChannel (fallback for COOP restrictions)
  try {
    if (window.opener && !window.opener.closed) {
      window.opener.postMessage(msg, window.location.origin);
    }
  } catch(e) {}

  try {
    var channel = new BroadcastChannel("decap-cms-auth");
    channel.postMessage(msg);
    setTimeout(function() { channel.close(); }, 2000);
  } catch(e) {}

  setTimeout(function() { window.close(); }, 1000);
})();
</script></body></html>`;
}
