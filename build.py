#!/usr/bin/env python3
"""Build the multilingual static DreamsCatalyst site.

Reads the captured GoDaddy source pages (source/*.html), applies the
translation dicts (translations/<lang>/*.json), injects a language switcher,
hreflang/canonical tags, rewrites internal links, and REPLACES the dead
GoDaddy runtime (its scripts on img1.wsimg.com return HTTP 503):
  - lazy images/backgrounds are resolved at build time
  - dead widgets (reviews, appointments, popup, chat, cookie banner, logos,
    html embed) and GoDaddy scripts/branding are removed
  - /assets/site.js provides the hamburger menu, FAQ accordion, contact form

Writes:
  docs/                         English baseline (original slugs)
  docs/ko/ docs/ja/ docs/zh/    translated pages (clean slugs)
  docs/sitemap.xml + everything in static/ (assets, 404 pages, robots, _redirects)
  site/                         exact mirror of docs/ (host may publish either)
"""
import json, os, re, shutil, glob
from urllib.parse import quote, unquote
from bs4 import BeautifulSoup, NavigableString

NL = chr(10)

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = f'{BASE}/source'
OUT = f'{BASE}/docs'   # published folder
MIRROR = f'{BASE}/site'  # kept identical to docs/ until the owner confirms which one the host deploys

SITE_URL = 'https://dreamscatalyst.com'
CONTACT_EMAIL = 'mika@dreamscatalyst.com'
GA4_ID = 'G-K58NN0SKH0'          # the site's own Google Analytics 4 property
FORM_ENDPOINT = ''               # e.g. 'https://formspree.io/f/xxxxxxxx'; '' = mailto fallback in site.js
KEEP_TRUSTEDSITE = True          # re-add the TrustedSite script that lived in the GoDaddy HTML widget
HERO_CTA_TARGET = '/esl'         # "Get Started" on the home hero (was a link to the home page itself)

# slug mapping: source filename -> (english original slug, clean slug)
# esl-special-services is intentionally NOT built: it is an untouched GoDaddy
# starter-template page (redirected to /esl/ via static/_redirects).
PAGES = [
    ('home',                  '/',                         ''),
    ('esl',                   '/esl',                      'esl'),
    ('esl-tours-field-trips', '/esl-tours-%26-field-trips','esl-tours-and-field-trips'),
    ('esl-professional-services', '/esl-professional-services', 'esl-professional-services'),
    ('women-centered-coaching', '/women-centered-coaching', 'women-centered-coaching'),
    ('esl-corporate-partners', '/esl-corporate-partners',   'esl-corporate-partners'),
    ('esl-immigration-partners', '/esl-immigration-partners-1', 'esl-immigration-partners'),
    ('esl-faqs',              '/esl-faqs',                  'esl-faqs'),
    ('custom-tutoring-coaching', '/custom-tutoring%2Fcoaching', 'custom-tutoring-coaching'),
    ('about-us',              '/about-us',                  'about-us'),
    ('real-estate',           '/real-estate',               'real-estate'),
    ('esl-misc-expat-services','/esl-misc-expat-services',  'esl-misc-expat-services'),
    ('true-north-ai',         '/true-north-ai',             'true-north-ai'),
]
NAME2CLEAN = {n: c for n, _, c in PAGES}
EN_SLUG2CLEAN = {e: c for _, e, c in PAGES}

LANG_META = {
    'en':  {'lang': 'en',     'hreflang': 'en',     'label': 'EN',    'dir': ''},
    'ko':  {'lang': 'ko',     'hreflang': 'ko',     'label': '한국어', 'dir': 'ko'},
    'ja':  {'lang': 'ja',     'hreflang': 'ja',     'label': '日本語', 'dir': 'ja'},
    'zh':  {'lang': 'zh-Hans','hreflang': 'zh-Hans','label': '中文',   'dir': 'zh'},
}
LANGS = ['ko', 'ja', 'zh']

DEAD_WIDGETS = ('widget-reviews', 'widget-appointments', 'widget-html', 'widget-logos',
                'widget-popup', 'widget-messaging', 'widget-cookie-banner')

GA4_SNIPPET = (
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>'
    '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
    "gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied'});"
    f"gtag('js',new Date());gtag('config','{GA4_ID}');</script>"
)

LOGO_FILE = f'{BASE}/static/assets/img/logo.png'   # created by tools/localize_assets.py
LOGO_URL = (f'{SITE_URL}/assets/img/logo.png' if os.path.exists(LOGO_FILE) else
            'https://img1.wsimg.com/isteam/ip/911746c9-a317-4496-9588-e22eee9fc874/DreamsCatalyst_Middle%20Long.png')

