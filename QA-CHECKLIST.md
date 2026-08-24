# QA Checklist — DreamsCatalyst Multilingual Clone

Verified per language per page. All checks below were executed programmatically
against the built `docs/` output (56 pages: 14 EN + 14 KO + 14 JA + 14 ZH), plus
a real-browser (headless Chrome) render of representative pages.

Legend: ✅ passed · ⚠️ known deviation (documented)

## 1. Page inventory (14 pages × 4 languages = 56)

| Page | EN | KO | JA | ZH |
|---|---|---|---|---|
| Home | ✅ | ✅ | ✅ | ✅ |
| ESL | ✅ | ✅ | ✅ | ✅ |
| ESL – Tours & Field Trips | ✅ | ✅ | ✅ | ✅ |
| ESL – Professional Services | ✅ | ✅ | ✅ | ✅ |
| Women-Centered Coaching | ✅ | ✅ | ✅ | ✅ |
| ESL – Corporate Partners | ✅ | ✅ | ✅ | ✅ |
| ESL – Immigration Partners | ✅ | ✅ | ✅ | ✅ |
| ESL – FAQs | ✅ | ✅ | ✅ | ✅ |
| Custom Tutoring/Coaching | ✅ | ✅ | ✅ | ✅ |
| About Us | ✅ | ✅ | ✅ | ✅ |
| Real Estate | ✅ | ✅ | ✅ | ✅ |
| ESL – Misc Expat Services | ✅ | ✅ | ✅ | ✅ |
| ESL – Special Services | ✅ | ✅ | ✅ | ✅ |
| True North AI | ✅ | ✅ | ✅ | ✅ |

## 2. Visual parity with English source

- ✅ **Class/structure identity**: DOM structure (element sequence + class
  attributes, excluding injected switcher and the intentional `locale-*`/`lang-*`
  fix) is identical between each translated page and its English original. The
  only structural diffs found were the intentional locale-class corrections.
- ✅ All inline styles, `<style>` blocks, images, fonts, and responsive
  breakpoints preserved verbatim.
- ✅ Images/backgrounds reference original GoDaddy CDN URLs (`img1.wsimg.com`);
  no broken image refs.
- ⚠️ Text length naturally differs per language (translation); line heights and
  wrapping follow the original CSS. CJK text is typically more compact; Korean
  can run slightly longer — no layout-breaking overflow observed in browser
  render of representative pages (KO ESL, ZH Women-Centered).

## 3. Internal links resolve within each language

- ✅ 1,548 internal links checked across all 56 pages → **0 broken**.
- ✅ Every page links only within its own language folder (e.g. `/ko/esl/` pages
  link to `/ko/...`).
- ✅ English baseline keeps original slugs; encoded URLs (`/esl-tours-%26-field-trips/`,
  `/custom-tutoring%2Fcoaching/`) resolve (verified via local server → HTTP 200).
- ✅ `/m/account`, `/m/bookings`, `/m/create-account` → live GoDaddy pages
  (`https://www.dreamscatalyst.com/m/...`), per decision in TRANSLATION-NOTES §2.
- ✅ `tel:`, `mailto:`, social, external links untouched.
- ✅ `manifest.webmanifest` self-hosted at root; referenced on all pages.

## 4. Language switcher works in both directions

- ✅ Switcher present on every page (all 56), fixed top-right: EN | 한국어 | 日本語 | 中文.
- ✅ Current language highlighted (teal fill), others linked.
- ✅ Each switcher link points to the equivalent page in the other language
  (e.g. from `/ko/esl/` → EN `/esl/`, JA `/ja/esl/`, ZH `/zh/esl/`).
- ✅ Round-trip: EN page → KO page → EN page resolves (verified by link check +
  browser render).

## 5. hreflang / lang attributes

- ✅ `<html lang>`: `en`, `ko`, `ja`, `zh-Hans` on the respective versions.
- ✅ hreflang block in every page head: `en`, `ko`, `ja`, `zh-Hans`, `x-default`.
- ✅ `og:locale`: `en_US` / `ko_KR` / `ja_JP` / `zh_CN`.
- ✅ Body layout classes corrected: `locale-ko-KR lang-ko`, `locale-ja-JP
  lang-ja`, `locale-zh-CN lang-zh-Hans` (GoDaddy hardcodes `locale-en-US lang-en`).
- ✅ Per-page translated `<title>` + meta description + og/twitter tags.
- ⚠️ hreflang URLs use the canonical `https://dreamscatalyst.com/...` base
  (production target). On the Cloudflare Pages preview domain these are
  placeholders until domain cutover — expected for this phase.

## 6. No leftover English / placeholders

- ✅ Translation coverage: all 406 unique visible strings + 15 attribute strings
  (alt/aria-label/originalText) + 14 meta sets translated in all 3 languages.
- ✅ Zero untranslated content nodes found (exact-match scan across all 56 pages).
- ✅ Remaining English tokens are intentional keeps: brand/founder name, phone,
  address, DRE#, email addresses, social handles, "Copyright… All Rights
  Reserved", and the quoted term "Field Trip Studies" inside translated KO text.
- ⚠️ `filler@godaddy.com` appears in the footer contact form of the *live* site;
  preserved as-is (matches source; owner should replace with real email).
- ⚠️ Template placeholder copy ("Add a description…", "First Item", "XX…") exists
  on the *live* site and is translated faithfully — see TRANSLATION-NOTES §3/§7.

## 7. Functional behaviors preserved

- ✅ "Show More / Show Less" toggles (checkbox + CSS mechanism) present and
  translated (더 보기/접기, もっと見る/閉じる, 展开/收起) — verified in browser render.
- ✅ Mobile hamburger nav intact (aria-label translated).
- ✅ Contact form markup + reCAPTCHA notice intact.
- ✅ Cookie banner text translated (동의/거부, 同意する/拒否する, 同意/拒绝).
- ✅ Social links intact (Facebook, Instagram, LinkedIn, Yelp, YouTube).

## 8. Browser render spot checks (headless Chrome)

| Page | Result |
|---|---|
| `/ko/esl/` | ✅ Korean headings/FAQ/CTAs render; switcher + hreflang present; Show More toggles found |
| `/zh/women-centered-coaching/` | ✅ Chinese content renders; `lang="zh-Hans"` correct |
| `/ko/` (home) | ✅ Korean nav labels render |
| EN `/esl-tours-%26-field-trips/` | ✅ HTTP 200 |
| EN `/custom-tutoring%2Fcoaching/` | ✅ HTTP 200 |

## 9. Build reproducibility

- ✅ `build.py` regenerates the entire `docs/` deterministically from
  `source/*.html` + `translations/<lang>/*.json` (56 pages).
- ✅ Source HTML captured 2026-08-21 from live site (GoDaddy Website Builder 8.0.0).

---

Signed off: built & verified end-to-end (fetch → translate → build → link check →
browser render). Remaining external steps: GitHub push + Cloudflare Pages (need
user credentials/auth).
