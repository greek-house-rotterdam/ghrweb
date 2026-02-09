# Stakeholder Pitch — Greek House in Rotterdam Website

> Talking points and presentation guide for the prototype walkthrough with the GHR board.
> Audience: non-technical stakeholders.

---

## 1. What We're Building

A website for the Greek House in Rotterdam — a central place where people can:

- Read news and announcements
- See upcoming events
- Learn about the organization's history and teams
- Contact us or apply to become a member
- Switch between Greek, Dutch, and English

This website is designed as a **content hub** with no user interaction beyond navigation and forms. Visitors read, browse, and submit forms — nothing more. This keeps the site fast, secure, and simple to maintain.

---

## 2. Prototype Walkthrough

> _Open the website and walk through the following:_

### What visitors see

- **Home page** — news highlights, upcoming events, team activities, call-to-action buttons
- **History** — the 80-year story of the Greek House
- **Teams** — dance group, Dutch/art classes, meetings, etc.
- **News** — articles and announcements, with dates and images
- **Events** — calendar of upcoming activities
- **Contact** — form, Google Map, phone, email, social media links
- **About Us** — mission, board, organization overview
- **FAQ** — frequently asked questions
- **Become a Member** — enrollment form (friend, member, candidate)
- **Language switcher** — Greek / Dutch / English on every page

### Key things to notice

- The site is **trilingual** — every page exists in all three languages
- It is **mobile-friendly** — works on phones, tablets, and desktops
- It loads **instantly** — no waiting, no spinning icons
- There is **no login** for visitors — the site is fully public

---

## 3. How Admins Add Content

> _Open the admin panel at `/admin` and demonstrate._

### The admin panel

- Admins visit `yoursite.com/admin` and log in with their personal account
- They see a simple dashboard with sections: News, Events
- To create a post, they click "New," fill in a title, description, date, optionally upload an image, and write the article body in a simple text editor
- They click **Publish** — and the new article appears on the website within about 30 seconds

### What happens behind the scenes (simplified)

1. Admin writes and publishes a post in Greek
2. The post is saved automatically
3. The website rebuilds itself — live in ~30 seconds
4. An automated process translates the post into Dutch and English
5. The website rebuilds again with the translations

**The admin does not need to translate anything manually.** They write once in Greek, and the system takes care of the rest.

### Who can publish

We can set up different permission levels:

- **Admins** (e.g., the Board): full control — they can publish directly
- **Editors** (e.g., the Cultural Team): they can write and submit content, but an admin reviews and approves it before it goes live

This gives the organization editorial control without bottlenecks.

---

## 4. Content Freedom

### What admins can publish

- News articles (text + images)
- Event announcements (with date, location, description, images)
- Any combination of text, images, embedded YouTube/Spotify, and downloadable PDFs

### What admins can change

- Create, edit, or remove any news post or event
- Upload and replace images
- Update text on any content page

### What requires developer help

- Adding a new page type (e.g., a "Gallery" section)
- Changing the website layout or navigation structure
- Modifying form fields or adding new forms

**Day-to-day content work** (posting news, updating events) is fully in the hands of the team. **Structural changes** (new pages, layout redesigns) need a developer.

---

## 5. Google Forms — Why This Choice

Contact and enrollment forms are powered by Google Forms, embedded directly into the website. This is a deliberate choice:

| Benefit | Explanation |
|---------|-------------|
| **Free** | No cost, ever |
| **Spam protection** | Google handles it — no captcha puzzles for users |
| **Responses in Google Sheets** | Organized, searchable, easy to share with the board |
| **Email notifications** | The organization gets an email whenever someone submits |
| **Data retention control** | You decide how long to keep responses — and you can delete them at any time |
| **GDPR-friendly** | Google stores the data; you control access and retention. We add a consent checkbox to each form |
| **No database needed** | No extra system to maintain, secure, or pay for |
| **Reliable** | Google infrastructure — virtually zero downtime |

The alternative would be a custom-built form, which would require a backend server, a database, spam protection, and ongoing maintenance — all for no added benefit.

---

## 6. Pricing

### Annual running costs

| Item | Cost |
|------|------|
| Domain name renewal | ~€10–15/year |
| Website hosting | **Free** (Cloudflare Pages free tier) |
| Content management system | **Free** (Decap CMS) |
| SSL certificate (secure connection) | **Free** (Cloudflare) |
| CDN (fast global delivery) | **Free** (Cloudflare) |
| Automated translation | **Free** (DeepL API free tier — 500,000 characters/month) |
| Contact & enrollment forms | **Free** (Google Forms) |
| Analytics | **Free** (Google Analytics) |
| **Total per year** | **~€10–15** |

