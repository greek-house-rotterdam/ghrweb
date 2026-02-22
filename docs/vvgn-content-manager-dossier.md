# VVGN Content Dossier (for Content Manager)

This briefing converts the scrape into an editor-friendly view of the content: what to migrate, how it is organized today, and what tone/style patterns appear in real posts.

## 1) Executive snapshot

- Pages scraped in total: **495**
- URL entries that look like posts: **215**
- Unique posts after deduplication (same title/date/language merged): **187**
- Posts with full textual body: **73**
- Placeholder-only posts: **114**

Important: most Dutch post URLs are placeholders that point readers to another language version.

## 2) Content structure of the current site

| Page type | Count | Practical meaning |
|---|---:|---|
| Post | 215 | Actual article pages |
| Tag page | 222 | Index pages used for browsing by tag |
| Category page | 47 | Index pages used for browsing by category |
| Author page | 7 | Author archive pages |
| Pagination page | 3 | Continuation pages in archives |
| Site/static page | 1 | Homepage/static page |

Interpretation: editorial value is concentrated in posts, while many pages are archive/navigation layers.

## 3) Post corpus quality and language coverage

### By language (unique posts)

- **Dutch: 119** total (5 full text, 114 placeholder-only)
- **Greek: 64** total (64 full text, 0 placeholder-only)
- **English: 4** total (4 full text, 0 placeholder-only)

### By year (unique posts)

- **2017: 1 posts**
- **2018: 9 posts**
- **2019: 38 posts**
- **2020: 29 posts**
- **2021: 36 posts**
- **2022: 31 posts**
- **2023: 35 posts**
- **2024: 8 posts**

Full-text post length profile: **197.3 avg words**, **164 median**, range **16-698** words.

## 4) Main content themes (from full-text posts)

### Inferred content types

- **Cultural program activity** — 26 posts
- **Course / class** — 14 posts
- **Festive event** — 10 posts
- **Community update** — 7 posts
- **Workshop** — 6 posts
- **General announcement** — 5 posts
- **Public event promotion** — 5 posts

### Top categories (primary category)

- **Δραστηριότητες του Ελληνικού Σπιτιού στο Ρότερνταμ** — 10 posts
- **Γενικές Ανακοινώσεις για την Ένωση Ελλήνων Ολλανδίας** — 10 posts
- **Μαθήματα Ολλανδικών** — 10 posts
- **Book Club / Λέσχη Ανάγνωσης** — 8 posts
- **Η Θεατρική Ομάδα του Ελληνικού Σπιτιού στο Ρότερνταμ** — 6 posts
- **Η Χορωδία του Ελληνικού Σπιτιού στο Ρότερνταμ** — 5 posts
- **Διαδικτυακές πολιτιστικές συναντήσεις** — 5 posts
- **Mode & lekkernijen** — 4 posts
- **Workshops Εικαστικών** — 4 posts
- **Μαθήματα μουσικής & μουσικών οργάνων** — 3 posts
- **Δείξε μου την πόλη σου!** — 2 posts
- **Workshops Μαγειρικής** — 2 posts

## 5) Tone, style, and writing patterns

Observed from full-text posts:

- **Service-oriented and practical**: frequent logistics and planning details (dates, schedules, instructions).
- **Community voice**: direct calls to members/friends are common.
- **Action-first copy**: calls-to-action in **29/73** full-text posts.
- **Operational details** are often embedded: email in **20** posts, phone-like contact in **29** posts, prices in **19** posts.
- **Warm/informal flavor**: emoji usage appears in **3** full-text posts.

## 6) Migration recommendation for content manager

1. Prioritize **full-text posts** first (these carry the real narrative and operational value).
2. Treat **placeholder-only Dutch posts** as language-gap items; link them to the source Greek/English content during migration.
3. Migrate category/tag structures after core posts, to avoid spending time on archive pages before primary content is stable.

## 7) Representative examples (full-text posts)

### Community update

