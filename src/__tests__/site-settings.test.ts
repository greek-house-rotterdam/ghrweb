import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "fs";
import { join } from "path";
import { parse as parseYaml } from "yaml";
import {
  BOARD_ROLES,
  SETTINGS_SCHEMAS,
  contactFormUrl,
  getSiteSettings,
  mapUrls,
  parseSettings,
  type SettingsFile,
} from "../lib/site-settings";
import { t } from "../i18n/ui";
import type { Lang } from "../i18n/utils";

const ROOT = join(__dirname, "../..");
const DATA = join(ROOT, "src/data");
const config = parseYaml(readFileSync(join(ROOT, "public/admin/config.yml"), "utf-8"));

const NAMES = Object.keys(SETTINGS_SCHEMAS) as SettingsFile[];

function readData(): Record<string, string> {
  return Object.fromEntries(
    NAMES.map((n) => [`../data/${n}.yml`, readFileSync(join(DATA, `${n}.yml`), "utf-8")]),
  );
}

// Valid files to change one value in.
const valid = (): Record<string, string> => ({
  "../data/board.yml": "members:\n  - role: president\n    name: Maria\n",
  "../data/contact.yml": "address: Somewhere 1\nunion_email: a@b.nl\n",
  "../data/forms.yml": "contact_form_id: abc_DEF-123\n",
});

function failure(files: Record<string, string>): string {
  try {
    parseSettings(files);
  } catch (error) {
    return (error as Error).message;
  }
  throw new Error("expected parseSettings to fail");
}

// ---------------------------------------------------------------------------
// The files in src/data
// ---------------------------------------------------------------------------