LOCAL_BUSINESS = {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    '@id': f'{SITE_URL}/#business',
    'name': 'DreamsCatalyst - Mika L. Stratton',
    'url': f'{SITE_URL}/',
    'image': LOGO_URL,
    'telephone': '+1-408-475-6452',
    'email': CONTACT_EMAIL,
    'areaServed': 'San Francisco Bay Area, California, USA',
    'address': {'@type': 'PostalAddress', 'addressRegion': 'CA', 'addressCountry': 'US'},
    'sameAs': [
        'https://www.facebook.com/245039592022998',
        'https://www.instagram.com/DreamsCatalyst',
        'https://www.linkedin.com/company/dreamscatalyst/',
        'https://www.yelp.com/biz/dreamscatalyst-pleasanton-2',
        'https://www.youtube.com/@DreamsCatalyst',
    ],
}


def load_translations(lang):
    d = {}
    for f in sorted(glob.glob(f'{BASE}/translations/{lang}/*.json')):
        d.update(json.load(open(f, encoding='utf-8')))
    return d

def truncate_prefix(translation, ratio):
    """Truncate a translation to approx the same character ratio as the
    English collapsed preview, on a word boundary when possible."""
    n = max(1, int(len(translation) * ratio))
    cut = translation[:n]
    for sep in (' ', '。', '！', '？', '.', '!', '?', '、', '」', '」', '）', ')', '】'):
        idx = cut.rfind(sep)
        if idx > len(cut) * 0.55:
            return cut[:idx + 1]
    return cut

def translate_string(s, tdict):
    """Return (translated, matched_exact). Handles collapsed-prefix fallback."""
    if s in tdict:
        return tdict[s], True
    cands = [k for k in tdict if len(k) > len(s) and k.startswith(s)]
    if cands:
        best = min(cands, key=len)
        ratio = len(s) / len(best)
        return truncate_prefix(tdict[best], ratio), False
    return s, False

def page_url(lang, en_slug, clean_slug):
    """Absolute URL of a built page, always with a trailing slash, matching the
    folder build.py writes (so canonical/hreflang never point at a redirect)."""
    d = LANG_META[lang]['dir']
    if lang == 'en':
        path = unquote(en_slug.strip('/'))      # 'custom-tutoring/coaching', 'esl-tours-&-field-trips'
    else:
        path = '/'.join(p for p in (d, clean_slug) if p)
    path = quote(path, safe='/')
    return f'{SITE_URL}/{path}/' if path else f'{SITE_URL}/'

def switcher_html(cur_dir, clean_slug, en_slug):
    """Language switcher: a slim static bar at the top of the header (it used to be
    position:fixed and covered the logo on phones)."""
    def href_for(lang):
        d = LANG_META[lang]['dir']
        slug = en_slug if lang == 'en' else clean_slug
        slug = slug.strip('/') if slug != '/' else ''
        if slug == '':
            return '/' if d == '' else f'/{d}/'
        return f'/{d}/{slug}/' if d else f'/{slug}/'
    links = []
    for lang in ['en', 'ko', 'ja', 'zh']:
        d = LANG_META[lang]['dir']
        active = (d == cur_dir)
        colors = 'background:#0a636e;color:#fff;' if active else 'background:transparent;color:#0a636e;'
        current = ' aria-current="true"' if active else ''
        links.append(
            f'<a href="{href_for(lang)}" hreflang="{LANG_META[lang]["hreflang"]}" '
            f'lang="{LANG_META[lang]["lang"]}"{current} style="{colors}padding:4px 8px;'
            f'border-radius:4px;text-decoration:none;">{LANG_META[lang]["label"]}</a>'
        )
    return ('<nav id="hermes-lang-switcher" aria-label="Language" '
            'style="position:relative;z-index:2;display:flex;justify-content:flex-end;gap:4px;'
            'padding:6px 12px;background:#fff;font-family:Arial,sans-serif;font-size:13px;'
            'font-weight:700;line-height:1;">' + ''.join(links) + '</nav>')

def hreflang_tags(en_slug, clean_slug):
    tags = []
    for lang in ['en', 'ko', 'ja', 'zh']:
        tags.append(f'<link rel="alternate" hreflang="{LANG_META[lang]["hreflang"]}" '
                    f'href="{page_url(lang, en_slug, clean_slug)}"/>')
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{page_url("en", en_slug, clean_slug)}"/>')
    return (NL + '    ').join(tags)