- **2023-10-05** — Παιδική παράσταση “Σταχτο-πού’ντην” – SOLD OUT (Greek)
  - Category: Δραστηριότητες του Ελληνικού Σπιτιού στο Ρότερνταμ
  - Context: SOLD OUT Είμαστε στην ευχάριστη θέση να ανακοινώσουμε πως τα εισιτήρια που είχαν διατεθεί προς προπώληση για την Σταχτο-πού’ντην | Παράσταση αφήγησης λαϊκών παραμυθιών με μουσική, εξαντλήθηκαν! Eυχαριστούμε όλες και όλους, μικρούς και μεγάλους για το ενδιαφέρον σας που είχε ως αποτέλεσμα, 10 ημέρες πριν την ...
  - URL: https://vvgn.eu/el/2023/10/05/%CF%80%CE%B1%CE%B9%CE%B4%CE%B9%CE%BA%CE%AE-%CF%80%CE%B1%CF%81%CE%AC%CF%83%CF%84%CE%B1%CF%83%CE%B7-%CF%83%CF%84%CE%B1%CF%87%CF%84%CE%BF-%CF%80%CE%BF%CF%8D%CE%BD%CF%84%CE%B7%CE%BD-sold-ou/
- **2022-11-06** — Mode & lekkernijen – November 2022 (Dutch)
  - Category: Mode & lekkernijen
  - Context: Beste leden en vrienden van de Vereniging van Grieken in Nederland / Het Griekse Huis in Rotterdam, Hiermede willen wij u voor een gezellige middag uitnodigen op zondag 27 november 2022 van 12:00-15.00 uur in het Griekse Huis in Rotterdam aan de Van Vollenhovenstraat 18. Vrienden ...
  - URL: https://vvgn.eu/nl/2022/11/06/%ce%bc%cf%8c%ce%b4%ce%b1-%ce%bb%ce%b9%cf%87%ce%bf%cf%85%ce%b4%ce%b9%ce%ad%cf%82-3/

### Course / class

- **2024-09-08** — Online μαθήματα ολλανδικής γλώσσας: Φθινόπωρο – Χειμώνας 2024 – 2025 (Greek)
  - Category: Μαθήματα Ολλανδικών
  - Context: Αγαπητά μέλη και φίλοι/ες του Ελληνικού Σπιτιού στο Ρότερνταμ, Η νέα σχολική – ακαδημαϊκή χρονιά ξεκινά και θέλουμε να σας ευχηθούμε ολόψυχα ένα όμορφο φθινόπωρο και έναν δημιουργικό χειμώνα, με ψυχική και σωματική υγεία! Είμαστε στην ευχάριστη θέση να σας ανακοινώσουμε την έναρξη νέων online τμημάτων ...
  - URL: https://vvgn.eu/el/2024/09/08/online-%CE%BC%CE%B1%CE%B8%CE%AE%CE%BC%CE%B1%CF%84%CE%B1-%CE%BF%CE%BB%CE%BB%CE%B1%CE%BD%CE%B4%CE%B9%CE%BA%CE%AE%CF%82-%CE%B3%CE%BB%CF%8E%CF%83%CF%83%CE%B1%CF%82-%CF%86%CE%B8%CE%B9%CE%BD%CF%8C%CF%80/
- **2024-02-16** — Νέος κύκλος μαθημάτων ολλανδικής γλώσσας (Άνοιξη – καλοκαίρι 2024) (Greek)
  - Category: Μαθήματα Ολλανδικών
  - Context: Αγαπητά μέλη και φίλοι/ες του Ελληνικού Σπιτιού στο Ρότερνταμ, Ευχόμαστε ολόψυχα να είστε όλοι καλά! Είμαστε στην ευχάριστη θέση να σας ανακοινώσουμε την έναρξη νέων – online – τμημάτων εκμάθησης της ολλανδικής γλώσσας για αρχάριους και προχωρημένους, διάρκειας 17 εβδομάδων. – Στα μαθήματα μπορούν να εγγραφούν ...
  - URL: https://vvgn.eu/el/2024/02/16/%ce%bd%ce%ad%ce%bf%cf%82-%ce%ba%cf%8d%ce%ba%ce%bb%ce%bf%cf%82-%ce%bc%ce%b1%ce%b8%ce%b7%ce%bc%ce%ac%cf%84%cf%89%ce%bd-%ce%bf%ce%bb%ce%bb%ce%b1%ce%bd%ce%b4%ce%b9%ce%ba%ce%ae%cf%82-%ce%b3%ce%bb%cf%8e-3/

