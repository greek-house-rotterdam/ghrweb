// @vitest-environment node
import { describe, it, expect } from "vitest";
import { experimental_AstroContainer as AstroContainer } from "astro/container";
import RedirectPage from "../components/RedirectPage.astro";

describe("RedirectPage", () => {
  async function render(to: string) {
    const container = await AstroContainer.create();
    return container.renderToString(RedirectPage, { props: { to } });
  }

  it("redirects with a meta refresh and names the short address as canonical", async () => {
    const html = await render("/gr/news/pascha-2026");
    expect(html).toContain('<meta http-equiv="refresh" content="0;url=/gr/news/pascha-2026"');
    expect(html).toContain('<link rel="canonical" href="/gr/news/pascha-2026"');
    expect(html).toContain('<a href="/gr/news/pascha-2026">');
  });

  it("keeps the redirect out of search results", async () => {
    expect(await render("/nl/news/x")).toContain('name="robots" content="noindex"');
  });

  it("percent-encodes Greek characters in the target", async () => {
    const html = await render("/gr/news/πάσχα");
    expect(html).toContain("url=/gr/news/%CF%80%CE%AC%CF%83%CF%87%CE%B1");
  });
});