def rewrite_href(href, lang):
    """Rewrite an internal href for the language folder. Returns None if
    the href should be left untouched."""
    if not href or lang == 'en':
        return None
    if href.startswith(('http://', 'https://', '//', 'tel:', 'mailto:', '#')):
        return None
    if href.startswith('/'):
        slug = href[1:].rstrip('/')
        clean = EN_SLUG2CLEAN.get('/' + slug)
        if clean is None:
            return None
        d = LANG_META[lang]['dir']
        if clean == '':
            return '/' if d == '' else f'/{d}/'
        return f'/{d}/{clean}/' if d else f'/{clean}/'
    return None

def frag(markup):
    return BeautifulSoup(markup, 'html.parser')

def sanitize(soup):
    """Remove the dead GoDaddy runtime and do its work at build time.
    Runs on the English source BEFORE translation (text selectors are English)."""
    # 1. Lazy images: put the real URLs into src/srcset (GoDaddy JS used to do this)
    for el in soup.find_all(attrs={'data-srcsetlazy': True}):
        el['srcset'] = el['data-srcsetlazy']
        del el['data-srcsetlazy']
    for img in soup.find_all('img', attrs={'data-srclazy': True}):
        img['src'] = img['data-srclazy']
        del img['data-srclazy']
        if 'transparent_placeholder' in img.get('srcset', ''):
            del img['srcset']
        img['loading'] = 'lazy'
        img['decoding'] = 'async'
    for el in soup.find_all(attrs={'data-lazyimg': True}):
        del el['data-lazyimg']

    # 2. Lazy backgrounds: un-hide (.d-none) and give them the parent's height
    for el in soup.find_all(attrs={'data-lazybg': True}):
        el['class'] = [c for c in el.get('class', []) if c != 'd-none']
        style = el.get('style', '').strip().rstrip(';')
        el['style'] = (style + ';' if style else '') + 'height:100%'
        del el['data-lazybg']

    # 3. Widgets only GoDaddy's JS could fill -> empty white gaps today
    had_trustedsite = bool(soup.select('div.widget-html'))
    for cls in DEAD_WIDGETS:
        for w in soup.select('div.' + cls):
            w.decompose()

    # 4. GoDaddy account/bookings UI (/m/* pages no longer exist; drawer shows filler@godaddy.com)
    for el in soup.select('[data-ux="UtilitiesMenu"], [data-ux="Membership"]'):
        el.decompose()
    for a in soup.find_all('a', href=lambda h: bool(h) and (h.startswith('/m/') or 'dreamscatalyst.com/m/' in h)):
        (a.find_parent('li') or a).decompose()

    # 5. "Powered by GoDaddy Airo" + generator meta
    for p in soup.select('[data-aid="FOOTER_POWERED_BY_AIRO_RENDERED"]'):
        cell = p.find_parent(attrs={'data-ux': 'GridCell'}) or p.parent
        cell.decompose()
    for m in soup.select('meta[name="generator"]'):
        m.decompose()

    # 6. Scripts: drop every GoDaddy runtime/tracking script, keep JSON-LD (rewritten)
    for s in soup.find_all('script'):
        if s.get('type') == 'application/ld+json':
            s.string = json.dumps(LOCAL_BUSINESS, ensure_ascii=False)
        else:
            s.decompose()
    soup.head.append(frag(GA4_SNIPPET))
    if KEEP_TRUSTEDSITE and had_trustedsite:
        soup.body.append(frag('<script async src="https://cdn.ywxi.net/js/1.js"></script>'))
    soup.body.append(frag('<script defer src="/assets/site.js"></script>'))

    # 7. Contact form: real field names + endpoint; site.js handles submit
    for form in soup.select('div.widget-contact form'):
        form['data-dc-contact'] = ''
        form['method'] = 'post'
        form['action'] = FORM_ENDPOINT
        if FORM_ENDPOINT:
            form['data-endpoint'] = FORM_ENDPOINT
        fields = (('CONTACT_FORM_NAME', 'name', {'autocomplete': 'name'}),
                  ('CONTACT_FORM_EMAIL', 'email', {'type': 'email', 'autocomplete': 'email', 'required': ''}),
                  ('CONTACT_FORM_MESSAGE', 'message', {}))
        for aid, name, extra in fields:
            el = form.find(['input', 'textarea'], attrs={'data-aid': aid})   # the wrapper <div> carries the same data-aid
            if el:
                el['name'] = name
                for k, v in extra.items():
                    el[k] = v
        for el in form.select('input[name="_app_id"]'):
            el.decompose()
        form.append(frag('<input type="hidden" name="_subject" value="New inquiry from dreamscatalyst.com">'
                         '<input type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true" '
                         'style="position:absolute;left:-9999px;width:1px;height:1px;">'))
    for t in soup.find_all(string=re.compile('protected by reCAPTCHA')):
        p = t.find_parent('p')
        if p:
            p.decompose()

    # 8. Template leftovers and dead-end links
    for p in soup.select('[data-aid="MENU_SECTION_FOOTNOTE_RENDERED"]'):
        p.decompose()                                   # "Add a footnote if this applies to your business"
    for a in soup.select('a[data-aid="HEADER_CTA_BTN"]'):
        a['href'] = HERO_CTA_TARGET                     # "Get Started" pointed at the home page itself
    for a in soup.select('a[data-aid^="CAT_CARD_LINK_RND_"]'):
        n = a['data-aid'].rsplit('_', 1)[-1]
        title = soup.find(attrs={'data-aid': f'FEAT_CAT_TITLE_RND{n}'})
        if title:
            a['aria-label'] = title.get_text(' ', strip=True)
        a.string = ''                                   # accessible name was "#"
    for a in soup.select('[data-aid="HAMBURGER_MENU_LINK"][toggleid]'):
        a['aria-controls'] = a['toggleid']

