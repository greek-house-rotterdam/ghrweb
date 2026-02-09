# Greek House in Rotterdam — Website Requirements

> Formalized requirements for the GHR website. Compiled from pre- and post-stakeholder-interview PRDs, with priority given to post-interview decisions.

---

## 1. Project Overview

**Goal:** Build a sustainable, low-maintenance website for the Greek House in Rotterdam (GHR) — a voluntary cultural organization. The website serves as a hub for cultural history, community news, event coordination, and member engagement.

**Primary audience:** Younger Greek people in the Netherlands.

**Guiding principles:**

- Simplicity over feature richness — avoid feature creep
- Optimized for value, reliability, and ease-of-use (visitors and admins)
- Must remain actively maintained without becoming a burden

---

## 2. Site Structure & Content

### 2.1 Pages

| Page | Description |
|------|-------------|
| **Home** | Landing page with news, upcoming events, team highlights, and CTAs |
| **History** | "80 Years of Greek House" — cultural and historical timeline |
| **Teams** | Activities organized by team: dance, Dutch/art classes, meetings, etc. |
| **News** | Recent news and announcements |
| **Events** | Calendar of upcoming events |
| **Contact** | Contact form, map, direct contact details |
| **About Us** | Organization overview, mission, board |
| **FAQ** | Frequently asked questions |
| **Become a Member** | Enrollment form (friend, member, candidate member) |

### 2.2 Home Page — Content Priority

**Primary (above the fold):**

1. Recent news and announcements
2. Activities by team (dance, classes, meetings)
3. Calendar with upcoming events
4. Useful information

**Secondary:**

5. Partners and Greek organizations
6. Navigation links to subpages (History, Contact, FAQ, About, Enrollment)

### 2.3 Content Types (Admin-Uploaded Only)

Visitors cannot upload any content. All content is managed by authorized admins.

Supported content types for admin uploads:

- Text (articles, announcements, descriptions)
- Images (JPEG, PNG, WebP — max 5 MB recommended, with auto-optimization)
- Embedded media (YouTube/Vimeo embeds for video, Spotify embeds)
- PDFs (optional, for downloadable resources)

---

## 3. Languages & Translation

**Languages:** Greek, Dutch, English — trilingual from launch

**Translation approach:**

- Automated, high-quality AI translation
- Options: DeepL API, hosting provider solution, or GitHub Action with AI
- Must apply automatically to new content (news posts, event updates)

---

## 4. Contact & Forms

### 4.1 Contact Form

- **Preferred implementation:** Embedded Google Form
- **Fields:** Name, Email, Phone (optional), Message
- **Routing dropdown:** "Already a member," "Want to become a member," "General question," "Volunteering," "Other" (with free-text field)
- **On submission:** Thank-you message with expected response time
- **Notification:** Organization receives email with submitted data
- **Anti-spam:** Google Forms built-in protection (no separate reCAPTCHA needed — see Q&A below)

### 4.2 Member Enrollment Form

- Separate or combined with contact form via routing

> **Open question:** Is member enrollment a separate Google Form, or the same form with a routing option?

### 4.3 Additional Contact Elements

- Interactive Google Map showing the Greek House location
- Direct contact details: phone, email, social media icons
- Call-to-action: "Become a Volunteer" / "Enroll as Member"

---

## 5. Access & Privacy

### 5.1 Public Access

- The website is fully public — no user login or registration
- No user-uploaded content (eliminates security and hosting risk)

### 5.2 Admin Access

- **Phase 1 (launch):** Single-tier admin access
- **Phase 2 (post-launch):** Multi-tier privileges (admin, editor, etc.)

**Publishing permissions (who can create/edit content):**

- Admin / Editor team
- Board of Directors (Διοικητικό Συμβούλιο)
- Cultural team (Πολιτιστική Ομάδα)

### 5.3 Privacy & GDPR

Even though the site is public, GDPR obligations apply:

- **Privacy Policy page** — required; explains what data is collected and how it's processed
- **Cookie consent banner** — required if using analytics or third-party embeds
- **Google Forms consent** — add a GDPR consent checkbox to each Google Form (Google Forms does not provide this automatically for the data controller)
- **Data retention** — define and document how long form responses are kept (Google Sheets stores responses; no separate database needed)
- **Event photos** — consider consent for photos of identifiable people

---

## 6. Communications & News

- News and announcements are published on the website
- **No email dispatch, no push notifications** from the website itself
- News is cross-posted to social media with links back to the website
- Newsletter opt-in checkbox on forms collects interest for future use

> **Open question:** Is there a plan for an external newsletter service (e.g., Mailchimp), or is the opt-in purely for future consideration?

---

## 7. Events

### 7.1 Launch Scope (v1)

- Events calendar page showing upcoming events
- Events displayed on the home page

### 7.2 Future Scope (v2)

- Third-party event registration integration (e.g., Eventbrite)
- Features: QR code registration, notifications for event changes
- Admin access to registration data (via third-party dashboard)
- Nice-to-haves: waiting list, cancellation

---

## 8. Social Media

### 8.1 Required (v1)

