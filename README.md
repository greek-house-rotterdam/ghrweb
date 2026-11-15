# Greek House in Rotterdam — Website

The website for the Greek House in Rotterdam (GHR): a sustainable, trilingual hub for cultural history, community news, and event coordination.

## Documentation

Most project documentation is kept out of version control for now. These files are in it:

| Document | Description |
| :--- | :--- |
| [Content Style Guide](docs/content-style-guide.md) | Rules the AI content review checks posts against |
| [Tone & Voice Guidelines](docs/tone-and-voice-guidelines.md) | Tone and voice used by the translation and review prompts |
| [Editor Guide](docs/editor-guide.md) | For website editors (in Greek): writing, publishing, fixing translations, hiding posts, settings, events |
| [Developer Guide](docs/developer-guide.md) | For the developer: how changes reach the site, removing content, alerts, events, secrets |
| [Known Limitations](docs/known-limitations.md) | Gaps in the publishing pipeline we accept for now, with workarounds |
| [Content Reset](docs/content-reset.md) | The November 2026 reset to the managers' approved content, and how to restore removed entries |

When a change alters how editors or the developer work, update the two guides in the same pull request.

## Commands

All commands are run from the root of the project:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run dev:cms`         | Starts dev server + Decap CMS local backend      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |

## CMS Admin

The site uses [Decap CMS](https://decapcms.org/) for content management, accessible at `/admin`.

**Local development:** Run `npm run dev:cms` and visit `http://localhost:4321/admin/`. This starts a local proxy server (`decap-server`) so you can create and edit content without GitHub authentication. Changes write directly to your local `src/content/` files.

**Production:** The CMS authenticates via GitHub. The `local_backend` setting in `public/admin/config.yml` only activates on `localhost` — it is ignored on any other domain, so it is safe to leave on.