### Compared to typical alternatives

A managed hosting solution (e.g., Hostinger + WordPress) would cost **€50–65/year** and require ongoing maintenance: software updates, security patches, plugin conflicts, backups. Our approach costs a fraction and requires near-zero technical maintenance.

### One-time costs

| Item | Cost |
|------|------|
| Development | Volunteer (me) |
| Domain purchase | Already done |

---

## 7. How the Technology Works (Simplified)

Think of this website like a **digital brochure** that automatically reprints itself every time someone updates the content.

- The website is a collection of **pre-built pages** — like a printed booklet, but digital
- When an admin publishes something, the system **rebuilds the booklet** with the new content and distributes it worldwide in seconds
- There is **no server running** in the background — no machine to maintain, no software to update, nothing that can crash
- The pages are delivered from a **global network** (Cloudflare) — visitors in Greece, the Netherlands, or anywhere else get the fastest possible load time

### Why this matters

| Property | What it means for you |
|----------|----------------------|
| **No server** | Nothing to maintain, nothing to break, nothing to hack |
| **Pre-built pages** | The site loads instantly — no waiting |
| **Global delivery** | Fast everywhere in the world |
| **Automatic rebuilds** | Publish once, the site updates itself |
| **No vendor lock-in** | Everything is in our own repository — we can move to any provider at any time |

---

## 8. Security & Privacy

### Security

Because there is no server, no database, and no user login, the attack surface is essentially **zero**.

