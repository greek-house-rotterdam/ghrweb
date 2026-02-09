# Greek House Website

## Prioritization of features to display on main page:

Primary:

Προσφατα νεα & ανακοινωσεις

Δρασεις ανα ομαδα

Χορευτικο

Μαθηματα ολλανδικων/εικαστικων/κλπ

Συναντησεις

Ημερολογιο με upcoming events

Χρησιμες πληροφοριες

Partners

Ελληνικοι φορεις

κλπ

Links to Tabs/Subpages/

80 χρονια ελληνικο σπιτι

Contact Us

FAQ

About us

Application form: Γινε μελος (φιλος, μελος, υποψηφιο μελος)

## Primary audience:

Webpage is primarily addressing the younger greek people in the Netherlands. 

## Discoverability

Χρειαζομαστε SEO. Πρεπει να κανει apply σε καθε content update (e.g. new post) στο website. 

Nice to have: GEO / AEO (for AI engine discoverability)

## **Success Metric**

Μετρησιμα KPIs:

- Αυξηση (%) στην επισκεψιμοτητα του website
- Αυξηση αριθμου μελων (μεσω του website)
- Αυξηση αριθμου συμμετεχοντων σε δρασεις/εκδηλωσεις (μεσω του website)
- Μειωση (%) επαναλαμβανομενων emai:
    - αριθμος μελων (ή επισκεπτων) / επαναλαμβανομενα email
- Two surveys to be filled out by current volunteers:
    - 1 now, 1 in 2027
    - what they expect from the website, how useful it has been to them, etc

## Δομη κ Content

**Βασικες σελιδες:** *Home, History (80 years), Teams, News, Events, Contact, About Us*. Other?

## **Contact Form**

- Simple Form (Name, Email, Message).
    - GDPR compliance
    - επιθυμω να λαμβανω ενημερωσεις / newsletters
- Interactive Google Map (Location of Greek House).
- Direct Contact Details (Phone, Email, Social Icons).
- **Specific Call-to-Action (CTA):** "Γίνε Εθελοντής" ή "Γράψου Μέλος".

## Accessibility & Privacy Control

Public access, no restrictions. No privacy control (no user log in / sign in).

The following teams will have the permission to publish/update content on the website:

- Ομαδα απο admins / editors
- Διοικητικο Συμβουλιο
- Πολιτιστικη ομαδα

**Admin access**

- Start with single tier admin access
- Later apply admin access with multi-tier privileges

The users must not be able to upload any type of content to the website

- For example: Ο χρηστης θα μπορουσε να ανεβαζει το CV του σε περιπτωση που θελει να κανει apply για εθελοντης. Αυτο θα αυξησει κατα πολυ το s**ecurity/privacy risk** και τις απαιτήσεις του **Hosting.** Επομενως αποριπτεται. Οποιουδηποτε ειδους τετοια επικοινωνια θα γινεται manually μεσω αλλων μορφων επικοινωνιας (email, etc).

## Communications

News (and newsletter) will be posted on the website. No email dispatch, no notifications. The news will also be posted on social media, linking to the full news page on the website.

## Event registration

This is a future feature we may want to add. Users would be able to track events and register. 

Preferebly we are looking for automated solution using 3rd party event tracking/registration, e.g. using Eventbrite or other plugins

- Requirements:
    - The users should be able to track events, and be informed about upcoming events
    - The users should be able to register to events (e.g. using QR code via Eventbrite) and be notified about their registration and about any updates to their events (e.g. time shift, change of date, etc)
    - The admin of the website should have access to the event registrations; either on a custom registry or on via a 3rd party UI (e.g. eventbrite)
    - Waiting list and cancelation would be nice-to-haves.

## WebPage Amdin

We need to have webpage admin controls that are easy to use by people who have only beginner technical knowledge. Tiered-access levels (admin, editor, etc) should be configured.

## **Live Social Media Feeds**

Mandatory: 

- icons-links to social media pages of the organization
- instagram, facebook, spotify, etc

Debatable:

- live social media feed
    - should be lightweight
    - should be automated/standardised
    - should not “clutter” the page visually

## Development

- Set up would preferably be developed with as much code as possible. Otherwise, automated templates should be used. Not desired is a development style through drawing manually on Canvas, Figma, etc.
- Speed of development is paramount
- Easy of later use by non-technical people is also paramount
- If using Github for (part of) the page, then consider using automated github actions for module updates, SEO, translation, GEO. Otehrwise, the platform serving the webpage should provide ready-made UI solutions that non-technical people can use to easily update the modules and post/update/delete news on the website.

## Translation

Automated. High quality. Preferable: AI solution, e.g.:

- DeepL from Google
- Server provider (e.g. Hostinger) automated solution
- Github action (using AI)

The website is trilingual (Greek/Dutch/English).

## Style & Aesthetics (Το "Vibe")

- **Visual Identity:** π.χ. Modern/Minimalist
    - not like this: [https://ekbru.be/](https://ekbru.be/)
    - best: modern, clean, minimal
    - attract younger ages

No need for high contrast / large fonts

## Logistics κ Security

- Annual renewal is ok
- Billing to be handled by the organisation (they provide credit card)
- After development, I (the developer) will maintain the website for the first 3 months. After that I will hand it over to the organisation where much less technical people will take over. For more serious technical tasks, I will still be around, but preferably not for the week-to-week operations.

## Contact Form

- use Google Form if possible
- After sumbission, the organization should receive an email with the user request and data
- user data: name, email, phone number(optional), email,
- to be filled out by user:
    - routing: “already a member”, “want to become a member”, “general question”, “volunteering”, etc
    - “other” option also available with text box popping up if selected
- after submission: “thank you” message is displayed also informing about when the volunteer should wait for a reply (no need to send email)
- **anti-spam measures:** we don’t want our emails to land to the spam page

## Payments & Subscriptions

- The website will not handle subscriptions for the organization.
- The website will not handle payments.

## Questions

- what content can be uploaded to the website
    - type
    - size
    - other concerns
- Since we to be using Google Forms for the contact form and for the member enrolment:
    - **is** GDPR Compliance checkbox still needed somewhere/somehow?
    - do we need to sustain a database of these contact forms?
- do we need **Google reCAPTCHA v3**?
- the webpage is public, would there still be any privacy concerns?