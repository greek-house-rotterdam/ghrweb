# Cloudflare Ownership & Operations — GHR

> Concise implementation note for Cloudflare setup and governance.

---

## Decisions

1. **Use an organization-owned Cloudflare account** (shared org email) as the primary owner.
2. **Use personal Cloudflare users for daily work** (developer/admin actions).
3. **Keep the shared org login as break-glass only** (recovery/continuity), not daily operations.
4. **Keep billing under the organization identity** (payment method and invoices tied to org ownership).
5. **Developer role:** `@PanoEvJ` is assigned **Super Admin** on Cloudflare (personal user), while ownership remains with the organization account.

## Why (minimal rationale)

- Avoids single-person lock-in if the developer is unavailable.
- Preserves individual accountability for day-to-day changes.
- Keeps legal/operational ownership (billing and infrastructure control) with the organization.

---

## How To Implement

1. Create/confirm a shared org email for infrastructure ownership.
2. Create the Cloudflare account with that org email.
3. Enable 2FA on the shared account and store recovery material in a team password manager:
   - Shared TOTP access for authorized Owners only
   - Backup/recovery codes
   - Optional: 2 hardware keys stored in separate secure locations
4. Invite individual admins using their personal Cloudflare users.
5. Give least-privilege roles (developer/admin only where needed).
6. Connect Cloudflare Workers to `greek-house-rotterdam/ghrweb` (Dashboard → Compute → Workers & Pages → Create → Connect to Git).
7. Confirm org-level billing ownership (payment method + invoice access).

---

## Task Split (Who Does What)

### Non-developer owners/admins

- Billing and invoice management.
- Domain renewal and registrar-level continuity checks.
- Access governance (add/remove admins; verify at least 2 Owners have recovery access).
- Basic operational checks (latest deploy succeeded, site is up).

### Developer-only

- DNS and Pages configuration changes.
- Build settings and environment variables/secrets.
- Security-sensitive platform configuration changes.
- Incident response for deployment/configuration failures.

---

## Operational Guardrails

- Maintain at least **2 trusted Owners** with recovery access.
- Do not use the shared org account for routine changes.
- Perform routine actions via personal accounts for clean auditability.
- Track and document audit trail visibility/retention across GitHub + Cloudflare (see pending task #16).

---

## CMS Authentication (OAuth Worker)

Decap CMS runs entirely in the browser. To read/write content on the GitHub repo, it needs a GitHub OAuth token. OAuth token exchange requires a server-side secret (`GITHUB_CLIENT_SECRET`) that cannot be exposed in browser code. The Cloudflare Worker at `src/oauth.ts` serves as this server-side middleman.

**How it works:**

1. Admin clicks "Login with GitHub" in Decap CMS (`/admin/`)
2. CMS opens a popup to the Worker's `/auth` endpoint
3. Worker sends a handshake message back to CMS, then redirects the popup to GitHub's authorization page
4. User authorizes the app on GitHub
5. GitHub redirects back to the Worker's `/callback` endpoint with a temporary code
6. Worker exchanges the code for an access token (server-side, using the client secret)
7. Worker sends the token back to CMS via `postMessage` (and `BroadcastChannel` as fallback)
8. CMS now has a GitHub token and can operate on the repo

**Dependencies:**

| Component | Location | What breaks if it's wrong |
|-----------|----------|---------------------------|
| `GITHUB_CLIENT_ID` | Cloudflare Worker env variable (Dashboard → Workers → Settings → Variables) | OAuth redirect fails — login shows GitHub error page |
| `GITHUB_CLIENT_SECRET` | Cloudflare Worker secret (same location, encrypted) | Token exchange fails — login popup shows "OAuth error" |
| GitHub OAuth App | Registered under the GitHub Organization (Settings → Developer settings → OAuth Apps) | All of the above — this is where the client ID/secret originate |
| `config.yml` → `backend.base_url` | `public/admin/config.yml` | CMS sends auth requests to the wrong URL — login fails silently |
| Worker deployment | Deployed at `ghrweb.enosi-ellinon-ollandias.workers.dev` | CMS login is completely unavailable |

**If CMS login breaks:**

1. Check the Worker is deployed and reachable (visit `https://ghrweb.enosi-ellinon-ollandias.workers.dev/` — should serve the site)
2. Verify `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are set in the Cloudflare dashboard
3. Verify the GitHub OAuth App still exists and the callback URL matches the Worker's `/callback` endpoint
4. Check `config.yml` → `backend.base_url` points to the correct Worker URL

**Secret rotation:** Generate new credentials in the GitHub OAuth App settings, then update the Worker env variables in the Cloudflare dashboard. No code change or redeployment needed.

---

## If You Already Started With A Personal Account

- Keep it temporarily to avoid blocking launch.
- Add org-owned account ownership and recovery controls first.
- Migrate billing ownership and admin access to the org model before launch.

---

## Potential Future Improvements / Upgrades

- Stay on Cloudflare free tier by default; upgrade only for a clear operational need.
- Consider a paid plan when you need stricter/advanced WAF controls beyond free defaults.
- Consider a paid plan when uptime risk requires stronger guarantees (e.g., stronger SLA/support expectations).
- Consider a paid plan when you need deeper security analytics/logging for incident response.
- Consider a paid plan when traffic growth or feature limits create repeated operational friction.

---

_Last updated: Apr 21, 2026 (added CMS Authentication / OAuth Worker section)_
