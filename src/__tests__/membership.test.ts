import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "fs";
import { join, relative } from "path";
import { parse as parseYaml } from "yaml";
import { formsSchema } from "../lib/site-settings";

// The managers don't want a public membership application form (#115):
// people get in touch first, and the managers send the form themselves.
// Editor content (src/content) may still link to Google Forms, for example an
// event sign-up; these tests cover the code and the site settings only.

const ROOT = join(__dirname, "../..");
const SCANNED = ["src/pages", "src/components", "src/layouts", "src/i18n", "src/data"];
const FORM_LINK = /docs\.google\.com\/forms|forms\.gle/;

function files(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const full = join(dir, e.name);
    if (e.isDirectory()) return files(full);
    return /\.(astro|ts|js|yml|yaml)$/.test(e.name) ? [full] : [];
  });
}

describe("no public membership form", () => {
  it("the site settings hold only the contact form", () => {
    expect(Object.keys(formsSchema.shape)).toEqual(["contact_form_id"]);
  });

  it("/admin offers only the contact form field", () => {
    const config = parseYaml(readFileSync(join(ROOT, "public/admin/config.yml"), "utf-8"));
    const settings = config.collections.find((c: { name: string }) => c.name === "settings");
    const forms = settings.files.find((f: { name: string }) => f.name === "forms");
    expect(forms.fields.map((f: { name: string }) => f.name)).toEqual(["contact_form_id"]);
  });

  for (const file of SCANNED.flatMap((d) => files(join(ROOT, d)))) {
    it(`${relative(ROOT, file)} has no Google Form link`, () => {
      expect(readFileSync(file, "utf-8")).not.toMatch(FORM_LINK);
    });
  }

  it("the membership page sends people to the contact page", () => {
    const page = readFileSync(join(ROOT, "src/pages/[lang]/become-a-member.astro"), "utf-8");
    expect(page).toContain("/contact`");
  });
});