### Cultural program activity

- **2024-05-28** — A Shak3speare’s Night: Πτυχές του έργου του (Greek)
  - Category: Η Θεατρική Ομάδα του Ελληνικού Σπιτιού στο Ρότερνταμ
  - Context: Η Θεατρική Ομάδα “Παρακμή” του Ελληνικού Σπιτιού στο Ρότερνταμ / Ένωσης Ελλήνων Ολλανδίας μετά την περσινή sold-out “Βραδιά Θεάτρου” παρουσιάζει φέτος μια μοναδική Βραδιά για τον Σαίξπηρ με 3 έργα του να εναλλάσσονται και να συνυπάρχουν σε ένα λυρικό χορό που στόχο έχει την κορύφωση και ...
  - URL: https://vvgn.eu/el/2024/05/28/a-shak3speares-night-%cf%80%cf%84%cf%85%cf%87%ce%ad%cf%82-%cf%84%ce%bf%cf%85-%ce%ad%cf%81%ce%b3%ce%bf%cf%85-%cf%84%ce%bf%cf%85/
- **2023-11-13** — 1o Book club / Λέσχη Ανάγνωσης 2023-2024 (Greek)
  - Category: Book Club / Λέσχη Ανάγνωσης
  - Context: Με χαρά και ανυπομονησία σας ανακοινώνουμε την επανεκκίνηση του Book Club του Ελληνικού Σπιτιού στο Ρότερνταμ!! Αν ένα συνηθισμένο απόγευμα σας βρίσκει με τις μούρες σας χωμένες σε ένα βιβλίο. Αν αγαπάτε το διάβασμα, σας αρέσει να γνωρίζετε νέες απόψεις και να βλέπετε το νόμισμα και ...
  - URL: https://vvgn.eu/el/2023/11/13/1o-book-club-%ce%bb%ce%ad%cf%83%cf%87%ce%b7-%ce%b1%ce%bd%ce%ac%ce%b3%ce%bd%cf%89%cf%83%ce%b7%cf%82-2023-2024/

### Festive event

- **2023-11-09** — Η συμμετοχή μας στο GreekHubFest στις 26 Νοεμβρίου 2023 (Greek)
  - Category: Γενικές Ανακοινώσεις για την Ένωση Ελλήνων Ολλανδίας
  - Context: Γεμάτοι χαρά και ανυπομονησία, θέλουμε να σας ενημερώσουμε για τη συμμετοχή μας στο Greekhubfest – Γνώση, εμπειρία, διάδραση: Η Ελλάδα λάμπει στην Ευρώπη ! Την Κυριακή 26/11 και ώρα 18:00, εθελοντές και τα μέλη του Het Griekse Huis in Rotterdam θα μιλήσουμε ζωντανά για την ιστορία ...
  - URL: https://vvgn.eu/el/2023/11/09/%CE%B7-%CF%83%CF%85%CE%BC%CE%BC%CE%B5%CF%84%CE%BF%CF%87%CE%AE-%CE%BC%CE%B1%CF%82-%CF%83%CF%84%CE%BF-greekhubfest-%CF%83%CF%84%CE%B9%CF%82-26-%CE%BD%CE%BF%CE%B5%CE%BC%CE%B2%CF%81%CE%AF%CE%BF%CF%85-2023/