def build_page(name, html, lang, en_slug):
    soup = BeautifulSoup(html, 'html.parser')
    sanitize(soup)
    tdict = load_translations(lang) if lang != 'en' else {}
    meta = json.load(open(f'{BASE}/translations/{lang}/16-meta.json', encoding='utf-8')) if lang != 'en' else None

    # ---- <html lang> ----
    html_tag = soup.find('html')
    if html_tag:
        html_tag['lang'] = LANG_META[lang]['lang']

    # fix hardcoded locale/lang classes on the body layout div (GoDaddy artifact)
    if lang != 'en':
        locale_map = {'ko': 'ko-KR', 'ja': 'ja-JP', 'zh': 'zh-CN'}
        for el in soup.find_all(class_=re.compile(r'locale-en-US|lang-en')):
            cls = el.get('class') or []
            cls = [re.sub(r'locale-en-US', f'locale-{locale_map[lang]}', c) for c in cls]
            cls = [re.sub(r'lang-en', f'lang-{LANG_META[lang]["lang"]}', c) for c in cls]
            el['class'] = cls

    # ---- <head>: title + meta (only for translated versions) ----
    if lang != 'en':
        pm = meta[name]
        t = soup.find('title')
        if t and pm.get('title'):
            t.string = pm['title']
        for tag in soup.find_all('meta'):
            key = tag.get('property') or tag.get('name')
            if key == 'description' and pm.get('description'):
                tag['content'] = pm['description']
            elif key in ('og:title', 'twitter:title') and pm.get('title'):
                tag['content'] = pm['title']
            elif key in ('og:description',) and pm.get('description'):
                tag['content'] = pm['description']
            elif key == 'twitter:description' and 'Enhance Your Confidence' in (tag.get('content') or ''):
                tag['content'] = tdict.get('Enhance Your Confidence / Achieve Your Dreams', tag['content'])
            elif key == 'og:locale':
                tag['content'] = {'ko': 'ko_KR', 'ja': 'ja_JP', 'zh': 'zh_CN'}[lang]
        for tag in soup.find_all('meta', property='og:description'):
            tag['content'] = tdict.get('Unlocking Dreams, One Conversation at a Time', tag['content'])

    # ---- canonical + og:url point at THIS page (translations are not duplicates of EN) ----
    clean_slug = NAME2CLEAN[name]
    url = page_url(lang, en_slug, clean_slug)
    for link in soup.find_all('link', rel='canonical'):
        link['href'] = url
    for tag in soup.find_all('meta', property='og:url'):
        tag['content'] = url

    # ---- hreflang ----
    head = soup.find('head')
    if head:
        head.append(NavigableString(NL + '    '))
        for node in frag(hreflang_tags(en_slug, clean_slug)).contents:
            head.append(node)
        head.append(NavigableString(NL + '  '))

    # ---- translate text nodes ----
    changed = 0
    for node in soup.find_all(string=True):
        if node.parent.name in ('script', 'style', 'title'):
            continue
        s = node.strip()
        if not s or lang == 'en':
            continue
        if s in tdict:
            node.replace_with(NavigableString(node.replace(s, tdict[s])))
            changed += 1
        else:
            t, ok = translate_string(s, tdict)
            if ok or t != s:
                if len(s) >= 4 or s in tdict:
                    node.replace_with(NavigableString(node.replace(s, t)))
                    changed += 1

    # ---- attributes: alt, aria-label, originalText ----
    for el in soup.find_all(True):
        for attr in ('alt', 'aria-label', 'originalText', 'placeholder', 'title'):
            v = el.get(attr)
            if not v or lang == 'en':
                continue
            if v in tdict:
                el[attr] = tdict[v]

    # ---- internal link rewriting ----
    for a in soup.find_all('a', href=True):
        new = rewrite_href(a['href'], lang)
        if new:
            a['href'] = new

    # ---- language switcher ----
    header = soup.find('section', attrs={'data-aid': 'HEADER_SECTION'})
    if header:
        header.insert(0, frag(switcher_html(LANG_META[lang]['dir'], clean_slug, en_slug)))

    return str(soup), changed

