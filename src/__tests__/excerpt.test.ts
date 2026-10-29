import { describe, it, expect } from "vitest";
import { descriptionOrExcerpt, excerpt } from "../lib/excerpt";

describe("excerpt", () => {
  it("returns short text unchanged, without an ellipsis", () => {
    expect(excerpt("Hello world")).toBe("Hello world");
  });

  it("returns an empty string for missing or empty input", () => {
    expect(excerpt(undefined)).toBe("");
    expect(excerpt("")).toBe("");
    expect(excerpt("  \n\n ")).toBe("");
  });

  it("strips Markdown", () => {
    const md = [
      "# Title",
      "",
      "Some **bold**, *italic* and `code` with a [link](https://x.org).",
      "",
      "![alt text](/images/a.jpg)",
      "",
      "> quoted",
      "",
      "- item one",
      "1. item two",
      "",
      "---",
      "",
      "```js",
      "const hidden = 1;",
      "```",
      "End.",
    ].join("\n");
    expect(excerpt(md)).toBe(
      "Title Some bold, italic and code with a link. quoted item one item two End.",
    );
  });

  it("strips HTML and decodes common entities", () => {
    expect(excerpt("<p>Tom&nbsp;&amp; <b>Jerry</b></p><!-- note -->")).toBe(
      "Tom & Jerry",
    );
  });

  it("collapses whitespace and line breaks", () => {
    expect(excerpt("a \n\n  b\tc")).toBe("a b c");
  });

  it("keeps text of exactly the limit, without an ellipsis", () => {
    const text = "a".repeat(200);
    expect(excerpt(text, 200)).toBe(text);
  });

  it("cuts at a word boundary and adds an ellipsis only when it cut", () => {
    const out = excerpt("one two three four five six seven", 20);
    expect(out).toBe("one two three four…");
    expect(out.length).toBeLessThanOrEqual(20);
  });

  it("never goes over the limit, including the ellipsis", () => {
    const text = "lorem ipsum dolor sit amet ".repeat(30);
    for (const limit of [10, 50, 120, 200]) {
      expect(excerpt(text, limit).length).toBeLessThanOrEqual(limit);
    }
  });

  it("does not leave trailing punctuation before the ellipsis", () => {
    expect(excerpt("alpha beta, gamma delta", 14)).toBe("alpha beta…");
  });

  it("hard-cuts a single word longer than the limit", () => {
    expect(excerpt("x".repeat(50), 10)).toBe("x".repeat(9) + "…");
  });

  it("works with Greek text", () => {
    const out = excerpt("Καλώς ήρθατε στο Ελληνικό Σπίτι του Ρότερνταμ", 25);
    expect(out.endsWith("…")).toBe(true);
    expect(out.length).toBeLessThanOrEqual(25);
    expect(out).toBe("Καλώς ήρθατε στο…");
  });
});

describe("descriptionOrExcerpt", () => {
  it("prefers the description", () => {
    expect(descriptionOrExcerpt("Own text", "Body text")).toBe("Own text");
  });

  it("falls back to the body when the description is missing or empty", () => {
    expect(descriptionOrExcerpt(undefined, "**Body** text")).toBe("Body text");
    expect(descriptionOrExcerpt("", "Body text")).toBe("Body text");
    expect(descriptionOrExcerpt("   ", "Body text")).toBe("Body text");
  });

  it("is empty when both are missing", () => {
    expect(descriptionOrExcerpt(undefined, undefined)).toBe("");
  });
});
