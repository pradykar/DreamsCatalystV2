#!/usr/bin/env python3
"""Build multilingual static clone of dreamscatalyst.com.

Reads the 14 captured GoDaddy source pages (source/*.html), applies the
translation dicts (translations/<lang>/*.json), injects a language switcher,
hreflang tags, and rewrites internal links, then writes:

  site/                         English baseline (original slugs, +switcher/hreflang only)
  site/ko/...  site/ja/...  site/zh/...   (clean slugs)

Text-node strategy:
  - exact match against translation dict
  - if the node text is a strict prefix of exactly one dict key (a "Show More"
    collapsed preview), use that key's translation truncated to the same ratio
Everything else (classes, inline styles, structure, images, JS) is preserved.
"""
import json, os, re, shutil, glob
from bs4 import BeautifulSoup, NavigableString

BASE = '/home/prady/dreamscatalyst'
SRC = f'{BASE}/source'
OUT = f'{BASE}/docs'   # GitHub Pages publishes /docs from main (branch deploy, no workflow)

# slug mapping: source filename -> (english original slug dir, clean slug)
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
    ('esl-special-services',  '/esl-special-services',      'esl-special-services'),
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

# booking/account/contact links -> live English GoDaddy site (decision: option a)
M_LINKS = {
    '/m/account':        'https://www.dreamscatalyst.com/m/account',
    '/m/bookings':       'https://www.dreamscatalyst.com/m/bookings',
    '/m/create-account': 'https://www.dreamscatalyst.com/m/create-account',
    '/m/create':         'https://www.dreamscatalyst.com/m/create',
    '/m/login':          'https://www.dreamscatalyst.com/m/login',
}

def load_translations(lang):
    d = {}
    for f in glob.glob(f'{BASE}/translations/{lang}/*.json'):
        d.update(json.load(open(f)))
    return d

def truncate_prefix(translation, ratio):
    """Truncate a translation to approx the same character ratio as the
    English collapsed preview, on a word boundary when possible."""
    n = max(1, int(len(translation) * ratio))
    cut = translation[:n]
    # extend to a natural boundary (space or CJK punctuation) if close
    for sep in (' ', '。', '！', '？', '.', '!', '?', '、', '」', '」', '）', ')', '】'):
        idx = cut.rfind(sep)
        if idx > len(cut) * 0.55:
            return cut[:idx + 1]
    return cut

def translate_string(s, tdict):
    """Return (translated, matched_exact). Handles collapsed-prefix fallback."""
    if s in tdict:
        return tdict[s], True
    # strict-prefix fallback: find shortest dict key that starts with s
    cands = [k for k in tdict if len(k) > len(s) and k.startswith(s)]
    if cands:
        best = min(cands, key=len)
        ratio = len(s) / len(best)
        return truncate_prefix(tdict[best], ratio), False
    return s, False

def swither_html(cur_dir, clean_slug, en_slug):
    """Language switcher markup. cur_dir: '' (en) or 'ko'/'ja'/'zh'."""
    def href_for(lang):
        d = LANG_META[lang]['dir']
        # EN pages live at their original slugs; translated pages at clean slugs
        slug = en_slug if lang == 'en' else clean_slug
        slug = slug.strip('/') if slug != '/' else ''
        if slug == '':
            return '/' if d == '' else f'/{d}/'
        return f'/{d}/{slug}/' if d else f'/{slug}/'
    links = []
    for lang in ['en', 'ko', 'ja', 'zh']:
        d = LANG_META[lang]['dir']
        active = (d == cur_dir)
        style = ('background:#0a636e;color:#fff;' if active
                 else 'background:transparent;color:#0a636e;')
        links.append(
            f'<a href="{href_for(lang)}" hreflang="{LANG_META[lang]["hreflang"]}" '
            f'lang="{LANG_META[lang]["lang"]}" style="{style}">{LANG_META[lang]["label"]}</a>'
        )
    return ('<div data-ux="Block" id="hermes-lang-switcher" aria-label="Language switcher" '
            'style="position:fixed;top:10px;right:10px;z-index:999999;display:flex;'
            'gap:4px;padding:4px;background:rgba(255,255,255,0.92);border:1px solid #0a636e;'
            'border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.15);font-family:Arial,sans-serif;'
            'font-size:13px;font-weight:700;">' + ''.join(links) + '</div>')

def hreflang_tags(clean_slug, en_slug):
    tags = []
    for lang in ['en', 'ko', 'ja', 'zh']:
        d = LANG_META[lang]['dir']
        slug = en_slug if lang == 'en' else clean_slug
        slug = slug.strip('/') if slug != '/' else ''
        if d:
            href = (f'https://dreamscatalyst.com/{d}/{slug}/' if slug else f'https://dreamscatalyst.com/{d}/')
        else:
            href = (f'https://dreamscatalyst.com/{slug}/' if slug else 'https://dreamscatalyst.com/')
        tags.append(f'<link rel="alternate" hreflang="{LANG_META[lang]["hreflang"]}" href="{href}"/>')
    tags.append('<link rel="alternate" hreflang="x-default" href="https://dreamscatalyst.com/'
                + (f'{en_slug.strip("/")}/' if en_slug != '/' else '') + '"/>')
    return '\n    '.join(tags)

