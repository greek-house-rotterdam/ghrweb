import { describe, it, expect } from "vitest";
import { existsSync, openSync, readSync, closeSync, statSync } from "fs";
import { join } from "path";
import { DOCUMENTS } from "../lib/documents";
import { t } from "../i18n/ui";

// The documents the site links to (src/lib/documents.ts) must be real files in
// public/, or the link breaks once the old site that also had them closes.

const PUBLIC = join(__dirname, "../../public");
// Cloudflare Workers serves files of at most 25 MiB.
const MAX_BYTES = 25 * 1024 * 1024;

function firstBytes(path: string, n: number): string {
  const fd = openSync(path, "r");
  const buf = Buffer.alloc(n);
  readSync(fd, buf, 0, n, 0);
  closeSync(fd);
  return buf.toString("latin1");
}

describe("documents in public/documents/", () => {
  for (const [name, href] of Object.entries(DOCUMENTS)) {
    const file = join(PUBLIC, href);

    it(`${name} lives in public/documents/`, () => {
      expect(href).toMatch(/^\/documents\/[a-z0-9-]+\.pdf$/);
    });

    it(`${name} exists, is a PDF, and fits Cloudflare's limit`, () => {
      expect(existsSync(file)).toBe(true);
      expect(firstBytes(file, 5)).toBe("%PDF-");
      expect(statSync(file).size).toBeLessThanOrEqual(MAX_BYTES);
    });
  }

  it("the chronicle's size on the History page matches the file", () => {
    const mb = (statSync(join(PUBLIC, DOCUMENTS.chronicle)).size / 1e6).toFixed(1);
    expect(t("en", "history.chronicle.details")).toContain(`${mb} MB`);
    // Greek and Dutch write the decimal with a comma.
    const withComma = `${mb.replace(".", ",")} MB`;
    expect(t("gr", "history.chronicle.details")).toContain(withComma);
    expect(t("nl", "history.chronicle.details")).toContain(withComma);
  });
});
