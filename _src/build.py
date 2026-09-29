import os, re, json, html, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
from articles import ARTICLES

HERE = os.path.dirname(os.path.abspath(__file__))
APP_SRC = os.path.join(HERE, 'harry-app.html')
OUT = os.path.dirname(HERE)  # thư mục gốc của kho = trang web
ART = os.environ.get('ART_DIR')  # tùy chọn: bản xem trước trên Claude

ARTICLES = sorted(ARTICLES, key=lambda a: a['date'], reverse=True)
e = html.escape

def fmt_date(d):
    y, m, dd = d.split('-'); return f"{int(dd)}/{int(m)}/{y}"

def words(a):
    n = 0
    for kind, v in a['body']:
        if isinstance(v, str): n += len(v.split())
        else:
            for x in v: n += len((' '.join(x) if isinstance(x, list) else x).split())
    return n

def read_min(a): return max(2, round(words(a) / 200))

BG = '#000'
def fig(pose, size=None):
    head = '<circle cx="60" cy="30" r="21" fill="currentColor"/>'
    torso = '<rect x="43" y="56" width="34" height="68" rx="17" fill="currentColor"/>'
    legs = '<path d="M52 118 L46 186 M68 118 L74 186" stroke="currentColor" stroke-width="16" stroke-linecap="round" fill="none"/>'
    if pose == 'read':
        arms = (f'<path d="M46 66 L32 100 L52 104 M74 66 L88 100 L68 104" stroke="{BG}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                '<path d="M46 66 L32 100 L52 104 M74 66 L88 100 L68 104" stroke="currentColor" stroke-width="13" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                f'<path d="M36 90 L60 96 L84 90 L84 116 L60 122 L36 116 Z" fill="#ffbd59"/><path d="M60 96 L60 122" stroke="{BG}" stroke-width="2"/>')
    elif pose == 'think':
        arms = ('<path d="M46 66 L36 118" stroke="currentColor" stroke-width="14" stroke-linecap="round" fill="none"/>'
                f'<path d="M76 66 L92 90 L72 56" stroke="{BG}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                '<path d="M76 66 L92 90 L72 56" stroke="currentColor" stroke-width="13" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                '<text x="92" y="22" font-family="Literata, Georgia, serif" font-weight="700" font-size="30" fill="#ffbd59">?</text>')
    elif pose == 'rise':
        arms = ('<path d="M46 66 L28 34 M74 66 L92 34" stroke="currentColor" stroke-width="14" stroke-linecap="round" fill="none"/>'
                '<circle cx="100" cy="16" r="9" fill="#ffbd59"/>')
    else:
        arms = '<path d="M46 66 L36 118 M74 66 L84 118" stroke="currentColor" stroke-width="14" stroke-linecap="round" fill="none"/>'
    return f'<svg viewBox="0 0 120 200" width="100%" aria-hidden="true">{legs}{torso}{arms}{head}</svg>'

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Literata:opsz,wght@7..72,600;7..72,700&display=swap">')

