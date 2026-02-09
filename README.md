# Greek House in Rotterdam — Website

The website for the Greek House in Rotterdam (GHR): a sustainable, trilingual hub for cultural history, community news, and event coordination.

## Documentation

| Document | Description |
| :--- | :--- |
| [Background](docs/background.md) | Project goals, constraints, and high-level context |
| [Requirements](docs/requirements.md) | Functional and non-functional requirements |
| [Tech Stack](docs/tech-stack.md) | Architecture and technology choices |
| [Pre-Interview PRD](docs/pre_interview_prd.md) | Product requirements before stakeholder interviews |
| [Post-Interview PRD](docs/post_interview_prd.md) | Detailed requirements from stakeholder interviews |
| [FAQ & Knowledge Base](docs/faq.md) | Curated insights from development Q&A sessions |

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