- **2022-10-19** — “Ο Γιάννης και το πεύκο”: Διαδραστική παράσταση οικολογικού περιεχομένου για παιδιά 5-12 ετών (Greek)
  - Category: Δραστηριότητες του Ελληνικού Σπιτιού στο Ρότερνταμ
  - Context: Κυριακή 20 Νοεμβρίου και ώρα 15:00: Το Ελληνικό Σπίτι / Ένωση Ελλήνων Ολλανδίας φιλοξενεί στον ισόγειο χώρο του την νέα παράσταση των Hippo Theater Group, μια παράσταση για μικρούς αλλά και για μεγάλους! Η θεατρική ομάδα Hippo παρουσιάζει την διαδραστική θεατρική παράσταση οικολογικού περιεχομένου, με τίτλο ...
  - URL: https://vvgn.eu/el/2022/10/19/%CE%BF-%CE%B3%CE%B9%CE%AC%CE%BD%CE%BD%CE%B7%CF%82-%CE%BA%CE%B1%CE%B9-%CF%84%CE%BF-%CF%80%CE%B5%CF%8D%CE%BA%CE%BF-%CE%B4%CE%B9%CE%B1%CE%B4%CF%81%CE%B1%CF%83%CF%84%CE%B9%CE%BA%CE%AE-%CF%80%CE%B1/

### General announcement

- **2022-03-25** — Συναυλία ‘’THE AGORA UNVEILED’’ (Greek)
  - Category: Γενικές Ανακοινώσεις για την Ένωση Ελλήνων Ολλανδίας
  - Context: Με χαρά και τιμή η Πολιτιστική Ομάδα “Το Ελληνικό Σπίτι στο Ρότερνταμ” της Ένωσης Ελλήνων Ολλανδίας ανακοινώνει τη συνεργασία του Συλλόγου μας με τους MUSICENTRY & Foundation IHOS Amsterdam για τη διεξαγωγή της συναυλίας ‘’THE AGORA UNVEILED’’. Ως σπόνσορες & χορηγοί επικοινωνίας νιώθουμε ιδιαίτερη υπερηφάνεια για ...
  - URL: https://vvgn.eu/el/2022/03/25/%CF%83%CF%85%CE%BD%CE%B1%CF%85%CE%BB%CE%AF%CE%B1-the-agora-unveiled/
- **2020-04-18** — Λίγες σκέψεις μας για εσάς & Ευχές για Καλό Πάσχα (Greek)
  - Category: Γενικές Ανακοινώσεις για την Ένωση Ελλήνων Ολλανδίας
  - Context: Αγαπητά μέλη και φίλοι/ες της Ένωσης Ελλήνων Ολλανδίας, Αναρτούμε αυτό το post για να μοιραστούμε μερικές σκέψεις μας μαζί σας και παράλληλα για να σας ευχηθούμε εν όψει της ημέρας του Πάσχα. Αναμφισβήτητα, από τα μέσα Μαρτίου, όλοι και όλες μας ζούμε μια περίοδο γεμάτη προκλήσεις ...
  - URL: https://vvgn.eu/el/2020/04/18/english-%CE%BB%CE%AF%CE%B3%CE%B5%CF%82-%CF%83%CE%BA%CE%AD%CF%88%CE%B5%CE%B9%CF%82-%CE%BC%CE%B1%CF%82-%CE%B3%CE%B9%CE%B1-%CE%B5%CF%83%CE%AC%CF%82-%CE%B5%CF%85%CF%87%CE%AD%CF%82-%CE%B3%CE%B9%CE%B1/

### Public event promotion

- **2024-10-10** — 🚀 OPEN DAG . 26 10 2024 . Ενημέρωση Δράσεων στο Ελληνικό Σπίτι (Greek)
  - Category: Δραστηριότητες του Ελληνικού Σπιτιού στο Ρότερνταμ
  - Context: Tο Ελληνικό Σπίτι στο Ρότερνταμ ανοίγει τις πόρτες του για να σας υποδεχτεί και σας καλεί να γνωρίσετε τις δραστηριότητες και δράσεις της νέας χρονιάς! Το Σάββατο 26 Οκτωβρίου σας υποδεχόμαστε και μαζί με τους υπεύθυνους των δράσεων συζητάμε για την δομή, τους στόχους και για ...
  - URL: https://vvgn.eu/el/2024/10/10/%F0%9F%9A%80-open-dag-26-10-2024-%CE%B5%CE%BD%CE%B7%CE%BC%CE%AD%CF%81%CF%89%CF%83%CE%B7-%CE%B4%CF%81%CE%AC%CF%83%CE%B5%CF%89%CE%BD-%CF%83%CF%84%CE%BF-%CE%B5%CE%BB%CE%BB%CE%B7%CE%BD%CE%B9%CE%BA/
