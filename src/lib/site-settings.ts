// Site settings: language-neutral facts that editors change in /admin
// (board, contact details, forms). They live in src/data/*.yml.
//
// Every file is checked here when it is read. A wrong value fails the build
// with a message that names the file and the field, so a bad edit never
// reaches the live site.
import { z } from "astro/zod";
import { parse as parseYaml } from "yaml";

// The board roles. Names for each language live in src/i18n/ui.ts
// (board.role.<role>). Decap's role list in public/admin/config.yml must match.
export const BOARD_ROLES = [
  "president",
  "vice_president",
  "secretary",
  "treasurer",
  "member",
] as const;
export type BoardRole = (typeof BOARD_ROLES)[number];

// An empty box in the CMS is saved as "" or left out. Both mean "not set".
const unset = (value: unknown) =>
  value === "" || value === null ? undefined : value;
const optional = <T extends z.ZodType>(schema: T) =>
  z.preprocess(unset, schema.optional());

const text = optional(z.string().trim());
const email = optional(z.string().trim().email());
const httpsUrl = optional(
  z
    .string()
    .trim()
    .url()
    .refine((v) => v.startsWith("https://"), "must start with https://"),
);

export const boardSchema = z.object({
  members: z.array(
    z.object({
      role: z.enum(BOARD_ROLES),
      name: text,
    }),
  ),
});

export const contactSchema = z.object({
  address: text,
  union_email: email,
  house_email: email,
  instagram_url: httpsUrl,
  facebook_url: httpsUrl,
});

export const formsSchema = z.object({
  // Only the ID of the Google Form (the part between /d/e/ and /viewform).
  contact_form_id: optional(
    z
      .string()
      .trim()
      .regex(/^[A-Za-z0-9_-]+$/, "must be only the form ID, not a link"),
  ),
  member_form_url: httpsUrl,
  candidate_form_url: httpsUrl,
  friend_form_url: httpsUrl,
});

export const SETTINGS_SCHEMAS = {
  board: boardSchema,
  contact: contactSchema,
  forms: formsSchema,
} as const;

export type SettingsFile = keyof typeof SETTINGS_SCHEMAS;
export type Board = z.output<typeof boardSchema>;
export type Contact = z.output<typeof contactSchema>;
export type Forms = z.output<typeof formsSchema>;
export interface SiteSettings {
  board: Board;
  contact: Contact;
  forms: Forms;
}

// `files` maps a path like "../data/board.yml" to the file's text.
export function parseSettings(files: Record<string, string>): SiteSettings {
  const result: Record<string, unknown> = {};
  for (const name of Object.keys(SETTINGS_SCHEMAS) as SettingsFile[]) {
    const path = Object.keys(files).find((p) => p.endsWith(`/${name}.yml`));
    if (path === undefined) {
      throw new Error(`Site settings: src/data/${name}.yml is missing.`);
    }
    let data: unknown;
    try {
      // An empty file is read as "nothing set".
      data = parseYaml(files[path]) ?? {};
    } catch (error) {
      throw new Error(
        `Site settings: src/data/${name}.yml is not valid YAML. ${(error as Error).message}`,
      );
    }
    const parsed = SETTINGS_SCHEMAS[name].safeParse(data);
    if (!parsed.success) {
      const problems = parsed.error.issues
        .map((i) => `  - ${i.path.join(".") || "(whole file)"}: ${i.message}`)
        .join("\n");
      throw new Error(
        `Site settings: src/data/${name}.yml has a wrong value.\n${problems}`,
      );
    }
    result[name] = parsed.data;
  }
  return result as unknown as SiteSettings;
}

let cached: SiteSettings | undefined;

export function getSiteSettings(): SiteSettings {
  cached ??= parseSettings(
    import.meta.glob("../data/*.yml", {
      query: "?raw",
      import: "default",
      eager: true,
    }) as Record<string, string>,
  );
  return cached;
}

// The contact form's page, or null while no real form ID is set. "FORM_ID" is
// the placeholder the page used to contain; treat it as not set.
export function contactFormUrl(forms: Forms): string | null {
  const id = forms.contact_form_id;
  if (!id || id.toUpperCase() === "FORM_ID") return null;
  return `https://docs.google.com/forms/d/e/${id}/viewform?embedded=true`;
}

export function mapUrls(address: string) {
  const q = encodeURIComponent(address);
  return {
    embed: `https://www.google.com/maps?q=${q}&output=embed`,
    link: `https://www.google.com/maps/search/?api=1&query=${q}`,
  };
}
