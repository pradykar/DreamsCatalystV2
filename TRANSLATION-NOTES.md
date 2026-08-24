# Translation Notes — DreamsCatalyst Multilingual Clone

Project: faithful static clone of https://www.dreamscatalyst.com with Korean (ko),
Japanese (ja), and Simplified Chinese (zh-Hans) versions.

## 1. Scope & pages

The source site has **14 static pages**, not the 10 in the original brief. The
sitemap (sitemap.website.xml) plus the live nav reveal four additional pages that
all return HTTP 200 and are linked from the site:

| Page | English slug | Source of discovery |
|---|---|---|
| Real Estate | `/real-estate` | sitemap |
| ESL – Misc Expat Services | `/esl-misc-expat-services` | sitemap |
| ESL – Special Services | `/esl-special-services` | sitemap |
| True North AI | `/true-north-ai` | nav/footer (NOT in sitemap) |

All 14 pages were cloned in all four language versions (EN + KO/JA/ZH = 56 pages).
`/true-north-ai` was discovered only through the live page nav — a good reminder
that sitemaps can lag the actual site.

Out of scope (dynamic GoDaddy platform, no static equivalent): `/m/account`,
`/m/bookings`, `/m/create-account`, the reCAPTCHA contact-form backend, and the
GoDaddy online-appointments booking page (`/esl/ola/services/trial-intro-session`,
found in sitemap.ola.xml).

## 2. Booking / account / contact form handling (decision)

**Decision: Option (a)** — booking/account buttons in ALL language versions link
to the **live English GoDaddy pages** (`https://www.dreamscatalyst.com/m/...`).
The contact form is kept in place as the GoDaddy form markup (it posts to the
GoDaddy backend and still functions when the static clone is hosted on a domain),
with the reCAPTCHA notice kept intact.

Rationale: keeps bookings functional with zero maintenance; no broken mailto
stubs; matches the site owner's current workflow. If a fully static experience is
preferred later, swap these hrefs for mailto:hello@dreamscatalyst.com — the build
script's `M_LINKS` dict makes this a one-line change.

## 3. Adapted (non-literal) phrases

These were adapted for naturalness / cultural fit rather than word-for-word
translation:

| English source | Why adapted |
|---|---|
| "Unlocking Dreams, One Conversation at a Time" | Idiomatic tagline. Direct translation sounds flat in KO/JA/ZH. Adapted to preserve the metaphor of opening/awakening potential through conversation: KO "꿈을 여는 순간, 한 번의 대화에서 시작됩니다" (the moment of unlocking a dream begins with one conversation); JA "夢を開く鍵は、ひとつの会話から" (the key to opening dreams is one conversation); ZH "一次对话，开启梦想之门" (one conversation opens the door of dreams). |
| "Learning is 'a breeze' (so easy!) and time 'will fly'" | English idioms with parenthetical explanations. Translated the meaning and kept the friendly parenthetical style; the idioms themselves have no direct equivalents, so the explanation carries the intent. |
| "Shopping...it's the American Way!" | Cultural reference. Kept the slogan feel with local punctuation conventions; no equivalent idiom exists in the target languages. |
| "Happy Clients, Happy Life!" | Rhyming slogan; translated for the same alliterative/repetitive feel rather than literally. |
| "Your True North" | Metaphor of a guiding direction/north star. In KO/JA "True North" is kept as a loan term with a clarifying gloss (진정한 북극성 / トゥルーノース（真北）) since the phrase is a known concept in self-help contexts; ZH renders it with the English term plus gloss. |
| "Bay Area Tours & Field Trips" | "Field Trip" has no single-word equivalent; KO uses 현장 학습 (on-site learning), JA uses フィールドトリップ (loan word, widely understood), ZH uses 实地考察 (on-site investigation/study). |
| "Getting to Know You" (trial session) | Idiosyncratic session name; translated as "mutual getting-to-know" in each language (서로 알아가는 / お互いを知る / 互相了解). |
| "Add a footnote if this applies to your business" / "Add a description about this category/item" | GoDaddy template placeholder text still present on the live site (esl-misc-expat-services, esl-special-services). Translated literally so the clone matches the source; flagged for the owner to replace with real copy. |
| "XX Tailored courses focusing on…" (women-centered-coaching) | Live site has a stray "XX" prefix (copy/paste artifact of the professional-services blurb). Preserved as-is in translations to stay faithful; flagged for the owner. |

## 4. Kept as-is (not translated)

Per the brief: business name **DreamsCatalyst**, founder name **Mika L. Stratton**,
phone **(408) 475-6452**, physical region **San Francisco Bay Area, California, USA**,
email addresses, social handles/URLs, DRE license number, `tel:`/`mailto:` links,
and the copyright line (legal boilerplate).

## 5. Locale conventions

- Hours: "09:00 am – 05:00 pm" → locale form per language (오전 9:00 – 오후 5:00 /
  午前9:00 – 午後5:00 / 上午9:00 – 下午5:00).
- Weekday names translated (Mon–Sun → 월–일 / 月–日 / 周一–周日).
- Prices kept in USD with per-hour notation adapted ($85/hr → 시간당 $85 / 1時間あたり$85 / $85/小时).
- `og:locale` set to ko_KR / ja_JP / zh_CN.
- `<html lang>`: en / ko / ja / zh-Hans. Body layout class `locale-*`/`lang-*`
  (GoDaddy artifact) corrected per language.

## 6. Technical approach

- All CSS is inlined by GoDaddy (no external stylesheets), so each page is
  self-contained; the clone preserves the byte-identical class structure.
- Images/fonts reference the original `img1.wsimg.com` CDN URLs directly (no
  re-hosting); `manifest.webmanifest` was fetched and self-hosted at the site root.
- The language switcher is injected into every page's header (fixed top-right
  pill: EN | 한국어 | 日本語 | 中文), highlighting the current language.
- hreflang tags (en / ko / ja / zh-Hans / x-default) added to every page head.
- Internal links rewritten per language folder using clean URL-safe slugs
  (`esl-tours-and-field-trips`, `custom-tutoring-coaching` etc. — the `&` and
  `/` in the original English slugs are only kept for the English baseline).
- English baseline pages keep their original slugs (byte-identical except the
  injected switcher + hreflang), so `/esl-tours-%26-field-trips/` and
  `/custom-tutoring%2Fcoaching/` still resolve.

## 7. Known source-site quirks preserved

- `esl-special-services` is mostly GoDaddy starter template ("Welcome", "First
  Item", "Add a description…") — cloned as-is, translated.
- `/true-north-ai` button label typo "SupPort True North" — preserved typo in EN,
  translated cleanly in other languages.
- The site's "Show More/Show Less" blocks duplicate their content (collapsed +
  expanded copies); both copies were translated.