def rewrite_href(href, lang):
    """Rewrite an internal href for the language folder. Returns None if
    the href should be left untouched."""
    if not href:
        return None
    # /m/* -> live GoDaddy site (keeps booking/account functional on the static clone)
    if href.startswith('/m/'):
        return M_LINKS.get(href, None)
    # English baseline: only /m/* rewritten; other internal links keep original slugs
    if lang == 'en':
        return None
    if href.startswith(('http://', 'https://', '//', 'tel:', 'mailto:', '#')):
        return None
    if href.startswith('/m/'):
        # booking/account -> live GoDaddy site (translated versions only)
        return M_LINKS.get(href, None)
    if href.startswith('/'):
        slug = href[1:].rstrip('/')
        # decode %26 / %2F in the english slug
        clean = EN_SLUG2CLEAN.get('/' + slug)
        if clean is None:
            return None
        d = LANG_META[lang]['dir']
        if clean == '':
            return '/' if d == '' else f'/{d}/'
        return f'/{d}/{clean}/' if d else f'/{clean}/'
    return None

def build_page(name, html, lang, en_slug):
    soup = BeautifulSoup(html, 'html.parser')
    tdict = load_translations(lang) if lang != 'en' else {}
    meta = json.load(open(f'{BASE}/translations/{lang}/16-meta.json')) if lang != 'en' else None

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
        # og:description that is the tagline
        for tag in soup.find_all('meta', property='og:description'):
            tag['content'] = tdict.get('Unlocking Dreams, One Conversation at a Time', tag['content'])

    # ---- hreflang + canonical ----
    clean_slug = NAME2CLEAN[name]
    head = soup.find('head')
    if head:
        alt = soup.new_tag('meta')
        head.append(NavigableString('\n    '))
        # insert hreflang block before </head>
        hl = BeautifulSoup(hreflang_tags(clean_slug, en_slug), 'html.parser')
        for node in hl.contents:
            head.append(node)
        head.append(NavigableString('\n  '))

    # ---- translate text nodes ----
    changed = 0
    for node in soup.find_all(string=True):
        if node.parent.name in ('script', 'style', 'title'):
            continue
        s = node.strip()
        if not s:
            continue
        # preserve nbsp
        norm = s.replace('\u00a0', ' ')
        if lang == 'en':
            continue
        if s in tdict:
            node.replace_with(NavigableString(node.replace(s, tdict[s])))
            changed += 1
        else:
            t, ok = translate_string(s, tdict)
            if ok or t != s:
                # only replace if we actually translated (avoid prefix noise on short strings)
                if len(s) >= 4 or s in tdict:
                    node.replace_with(NavigableString(node.replace(s, t)))
                    changed += 1

    # ---- attributes: alt, aria-label, originalText ----
    for el in soup.find_all(True):
        for attr in ('alt', 'aria-label', 'originalText'):
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
        sw = BeautifulSoup(swither_html(LANG_META[lang]['dir'], clean_slug, en_slug), 'html.parser')
        header.insert(0, sw)

    # ---- booking/account buttons keep working (translated) ----
    return str(soup), changed

def relativize(out_dir):
    """Convert root-absolute internal paths (/esl/, /ko/esl/, /manifest.webmanifest)
    to relative paths so the site works under any base path (e.g. GitHub Pages
    /DreamsCatalyst/). Leaves absolute URLs (https://..., //cdn, tel:, mailto:)
    untouched. hreflang/canonical absolute URLs stay absolute by design."""
    import urllib.parse as up
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


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # GitHub Pages: skip Jekyll processing
    open(f'{OUT}/.nojekyll', 'w').write('')

    # self-hosted static assets (manifest etc.)
    if os.path.exists(f'{BASE}/static/manifest.webmanifest'):
        shutil.copy(f'{BASE}/static/manifest.webmanifest', f'{OUT}/manifest.webmanifest')

    summary = {}
    for name, en_slug, clean in PAGES:
        html = open(f'{SRC}/{name}.html', encoding='utf-8').read()

        # English baseline: keep original slug dir (URL-decoded name so encoded
        # requests like /esl-tours-%26-field-trips/ resolve), inject switcher + hreflang only
        from urllib.parse import unquote
        en_dir_name = unquote(en_slug.lstrip('/'))
        en_dir = (f'{OUT}/{en_dir_name}' if en_slug != '/' else OUT)
        os.makedirs(en_dir, exist_ok=True)
        en_html, _ = build_page(name, html, 'en', en_slug)
        open(f'{en_dir}/index.html', 'w', encoding='utf-8').write(en_html)

        for lang in LANGS:
            d = LANG_META[lang]['dir']
            out_dir = f'{OUT}/{d}' + (f'/{clean}' if clean else '')
            os.makedirs(out_dir, exist_ok=True)
            out_html, changed = build_page(name, html, lang, en_slug)
            open(f'{out_dir}/index.html', 'w', encoding='utf-8').write(out_html)
            summary.setdefault(name, {})[lang] = changed

    for name, langs in summary.items():
        print(f"{name:35s} " + "  ".join(f"{k}:{v} nodes" for k, v in langs.items()))
    print("\nTotal pages written: 14 EN + 14x3 translated =", 14 + 14 * 3)

    relativize(OUT)
    print("Relative-link pass complete (portable to any base path).")

if __name__ == '__main__':
    main()
