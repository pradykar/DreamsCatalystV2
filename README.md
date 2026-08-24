# DreamsCatalyst — Multilingual Static Site

A faithful static clone of [dreamscatalyst.com](https://www.dreamscatalyst.com)
(GoDaddy Website Builder) with four language versions:

- **EN** — English baseline (root, original slugs)
- **한국어 (ko)** — `/ko/`
- **日本語 (ja)** — `/ja/`
- **中文 (zh-Hans)** — `/zh/`

14 pages × 4 languages = 56 HTML pages, plain HTML/CSS/JS (no build system
required at deploy time). Ready for GitHub + Cloudflare Pages.

## Structure

```
site/
├── index.html                    EN home
├── esl/                          EN pages (original slugs)
├── ko/  ja/  zh/                 translated pages (clean slugs)
│   └── esl/
│       └── index.html
├── manifest.webmanifest          self-hosted PWA manifest
├── TRANSLATION-NOTES.md          adaptation decisions + scope findings
└── QA-CHECKLIST.md               per-language/per-page verification
```

## Regenerating the site

```bash
python3 build.py    # reads source/*.html + translations/<lang>/*.json -> site/
```

Requires: python3, beautifulsoup4.

## Deploy (Cloudflare Pages)

- No build command required; publish directory = `site/` (repo root).
- Preview deployments on the PR branch work out of the box (`*.pages.dev`).
- Domain cutover to dreamscatalyst.com is a separate future task (this phase
  does not touch GoDaddy DNS/hosting).

## Language switcher & SEO

- Fixed language switcher (EN | 한국어 | 日本語 | 中文) on every page.
- `hreflang` (en/ko/ja/zh-Hans/x-default), `lang` attributes, and per-language
  meta title/description/OG/Twitter on every page.

## Booking / account buttons

Booking & account buttons point to the live GoDaddy site
(`https://www.dreamscatalyst.com/m/...`) so bookings keep working — see
TRANSLATION-NOTES.md §2 for the rationale and how to switch to mailto stubs.
