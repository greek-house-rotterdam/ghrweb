# Cloudflare Ownership & Operations — GHR

> Concise implementation note for Cloudflare setup and governance.

---

## Decisions

1. **Use an organization-owned Cloudflare account** (shared org email) as the primary owner.
2. **Use personal Cloudflare users for daily work** (developer/admin actions).
3. **Keep the shared org login as break-glass only** (recovery/continuity), not daily operations.
4. **Keep billing under the organization identity** (payment method and invoices tied to org ownership).

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
6. Connect Cloudflare Pages to `greek-house-rotterdam/ghrweb`.
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

## If You Already Started With A Personal Account

- Keep it temporarily to avoid blocking launch.
- Add org-owned account ownership and recovery controls first.
- Migrate billing ownership and admin access to the org model before launch.

---

_Last updated: Feb 22, 2026_