describe("src/data", () => {
  it("holds only YAML data files, one per settings group", () => {
    expect(readdirSync(DATA).sort()).toEqual(NAMES.map((n) => `${n}.yml`).sort());
  });

  it("passes the checks as committed", () => {
    expect(() => parseSettings(readData())).not.toThrow();
    expect(() => getSiteSettings()).not.toThrow();
  });

  it("keeps the placeholders as placeholders", () => {
    const { board, forms } = getSiteSettings();
    expect(board.members.map((m) => m.role)).toEqual([...BOARD_ROLES]);
    expect(board.members.every((m) => m.name === undefined)).toBe(true);
    expect(contactFormUrl(forms)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The loader
// ---------------------------------------------------------------------------

describe("parseSettings", () => {
  it("reads valid files", () => {
    const s = parseSettings(valid());
    expect(s.board.members).toEqual([{ role: "president", name: "Maria" }]);
    expect(s.contact.address).toBe("Somewhere 1");
    expect(s.forms.contact_form_id).toBe("abc_DEF-123");
  });

  it("treats an empty value, a missing value and a bare key alike: not set", () => {
    const files = {
      ...valid(),
      "../data/contact.yml": 'address: ""\nunion_email:\n',
    };
    const { contact } = parseSettings(files);
    expect(contact.address).toBeUndefined();
    expect(contact.union_email).toBeUndefined();
    expect(contact.house_email).toBeUndefined();
  });

  it("reads an empty file as nothing set", () => {
    const s = parseSettings({ ...valid(), "../data/contact.yml": "" });
    expect(s.contact).toEqual({});
  });

  it("trims spaces", () => {
    const s = parseSettings({ ...valid(), "../data/contact.yml": 'address: "  Street 1  "\n' });
    expect(s.contact.address).toBe("Street 1");
  });

  it("names the file and the field when a value is wrong", () => {
    const message = failure({ ...valid(), "../data/contact.yml": "union_email: not-an-email\n" });
    expect(message).toContain("src/data/contact.yml");
    expect(message).toContain("union_email");
  });

  it("rejects a link that is not https", () => {
    const message = failure({
      ...valid(),
      "../data/contact.yml": "instagram_url: http://www.instagram.com/x\n",
    });
    expect(message).toContain("instagram_url");
    expect(message).toContain("https://");
  });

  it("rejects text that is not a link", () => {
    expect(failure({ ...valid(), "../data/forms.yml": "member_form_url: soon\n" })).toContain(
      "member_form_url",
    );
  });

  it("rejects a whole link where only the contact form ID belongs", () => {
    const message = failure({
      ...valid(),
      "../data/forms.yml": "contact_form_id: https://docs.google.com/forms/d/e/abc/viewform\n",
    });
    expect(message).toContain("contact_form_id");
    expect(message).toContain("only the form ID");
  });

  it("rejects an unknown board role and says where", () => {
    const message = failure({
      ...valid(),
      "../data/board.yml": "members:\n  - role: president\n  - role: boss\n",
    });
    expect(message).toContain("src/data/board.yml");
    expect(message).toContain("members.1.role");
  });

  it("rejects a board member without a role", () => {
    expect(failure({ ...valid(), "../data/board.yml": "members:\n  - name: Maria\n" })).toContain(
      "members.0.role",
    );
  });

  it("rejects a board file without the members list", () => {
    expect(failure({ ...valid(), "../data/board.yml": "{}\n" })).toContain("members");
  });

  it("accepts a board with no members", () => {
    expect(parseSettings({ ...valid(), "../data/board.yml": "members: []\n" }).board.members).toEqual(
      [],
    );
  });

  it("fails on YAML that cannot be read", () => {
    const message = failure({ ...valid(), "../data/contact.yml": "address: [unclosed\n" });
    expect(message).toContain("src/data/contact.yml is not valid YAML");
  });

  it("fails when a file is missing", () => {
    const files = valid();
    delete files["../data/forms.yml"];
    expect(failure(files)).toContain("src/data/forms.yml is missing");
  });

  it("reports every wrong value of a file at once", () => {
    const message = failure({
      ...valid(),
      "../data/contact.yml": "union_email: x\nhouse_email: y\n",
    });
    expect(message).toContain("union_email");
    expect(message).toContain("house_email");
  });
});

describe("contactFormUrl", () => {
  const url = (id: string | undefined) =>
    contactFormUrl(parseSettings({ ...valid(), "../data/forms.yml": `contact_form_id: ${id ?? ""}\n` }).forms);

  it("builds the embed address from a form ID", () => {
    expect(url("1FAIpQLSabc-_9")).toBe(
      "https://docs.google.com/forms/d/e/1FAIpQLSabc-_9/viewform?embedded=true",
    );
  });

  it("gives nothing while the ID is empty", () => {
    expect(url(undefined)).toBeNull();
  });

  it("gives nothing for the old FORM_ID placeholder", () => {
    expect(url("FORM_ID")).toBeNull();
    expect(url("form_id")).toBeNull();
  });
});

describe("mapUrls", () => {
  it("encodes the address", () => {
    const { embed, link } = mapUrls("Van Vollenhovenstraat 18, 3016 BH Rotterdam");
    expect(embed).toBe(
      "https://www.google.com/maps?q=Van%20Vollenhovenstraat%2018%2C%203016%20BH%20Rotterdam&output=embed",
    );
    expect(link).toContain("query=Van%20Vollenhovenstraat%2018");
  });
});

// ---------------------------------------------------------------------------
// Texts for the board roles
// ---------------------------------------------------------------------------

describe("board role names", () => {
  for (const lang of ["gr", "nl", "en"] as Lang[]) {
    for (const role of BOARD_ROLES) {
      it(`${lang} has a role name and a placeholder name for ${role}`, () => {
        expect(t(lang, `board.role.${role}`)).toBeTruthy();
        expect(t(lang, `board.placeholder.${role}`)).toBeTruthy();
      });
    }
    it(`${lang} says what to do when there is no contact form`, () => {
      expect(t(lang, "contact.form.fallback")).toBeTruthy();
    });
  }
});

// ---------------------------------------------------------------------------
// Decap fields match the schema
// ---------------------------------------------------------------------------

interface CmsField {
  name: string;
  widget: string;
  required?: boolean;
  options?: ({ value: string } | string)[];
  fields?: CmsField[];
}

const settings = config.collections.find((c: { name: string }) => c.name === "settings");
const cmsFiles: { name: string; file: string; fields: CmsField[] }[] = settings.files;

// Compare the CMS fields with a zod object: same names, and a field is
// required in the CMS (required is not false) exactly when it is required in
// the schema (the value "not set" does not pass).
function compare(fields: CmsField[], schema: { shape: Record<string, any> }, where: string) {
  expect(fields.map((f) => f.name).sort(), `${where}: field names`).toEqual(
    Object.keys(schema.shape).sort(),
  );
  for (const field of fields) {
    const optionalInSchema = schema.shape[field.name].safeParse(undefined).success;
    const optionalInCms = field.required === false;
    expect(optionalInCms, `${where}.${field.name}: optional in CMS and in schema`).toBe(
      optionalInSchema,
    );
  }
}

describe("Decap site settings collection", () => {
  it("is a files collection with no create and no folder", () => {
    expect(settings.files).toBeDefined();
    expect(settings.folder).toBeUndefined();
    expect(settings.create).toBeUndefined();
  });

  it("is named so Decap's branch is cms/settings/<file>", () => {
    expect(settings.name).toBe("settings");
    expect(settings.label).toBe("Ρυθμίσεις ιστότοπου");
  });

  it("works in the editorial workflow", () => {
    expect(config.publish_mode).toBe("editorial_workflow");
  });

  it("has one entry per settings file, each pointing at its file", () => {
    expect(cmsFiles.map((f) => f.name)).toEqual(NAMES);
    for (const f of cmsFiles) expect(f.file).toBe(`src/data/${f.name}.yml`);
  });

  for (const name of NAMES) {
    it(`${name}: Decap fields match the schema`, () => {
      const entry = cmsFiles.find((f) => f.name === name)!;
      const schema = SETTINGS_SCHEMAS[name];
      compare(entry.fields, schema, name);
    });
  }

  it("board: the member fields match the schema", () => {
    const members = cmsFiles.find((f) => f.name === "board")!.fields[0];
    expect(members.widget).toBe("list");
    const item = (SETTINGS_SCHEMAS.board.shape.members as any).element;
    compare(members.fields!, item, "board.members");
  });

  it("board: the role list has exactly the roles the page knows", () => {
    const members = cmsFiles.find((f) => f.name === "board")!.fields[0];
    const role = members.fields!.find((f) => f.name === "role")!;
    expect(role.widget).toBe("select");
    expect(role.options!.map((o) => (typeof o === "string" ? o : o.value))).toEqual([
      ...BOARD_ROLES,
    ]);
  });

  it("uses Greek labels and hints (brand names excepted)", () => {
    const labels: string[] = [settings.label, settings.description];
    const walk = (fields: CmsField[]) => {
      for (const f of fields as (CmsField & { label: string; hint?: string })[]) {
        labels.push(f.label);
        if (f.hint) labels.push(f.hint);
        if (f.fields) walk(f.fields);
      }
    };
    for (const f of cmsFiles as any[]) {
      labels.push(f.label);
      walk(f.fields);
    }
    for (const text of labels.filter((l) => !["Instagram", "Facebook"].includes(l))) {
      expect(text).toMatch(/[Α-Ωα-ω]/);
    }
  });
});