- No passwords to steal (visitors don't log in)
- No database to breach (there isn't one)
- No server to hack (pages are pre-built files on a CDN)
- Cloudflare provides DDoS protection, firewall, and SSL — included for free
- Admin access is protected by personal accounts with optional two-factor authentication

### Privacy (GDPR)

Even though the site is public, we are collecting personal data through forms. We handle this responsibly:

- **Privacy Policy page** on the website — explains what data we collect and why
- **Cookie consent banner** — required for Google Analytics; visitors must opt in
- **GDPR consent checkbox** on every Google Form — "I agree to the processing of my data"
- **Data retention** — we define how long form responses are kept and who has access
- **No user tracking beyond analytics** — we don't profile visitors

---

## 9. Maintenance Plan

### First 3 months after launch (developer-led)

- I maintain the website and fix any issues
- I train the admin team on how to use the content management system
- I monitor for any problems and address them

### After handover (organization-led)

| Task | Who | How often |
|------|-----|-----------|
| Publish news articles | Admins / Cultural team | As needed |
| Update event listings | Admins / Cultural team | As needed |
| Review form responses | Board / designated person | Weekly or as needed |
| Review/approve editor submissions | Admin | As needed |
| Check analytics dashboard | Board / designated person | Monthly |
| Domain renewal | Organization (auto-renew) | Yearly |

### What does NOT need maintenance

- Hosting — automatic, free, no action required
- SSL certificate — automatic renewal by Cloudflare
- Software updates — the site is static files; there are no plugins or frameworks to patch
- Backups — all content lives in the repository with full version history; nothing can be lost permanently
- Translations — automated on every publish

### When to call the developer

- Adding a new page or section to the site
- Changing the site layout or navigation
- Fixing a technical issue (rare, given the architecture)
- Updating form structure or adding new forms

---

## 10. Translation

Admins write content in **one language** (Greek). The system handles the rest:

1. Admin publishes an article in Greek
2. An automated process detects the new content
3. It sends the text to a professional-grade translation service (DeepL)
4. The Dutch and English versions are generated and published automatically

**Quality:** DeepL is widely regarded as one of the best translation engines available — often better than Google Translate for European languages. If any translation needs a manual correction, an admin can edit it directly.

**UI elements** (buttons, menus, labels) are translated once during development and don't change.

---

## 11. What the Website Does NOT Do

Setting clear boundaries avoids misunderstandings and scope creep:

| Not included | Why |
|--------------|-----|
| User accounts / login | Adds complexity, maintenance, and security risk for no benefit |
| Payment processing | Out of scope — handled separately by the organization |
| Subscription management | Out of scope |
| Email newsletters from the website | Not needed for v1 — news is posted on the site and shared on social media |
| File uploads by visitors | Major security risk — all uploads are admin-only |
| Live chat | Adds maintenance burden; contact form is sufficient |
| Event registration (v1) | Deferred to a future version; can integrate Eventbrite later |

---

## 12. Open Questions for the Board

These decisions are still pending and need your input:

### Content & Scope

1. **Who provides the initial content?** Specifically: the History page, Teams page, About Us text, FAQ entries. Is any of this ready, or does it need to be written?
2. **Is English included from launch?** The system supports it, but if no English-speaking audience is expected initially, we can launch with Greek and Dutch only and add English later.
3. **Is the live social media feed in scope for launch?** We can add Instagram/Facebook icon links (confirmed), but embedding a live feed adds complexity. Recommend deferring to post-launch.

### Forms & Communication

4. **Is member enrollment a separate form or part of the contact form?** Options: (a) one form with a dropdown ("I want to become a member"), or (b) two separate forms — one for contact, one for enrollment.
5. **Is there a plan for an external newsletter service** (e.g., Mailchimp)? The current scope only collects opt-in interest. If you want to actually send newsletters, we need to decide on a tool.

### Operations

6. **Who are the initial admins and editors?** We need names and email addresses to set up accounts.
7. **Each admin/editor needs a free personal account** (GitHub). Is this acceptable for the team, or is it a concern?
8. **Photos of people at events** — do we need a photo consent policy? GDPR applies to identifiable individuals.

---

## 13. Summary of Benefits

| | Our approach |
|---|---|
| **Cost** | ~€10–15/year — just the domain |
| **Speed** | Pages load instantly from a global network |
| **Security** | No server, no database, no passwords — near-zero attack surface |
| **Maintenance** | Near-zero for day-to-day operations |
| **Content management** | Visual editor — no technical skills needed |
| **Translation** | Automatic — write once in Greek, get Dutch and English for free |
| **Forms** | Google Forms — free, reliable, GDPR-manageable, no database needed |
| **Portability** | No vendor lock-in — everything is ours, we can move anytime |
| **Scalability** | Handles any amount of traffic — served from a global CDN |

---

## 14. Development Timeline

Estimated timeline from today. Assumes part-time effort (evenings/weekends) with AI-assisted development.

### Phase 1 — Foundation (Weeks 1–2)

- [x] Project setup (framework, CMS, hosting config)
- [x] Tech stack selection and documentation
- [x] CMS configuration (news and events collections)
- [x] Trilingual routing and language switcher
- [x] Base layout, header, footer
- [ ] Select and apply visual theme / design system
- [ ] Home page layout and content sections
- [ ] Mobile responsiveness pass

### Phase 2 — Core Pages (Weeks 3–4)

- [ ] News listing and detail pages (with pagination)
- [ ] Events listing and detail pages
- [ ] History page
- [ ] Teams page
- [ ] About Us page
- [ ] FAQ page
- [ ] SEO setup (meta tags, Open Graph, sitemap, structured data)

### Phase 3 — Forms & Integration (Weeks 5–6)

- [ ] Contact page with embedded Google Form + Google Map
- [ ] Become a Member page with embedded Google Form
- [ ] GDPR consent checkbox on all forms
- [ ] Privacy Policy page
- [ ] Cookie consent banner (for Google Analytics)
- [ ] Google Analytics (GA4) integration
- [ ] Social media icon links in header/footer

### Phase 4 — Translation & Automation (Week 7)

- [ ] GitHub Action for automated translation (DeepL API)
- [ ] Test translation pipeline: publish in Greek → auto-generate Dutch + English
- [ ] Translate all UI strings (navigation, buttons, labels)
- [ ] Review and correct auto-translated content

### Phase 5 — Polish & Launch Prep (Week 8)

- [ ] Content population (requires stakeholder input)
- [ ] Cross-browser testing (Chrome, Safari, Firefox, mobile)
- [ ] Performance audit (Lighthouse)
- [ ] Final SEO review
- [ ] Admin training session with the team
- [ ] Domain configuration (DNS → Cloudflare Pages)
- [ ] Launch

### Phase 6 — Post-Launch (Weeks 9–12)

- [ ] Monitor for issues and fix bugs
- [ ] Collect feedback from admins and visitors
- [ ] Conduct first user survey
- [ ] Gradual handover to the organization team
- [ ] Document admin workflows (simple how-to guide)

### Key Dependencies

| Dependency | Needed by | Who provides it |
|------------|-----------|-----------------|
| Visual theme / design direction approval | Week 2 | Board |
| Initial content (History, Teams, About, FAQ) | Week 8 | Board / Cultural team |
| Admin/editor team members identified | Week 7 | Board |
| GitHub accounts created by admins/editors | Week 8 | Each team member |
| Google Form content finalized (questions, routing) | Week 5 | Board |
| Domain DNS access | Week 8 | Organization |

### Risk: Content Readiness

The biggest risk to the timeline is **content availability**. The website structure and functionality can be built independently, but pages like History, Teams, and About Us need text and images from the organization. If content is delayed, launch will be delayed.

**Recommendation:** Start gathering content now — even rough drafts. The developer can format and polish it, but the knowledge must come from the organization.