BLOG_CSS = """
/* Layout: cột đọc 680px trên nền đen của kênh; tiêu đề serif, thân chữ không chân, điểm nhấn vàng */
:root{--bg:#000;--surface:#121110;--surface-2:#1c1a17;--line:#2e2b27;--fg:#f2f0ec;--muted:#a09a90;--gold:#ffbd59;--gold-soft:rgba(255,189,89,.14);--gold-ink:#1b1204;
--display:"Literata",Georgia,"Times New Roman",serif;--body:"Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color-scheme:dark}
*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--fg)}
:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{font-family:var(--body);font-size:17px;line-height:1.75;padding-inline:16px;padding-block:0 56px;-webkit-font-smoothing:antialiased}
img{max-width:100%}
a{color:var(--gold)}
:focus-visible{outline:2px solid var(--gold);outline-offset:3px;border-radius:6px}
.wrap{max-width:680px;margin:0 auto}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding-block:18px 14px;border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--fg)}
.brand-mark{width:34px;height:34px;border-radius:50%;background:var(--gold);color:var(--gold-ink);display:grid;place-items:center;font-family:var(--display);font-weight:700;font-size:18px}
.brand-name{font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:13px}
nav{display:flex;gap:16px;font-size:14px}
nav a{color:var(--muted);text-decoration:none}
nav a:hover,nav a[aria-current="page"]{color:var(--gold)}
.crumb{font-size:13px;color:var(--muted);margin:28px 0 10px}
.crumb a{color:var(--muted)}
h1{font-family:var(--display);font-weight:700;font-size:clamp(30px,7vw,42px);line-height:1.2;margin:0;text-wrap:balance}
.meta{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:14px;color:var(--muted);margin:14px 0 0}
.cat{color:var(--gold);font-weight:600;font-size:12px;letter-spacing:.12em;text-transform:uppercase}
.lede{font-size:19px;color:var(--fg);margin:22px 0 0}
.article{margin-top:8px}
.article h2{font-family:var(--display);font-size:25px;line-height:1.3;margin:40px 0 10px;text-wrap:balance}
.article p{margin:0 0 18px}
.article ul,.article ol{margin:0 0 20px;padding-left:22px;display:flex;flex-direction:column;gap:8px}
.article blockquote{margin:28px 0;padding:6px 0 6px 18px;border-left:3px solid var(--gold);font-family:var(--display);font-size:22px;line-height:1.45}
.tip{background:var(--surface-2);border-radius:14px;padding:16px 18px;margin:0 0 20px;font-size:16px}
.tablewrap{overflow-x:auto;margin:0 0 22px}
table{border-collapse:collapse;width:100%;font-size:16px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--gold);font-weight:600;font-size:13px;letter-spacing:.06em;text-transform:uppercase}
td:first-child{white-space:nowrap;font-variant-numeric:tabular-nums}
.cta{margin:40px 0 0;background:var(--surface);border:1px solid var(--gold);border-radius:20px;padding:22px 20px;display:grid;grid-template-columns:72px 1fr;gap:18px;align-items:center}
.cta .fig{width:72px;color:var(--fg)}
.cta h3{font-family:var(--display);font-size:21px;margin:0 0 6px;line-height:1.3}
.cta p{margin:0 0 14px;color:var(--muted);font-size:15px;line-height:1.6}
.btns{display:flex;gap:10px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 18px;border-radius:999px;border:1px solid var(--line);background:var(--surface-2);font-weight:600;text-decoration:none;color:var(--fg);font-size:15px}
.btn:hover{border-color:var(--gold)}
.btn-gold{background:var(--gold);border-color:var(--gold);color:var(--gold-ink)}
.related{margin-top:44px}
.related h2,.list-h{font-family:var(--display);font-size:22px;margin:0 0 14px}
.posts{display:grid;gap:14px;margin:0;padding:0;list-style:none}
.post{display:grid;grid-template-columns:56px 1fr;gap:16px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px 18px;text-decoration:none;color:var(--fg);transition:border-color .15s}
.post:hover{border-color:var(--gold)}
.post .fig{width:56px;color:var(--fg)}
.post h3{font-family:var(--display);font-size:19px;line-height:1.35;margin:4px 0 4px;text-wrap:balance}
.post p{margin:0;font-size:14px;color:var(--muted);line-height:1.55}
.post small{font-size:13px;color:var(--muted)}
footer{margin-top:48px;border-top:1px solid var(--line);padding-top:18px;font-size:13px;color:var(--muted);display:flex;flex-direction:column;gap:6px;line-height:1.6}
@media (max-width:420px){.cta{grid-template-columns:1fr}.cta .fig{width:60px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

def header(home, blog, current):
    return f'''<header class="top">
  <a class="brand" href="{home}"><span class="brand-mark" aria-hidden="true">H</span><span class="brand-name">Sách nhà Harry</span></a>
  <nav aria-label="Điều hướng chính">
    <a href="{home}">Trắc nghiệm</a>
    <a href="{blog}"{' aria-current="page"' if current=='blog' else ''}>Bài viết</a>
    <a href="https://www.tiktok.com/@sachnhaharry" target="_blank" rel="noopener">TikTok</a>
  </nav>
</header>'''

FOOTER = '''<footer>
  <span>© 2026 Sách nhà Harry · Bài học phát triển bản thân mỗi ngày.</span>
  <span>Nội dung mang tính chia sẻ và tham khảo, không thay thế tư vấn của chuyên gia tâm lý.</span>
</footer>'''

def page(title, desc, body, ld=None):
    ldtag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ''
    return f'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Sách nhà Harry">
<meta name="theme-color" content="#000000">
{FONTS}
<style>{BLOG_CSS}</style>
{ldtag}
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>
'''

def render_blocks(blocks):
    out = []
    first = True
    for kind, v in blocks:
        if kind == 'p':
            cls = ' class="lede"' if first else ''
            out.append(f'<p{cls}>{e(v)}</p>'); first = False
        elif kind == 'h2': out.append(f'<h2>{e(v)}</h2>')
        elif kind == 'ul': out.append('<ul>' + ''.join(f'<li>{e(x)}</li>' for x in v) + '</ul>')
        elif kind == 'ol': out.append('<ol>' + ''.join(f'<li>{e(x)}</li>' for x in v) + '</ol>')
        elif kind == 'quote': out.append(f'<blockquote>{e(v)}</blockquote>')
        elif kind == 'tip': out.append(f'<p class="tip">{e(v)}</p>')
        elif kind == 'table':
            h, *rows = v
            out.append('<div class="tablewrap"><table><thead><tr>' + ''.join(f'<th>{e(c)}</th>' for c in h) + '</tr></thead><tbody>' +
                       ''.join('<tr>' + ''.join(f'<td>{e(c)}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table></div>')
    return '\n'.join(out)

def post_card(a, href):
    return (f'<li><a class="post" href="{href}"><div class="fig">{fig(a["fig"])}</div><div>'
            f'<small><span class="cat">{e(a["cat"])}</span> · {read_min(a)} phút đọc</small>'
            f'<h3>{e(a["title"])}</h3><p>{e(a["desc"])}</p></div></a></li>')

def article_page(a):
    others = [x for x in ARTICLES if x['slug'] != a['slug']][:3]
    qid, qlabel = a['quiz']
    body = f'''{header('../index.html', 'index.html', 'blog')}
<main>
  <p class="crumb"><a href="index.html">Bài viết</a> / {e(a['cat'])}</p>
  <h1>{e(a['title'])}</h1>
  <p class="meta"><span class="cat">{e(a['cat'])}</span><span>{fmt_date(a['date'])}</span><span>· {read_min(a)} phút đọc</span></p>
  <article class="article">
{render_blocks(a['body'])}
  </article>
  <aside class="cta" aria-label="Bài trắc nghiệm liên quan">
    <div class="fig">{fig(a['fig'])}</div>
    <div>
      <h3>Thử tự kiểm tra bản thân</h3>
      <p>Bài trắc nghiệm 10 câu, khoảng 2 phút. Làm xong nhận thẻ kết quả để chia sẻ.</p>
      <div class="btns">
        <a class="btn btn-gold" href="../index.html#{qid}">{e(qlabel.replace('Làm bài test: ', 'Làm bài test'))}</a>
        <a class="btn" href="https://www.tiktok.com/@sachnhaharry" target="_blank" rel="noopener">Xem video trên TikTok</a>
      </div>
    </div>
  </aside>
  <section class="related">
    <h2>Đọc tiếp</h2>
    <ul class="posts">{''.join(post_card(x, x['slug'] + '.html') for x in others)}</ul>
  </section>
</main>
{FOOTER}'''
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a['title'], "description": a['desc'],
          "datePublished": a['date'], "inLanguage": "vi", "author": {"@type": "Organization", "name": "Sách nhà Harry"},
          "publisher": {"@type": "Organization", "name": "Sách nhà Harry"}}
    return page(a['title'] + ' | Sách nhà Harry', a['desc'], body, ld)

def blog_index():
    body = f'''{header('../index.html', 'index.html', 'blog')}
<main>
  <p class="crumb">Blog</p>
  <h1>Bài viết</h1>
  <p class="lede">Những bài đọc 5 phút về tâm lý, kỷ luật và các mối quan hệ, viết lại từ các video của kênh để bạn đọc chậm và ngẫm kỹ hơn.</p>
  <ul class="posts" style="margin-top:28px">{''.join(post_card(a, a['slug'] + '.html') for a in ARTICLES)}</ul>
</main>
{FOOTER}'''
    return page('Bài viết | Sách nhà Harry', 'Bài viết về phát triển bản thân, tâm lý, kỷ luật và các mối quan hệ từ kênh Sách nhà Harry.', body)

# ---------- Trang chủ (ứng dụng) có thêm mục blog ----------
app = open(APP_SRC, encoding='utf-8').read()
HOME_CARDS = ''.join(post_card(a, 'bai-viet/' + a['slug'] + '.html') for a in ARTICLES[:3])
home_css = """
.nav{display:flex;gap:14px;align-items:center;font-size:13px}
.nav a{color:var(--muted);text-decoration:none}.nav a:hover{color:var(--gold)}
.posts{display:grid;gap:14px;margin:0;padding:0;list-style:none}
.post{display:grid;grid-template-columns:56px 1fr;gap:16px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px 18px;text-decoration:none;color:var(--fg);transition:border-color .15s}
.post:hover{border-color:var(--gold)}
.post .fig{width:56px;color:var(--fg)}
.post h3{font-family:var(--display);font-size:18px;line-height:1.35;margin:4px 0 4px;text-wrap:balance}
.post p{margin:0;font-size:14px;color:var(--muted);line-height:1.55}
.post small{font-size:13px;color:var(--muted)}
.cat{color:var(--gold);font-weight:600;font-size:12px;letter-spacing:.12em;text-transform:uppercase}
.more{display:inline-block;margin-top:14px;font-weight:600;font-size:14px;text-decoration:none}
</style>"""
app = app.replace('</style>', home_css, 1)
app = app.replace('<a class="handle" href="https://www.tiktok.com/@sachnhaharry" target="_blank" rel="noopener">@sachnhaharry</a>',
                  '<nav class="nav" aria-label="Điều hướng chính"><a href="bai-viet/index.html">Bài viết</a><a href="https://www.tiktok.com/@sachnhaharry" target="_blank" rel="noopener">@sachnhaharry</a></nav>')
blog_section = f'''<section aria-labelledby="blog-h">
      <p class="eyebrow">Bài viết mới</p>
      <h2 class="section-title" id="blog-h">Đọc chậm, ngẫm kỹ</h2>
      <ul class="posts">{HOME_CARDS}</ul>
      <a class="more" href="bai-viet/index.html">Xem tất cả bài viết →</a>
    </section>

    <footer>'''
app = app.replace('<footer>', blog_section, 1)
app = app.replace('<div class="links">', '<div class="links"><a href="bai-viet/index.html">Bài viết</a>', 1)
assert 'bai-viet/index.html' in app and 'blog-h' in app

HEAD = '''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Sách nhà Harry – bài học phát triển bản thân mỗi ngày 5 phút, bài viết về tâm lý, kỷ luật và các bài trắc nghiệm miễn phí.">
<meta property="og:title" content="Sách nhà Harry – Hiểu mình hơn mỗi ngày 5 phút">
<meta property="og:description" content="Bài học mỗi ngày, bài viết và trắc nghiệm tâm lý miễn phí.">
<meta property="og:type" content="website">
<meta name="theme-color" content="#000000">
<style>*,*::before,*::after{box-sizing:border-box}html,body{margin:0}img{max-width:100%}[hidden]{display:none!important}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>
'''
i = app.index('</style>') + len('</style>')
# chèn sau khối style đầu tiên chứa home_css: tìm </style> cuối cùng trước <div class="wrap">
cut = app.index('<div class="wrap">')
standalone = HEAD + app[:cut] + '</head>\n<body>\n' + app[cut:] + '\n</body>\n</html>\n'

DIRS = [OUT] + ([ART] if ART else [])
for d in DIRS:
    if os.path.isdir(os.path.join(d, 'bai-viet')): shutil.rmtree(os.path.join(d, 'bai-viet'))
    os.makedirs(os.path.join(d, 'bai-viet'))

open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(standalone)
if ART: open(os.path.join(ART, 'index.html'), 'w', encoding='utf-8').write(app)
for d in DIRS:
    open(os.path.join(d, 'bai-viet', 'index.html'), 'w', encoding='utf-8').write(blog_index())
    for a in ARTICLES:
        open(os.path.join(d, 'bai-viet', a['slug'] + '.html'), 'w', encoding='utf-8').write(article_page(a))


# sitemap.xml cho Google (tự cập nhật mỗi lần build)
SITE = 'https://sachnhaharry.netlify.app'
latest = max(a['date'] for a in ARTICLES)
urls = [(SITE + '/', latest), (SITE + '/bai-viet/index.html', latest)] + [(SITE + '/bai-viet/' + a['slug'] + '.html', a['date']) for a in ARTICLES]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n' for u, d in urls) + '</urlset>\n'
open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(sm)
open(os.path.join(OUT, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\n\nSitemap: ' + SITE + '/sitemap.xml\n')
for a in ARTICLES: print(a['slug'], words(a), 'từ,', read_min(a), 'phút')
print('OK')