- Social media icon links: Instagram, Facebook, Spotify, etc.
- Placed in header/footer for persistent visibility

### 8.2 Deferred / Under Discussion

- Live social media feed embed
  - Must be lightweight, automated, and visually unobtrusive
  - Decision: defer unless a clean, low-maintenance solution is found

> **Open question:** Is the live feed in scope for v1 or explicitly deferred?

---

## 9. SEO & Discoverability

- **SEO is mandatory.** Applied automatically to every content update (new posts, pages).
- Includes: meta tags, Open Graph tags, structured data, sitemap, semantic HTML
- **Nice-to-have:** GEO / AEO (AI engine optimization) for discoverability in AI assistants

---

## 10. Success Metrics

| Metric | How to Measure |
|--------|---------------|
| Website traffic increase (%) | Web analytics (e.g., Google Analytics) |
| New members via website | Track enrollment form submissions |
| Event participation via website | Track event page visits / registration clicks |
| Reduction in repetitive emails | Compare email volume before/after launch |
| User satisfaction | Two surveys — one at launch, one in 2027 |

> **Open question:** Is Google Analytics the preferred analytics tool, or something lighter (e.g., Plausible, Umami)?

---

## 11. Style & Aesthetics

- **Visual identity:** Modern, clean, minimal
- **Target feel:** Welcoming to younger audiences, not institutional
- **Anti-reference:** Not like [ekbru.be](https://ekbru.be/)
- **Accessibility:** Standard web accessibility; no special requirements for high contrast or large fonts
- **Mobile responsive:** Yes

---

## 12. Development & Technical Approach

- **Code-first preferred** — avoid manual canvas/Figma-based design workflows
- **Speed of development is paramount**
- **Ease of use for non-technical admins is equally paramount**
- If using GitHub: automate SEO, translation, and module updates via GitHub Actions
- Otherwise: platform must provide ready-made UI for non-technical content management

### Developer Profile

- Senior backend developer, Python & AI expert
- Intermediate in GCP, Firebase, GitHub Actions
- Beginner-level frontend — relies on AI coding assistants

---

## 13. Payments & Subscriptions

- **No payment processing** on the website
- **No subscription management** on the website

---

## 14. Logistics

- Annual domain/hosting renewal is acceptable
- Billing handled by the organization (credit card provided)
- Developer maintains the website for the first 3 months post-launch
- After handover: non-technical members manage day-to-day operations
- Developer remains available for serious technical issues
- Target launch date: 2 months from this day
- Domain name: already purchased (re-use from old website)

---

## 15. Hosting & Platform

> **Open question:** No platform decision has been made. Given the developer profile and admin requirements, options include:
>
> - **Static site (e.g., Astro/Hugo) + Headless CMS (e.g., Decap CMS) + Firebase Hosting** — low cost, high control, but requires developer for structural changes
> - **WordPress on managed hosting (e.g., Hostinger)** — rich plugin ecosystem, easy for non-technical admins, but higher maintenance and security surface
> - **Website builder (e.g., Squarespace, Wix)** — easiest for non-technical people, but least developer control and potentially higher annual cost
>
> Recommendation depends on the balance between admin simplicity and developer control.

---

## Appendix: Answered Questions

These questions were raised in the post-interview PRD.

### Q1: What content can be uploaded to the website?

Since only admins upload content, the types are: text, images (JPEG/PNG/WebP, ≤5 MB with compression), embedded video/audio, and optionally PDFs. No user-uploaded content. Image optimization should be automated to keep the site fast.

### Q2: Is a GDPR compliance checkbox needed when using Google Forms?

**Yes.** Google Forms does not handle GDPR on behalf of the data controller (GHR). You need:

- A consent checkbox on each form ("I agree to the processing of my data as described in the Privacy Policy")
- A link to the Privacy Policy page on the website
- A data retention policy (how long form data is stored, who has access)

### Q3: Do we need a database for contact form submissions?

**No.** Google Forms stores responses in Google Sheets automatically. This is sufficient. Define a data retention schedule and restrict access to the Google Sheet.

### Q4: Do we need Google reCAPTCHA v3?

**Not if using Google Forms.** Google Forms has built-in spam protection. If a custom-built form is used instead, reCAPTCHA v3 is recommended.

### Q5: Are there privacy concerns for a public website?

**Yes.** Even without user accounts, GDPR applies when collecting personal data (contact forms, analytics). Required measures:

- Privacy Policy page
- Cookie consent banner (if using analytics/third-party scripts)
- GDPR consent checkbox on forms
- Consent considerations for photos of identifiable people at events

---

## Open Questions Summary

| # | Question | Status |
|---|----------|--------|
| 1 | Is English included from launch, or added later? | Pending |
| 2 | Is a domain name already purchased? Who owns it? | Pending |
| 3 | Who provides initial content? Is any of it ready? | Pending |
| 4 | Preferred analytics tool? (Google Analytics, Plausible, etc.) | Pending |
| 5 | Is there a plan for an external newsletter service? | Pending |
| 6 | Is member enrollment a separate form or combined with contact? | Pending |
| 7 | What hosting/platform approach is preferred? | Pending |