- **2023-09-21** — 🚀 OPEN DAG . 07/10/2023 . Ενημέρωση Δράσεων στο Ελληνικό Σπίτι (Greek)
  - Category: Δραστηριότητες του Ελληνικού Σπιτιού στο Ρότερνταμ
  - Context: Tο Ελληνικό Σπίτι στο Ρότερνταμ ανοίγει τις πόρτες του για να σας υποδεχτεί και σας καλεί να γνωρίσετε τις δραστηριότητες και δράσεις της νέας χρονίας! Το Σάββατο 7 Οκτωβρίου σας υποδεχόμαστε και μαζί με τους υπεύθυνους των δράσεων συζητάμε για την δομή, τους στόχους και για ...
  - URL: https://vvgn.eu/el/2023/09/21/1008/

### Workshop

- **2023-12-07** — Workshop Μαγειρικής: Νοέμβριος 2023 – Μάιος 2024 (Greek)
  - Category: Workshops Μαγειρικής
  - Context: 📣Αγαπητά μας μέλη και & φίλοι και φίλες του Ελληνικού Σπιτιού στο Ρότερνταμ, 📅Σας προσκαλούμε κάθε 3η Κυριακή του μήνα (δείτε παρακάτω τις αναγραφόμενες ημερομηνίες) στο “Workshop Μαγειρικής” του Ελληνικού Σπιτιού. Σε κάθε workshop θα μαθαίνουμε να παρασκευάζουμε κάτι καινούριο και διαφορετικό από την ελληνική κουζίνα ...
  - URL: https://vvgn.eu/el/2023/12/07/workshop-%ce%bc%ce%b1%ce%b3%ce%b5%ce%b9%cf%81%ce%b9%ce%ba%ce%ae%cf%82-%ce%bd%ce%bf%ce%ad%ce%bc%ce%b2%cf%81%ce%b9%ce%bf%cf%82-2023-%ce%bc%ce%ac%ce%b9%ce%bf%cf%82-2024/
- **2023-11-05** — 1ο workshop Μαγειρικής στο Ελληνικό Σπίτι στο Ρότερνταμ (Greek)
  - Category: Workshops Μαγειρικής
  - Context: 📣Αγαπητά μας μέλη και & φίλοι και φίλες του Ελληνικού Σπιτιού στο Ρότερνταμ, 📅Σας προσκαλούμε την Κυριακή 26 Νοεμβρίου στο 1ο workshop Μαγειρικής του Ελληνικού Σπιτιού. Σε αυτό το workshop γνωριμίας θα μάθουμε να ζυμώνουμε χωριάτικο ψωμί και ζύμη κουρού για την παρασκευή διαφόρων αρτοσκευασμάτων (τυροπιτάκια, ...
  - URL: https://vvgn.eu/el/2023/11/05/1%CE%BF-workshop-%CE%BC%CE%B1%CE%B3%CE%B5%CE%B9%CF%81%CE%B9%CE%BA%CE%AE%CF%82-%CF%83%CF%84%CE%BF-%CE%B5%CE%BB%CE%BB%CE%B7%CE%BD%CE%B9%CE%BA%CF%8C-%CF%83%CF%80%CE%AF%CF%84%CE%B9-%CF%83%CF%84%CE%BF/

## 8) Files to hand over

- Readable dossier: `docs/vvgn-content-manager-dossier.md`
- Complete post inventory (spreadsheet-friendly): `data/scrapes/vvgn/content-manager-post-inventory.csv`
- Raw crawl details: `data/scrapes/vvgn/manifest.json` and `data/scrapes/vvgn/crawl-report.md`
