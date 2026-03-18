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
<script>
(function() {
  if (window.opener) {
    window.opener.postMessage(
      "authorization:github:error:" + JSON.stringify({ message: ${escaped} }),
      "*"
    );
    setTimeout(function() { window.close(); }, 500);
  }
})();
</script></body></html>`;
  }

  return `<!doctype html><html><body>
<p>Authenticating...</p>
<script>
(function() {
  if (window.opener) {
    window.opener.postMessage(
      "authorization:github:success:" + JSON.stringify({ token: ${escaped}, provider: "github" }),
      "*"
    );
    setTimeout(function() { window.close(); }, 500);
  } else {
    document.body.innerHTML = "<p>Error: popup lost connection to the admin page. Close this window and try again.</p>";
  }
})();
</script></body></html>`;
}
