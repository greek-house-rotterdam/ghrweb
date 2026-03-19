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
  const params = new URLSearchParams({
    client_id: env.GITHUB_CLIENT_ID,
    redirect_uri: `${url.origin}/callback`,
    scope,
  });

  return Response.redirect(`${GITHUB_AUTHORIZE_URL}?${params}`, 302);
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
<h3>OAuth Debug</h3>
<ul id="log"></ul>
<script>
(function() {
  var log = document.getElementById("log");
  function addLog(text) {
    var li = document.createElement("li");
    li.textContent = text;
    log.appendChild(li);
  }

  var msg = "authorization:github:success:" + JSON.stringify({ token: ${escaped}, provider: "github" });
  addLog("Token obtained successfully");

  // Method 1: Direct opener postMessage
  try {
    if (window.opener && !window.opener.closed) {
      window.opener.postMessage(msg, window.location.origin);
      addLog("Method 1 (window.opener): SENT");
    } else {
      addLog("Method 1 (window.opener): " + (window.opener ? "closed" : "null"));
    }
  } catch(e) { addLog("Method 1 (window.opener): ERROR " + e.message); }

  // Method 2: BroadcastChannel
  try {
    var channel = new BroadcastChannel("decap-cms-auth");
    channel.postMessage(msg);
    addLog("Method 2 (BroadcastChannel): SENT");
    setTimeout(function() { channel.close(); }, 5000);
  } catch(e) { addLog("Method 2 (BroadcastChannel): ERROR " + e.message); }

  // Method 3: localStorage storage event
  try {
    localStorage.setItem("decap-cms-auth", msg);
    addLog("Method 3 (localStorage): SET");
    setTimeout(function() { localStorage.removeItem("decap-cms-auth"); }, 3000);
  } catch(e) { addLog("Method 3 (localStorage): ERROR " + e.message); }

  addLog("Is this a popup? " + (window.opener !== null));
  addLog("Origin: " + window.location.origin);
})();
</script></body></html>`;
}