def relativize(out_dir):
    """Convert root-absolute internal paths (/esl/, /ko/esl/, /assets/site.js)
    to relative paths so the site works under any base path. Only index.html
    pages are rewritten; 404 pages keep root-absolute links on purpose."""
    for f in glob.glob(f'{out_dir}/**/index.html', recursive=True) + [f'{out_dir}/index.html']:
        if not os.path.exists(f):
            continue
        html = open(f, encoding='utf-8').read()
        rel_dir = os.path.relpath(os.path.dirname(f), out_dir)
        depth = 0 if rel_dir == '.' else len(rel_dir.split(os.sep))
        prefix = '../' * depth

        def rel(m):
            val = m.group(2)
            if val.startswith(('http://', 'https://', '//', 'tel:', 'mailto:', '#', 'data:')):
                return m.group(0)
            if not val.startswith('/'):
                return m.group(0)
            return f'{m.group(1)}="{prefix}{val.lstrip("/")}"'

        html = re.sub(r'(href|src|action|poster)="(/[^"]*)"', rel, html)
        open(f, 'w', encoding='utf-8').write(html)

def write_sitemap(urls):
    body = NL.join(f'  <url><loc>{u}</loc></url>' for u in urls)
    with open(f'{OUT}/sitemap.xml', 'w', encoding='utf-8') as fh:
        fh.write(NL.join(['<?xml version="1.0" encoding="UTF-8"?>',
                          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                          body, '</urlset>', '']))

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    # static/ holds manifest, assets (site.js, img, fonts), 404 pages, robots.txt, _redirects
    shutil.copytree(f'{BASE}/static', OUT)
    open(f'{OUT}/.nojekyll', 'w').write('')

    summary, urls = {}, []
    for name, en_slug, clean in PAGES:
        html = open(f'{SRC}/{name}.html', encoding='utf-8').read()

        en_dir_name = unquote(en_slug.lstrip('/'))
        en_dir = (f'{OUT}/{en_dir_name}' if en_slug != '/' else OUT)
        os.makedirs(en_dir, exist_ok=True)
        en_html, _ = build_page(name, html, 'en', en_slug)
        open(f'{en_dir}/index.html', 'w', encoding='utf-8').write(en_html)
        urls.append(page_url('en', en_slug, clean))

        for lang in LANGS:
            d = LANG_META[lang]['dir']
            out_dir = f'{OUT}/{d}' + (f'/{clean}' if clean else '')
            os.makedirs(out_dir, exist_ok=True)
            out_html, changed = build_page(name, html, lang, en_slug)
            open(f'{out_dir}/index.html', 'w', encoding='utf-8').write(out_html)
            summary.setdefault(name, {})[lang] = changed
            urls.append(page_url(lang, en_slug, clean))

    for name, langs in summary.items():
        print(f"{name:35s} " + "  ".join(f"{k}:{v} nodes" for k, v in langs.items()))
    print(f"Total pages written: {len(PAGES)} EN + {len(PAGES)}x3 translated = {len(PAGES) * 4}")

    relativize(OUT)
    write_sitemap(urls)
    print("Relative-link pass complete; sitemap.xml written.")

    if os.path.exists(MIRROR):
        shutil.rmtree(MIRROR)
    shutil.copytree(OUT, MIRROR)
    print("site/ mirrored from docs/.")

if __name__ == '__main__':
    main()
