#!/usr/bin/env python3
"""Build and check the static homepage.

Run from anywhere:  python3 tools/build.py          (build + check)
                    python3 tools/build.py --check  (check only, no writes)

Source of truth: tools/projects.json. The script
  * regenerates the homepage "代表作" and "全部项目" blocks,
  * gives every project page the same masthead, footer, asset versions,
    key-metric strip and previous/next navigation,
  * writes sitemap.xml and 404.html,
  * checks local links/anchors, image attributes and banned phrases.

Private banned phrases (e.g. employer names) are read from
~/.config/nusniumu-site/banned.txt so they never enter this public repo.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "tools/projects.json").read_text(encoding="utf-8"))
CHECK_ONLY = "--check" in sys.argv

# Version/run-history wording that should not appear on the site.
PUBLIC_BANNED = ["首版", "第一版", "第二版", "重跑", "复跑", "重测", "沿用旧", "重做", "重写", "原版"]
PRIVATE_BANNED_FILE = Path.home() / ".config/nusniumu-site/banned.txt"

errors: list[str] = []
warnings: list[str] = []
E = html.escape


# ---------- helpers ----------

def short_hash(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8]


def image_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            w = int.from_bytes(data[24:27], "little") + 1
            h = int.from_bytes(data[27:30], "little") + 1
            return w, h
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            b = data[21:25]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return w, h
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    raise ValueError(f"unknown image format: {path}")


def replace_block(text: str, name: str, content: str, *, before: str | None = None,
                  after: str | None = None) -> str:
    """Replace <!-- build:name --> ... <!-- /build:name -->, inserting it if missing."""
    block = f"<!-- build:{name} -->\n{content}\n<!-- /build:{name} -->"
    pattern = re.compile(rf"<!-- build:{name} -->.*?<!-- /build:{name} -->", re.S)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1)
    anchor = before or after
    if anchor is None or anchor not in text:
        raise SystemExit(f"no marker or anchor for block {name!r}")
    if before:
        return text.replace(before, block + "\n" + before, 1)
    return text.replace(after, after + "\n" + block, 1)


def lang_attr(p: dict) -> str:
    return f' lang="{p["lang"]}"' if p.get("lang") else ""


def tag_line(p: dict) -> str:
    bits = [p["kind"]] + ([p["year"]] if p.get("year") else [])
    return " · ".join(bits)


PROJECTS = DATA["projects"]
BY_SLUG = {p["slug"]: p for p in PROJECTS}
CATS = {c["id"]: c["label"] for c in DATA["categories"]}
for p in PROJECTS:
    w, h = image_size(ROOT / p["thumb"])
    p["thumb_w"], p["thumb_h"] = w, h

CSS_V = short_hash(ROOT / "assets/site.css")
CASE_JS_V = short_hash(ROOT / "assets/case.js")
HOME_JS_V = short_hash(ROOT / "assets/projects.js")


def masthead(prefix: str, home_links: bool) -> str:
    base = "" if home_links else prefix
    return f"""<header class="shell masthead">
      <a class="brand" href="{prefix or '#top'}" aria-label="牛牧首页"><span aria-hidden="true">牛</span></a>
      <nav aria-label="主导航">
        <ul class="nav-list">
          <li><a href="{base}#featured">代表作</a></li>
          <li><a href="{base}#projects">全部项目</a></li>
          <li><a href="{base}#about">关于</a></li>
          <li><a href="{base}#contact">联系</a></li>
          <li><a href="https://github.com/NUSNiuMu">GitHub</a></li>
        </ul>
      </nav>
    </header>"""


FOOTER = '<footer class="shell site-footer"><a href="#top">回到顶部</a></footer>'


def metrics_dl(p: dict, cls: str, limit: int) -> str:
    items = "".join(
        f'<div><dt>{E(label)}</dt><dd>{E(value)}</dd></div>' for value, label in p["metrics"][:limit]
    )
    return f'<dl class="{cls}">{items}</dl>'


# ---------- homepage ----------

def featured_html() -> str:
    cards = []
    for slug in DATA["featured"]:
        p = BY_SLUG[slug]
        repo = (f'<a class="repo-link" href="{E(p["repo"])}" aria-label="GitHub 仓库：{E(p["title"])}">GitHub 仓库</a>'
                if p.get("repo") else "")
        cards.append(f"""          <li class="featured-item">
            <img src="{p['thumb']}" width="{p['thumb_w']}" height="{p['thumb_h']}" alt="{E(p['thumb_alt'])}" loading="lazy" decoding="async">
            <div class="featured-copy">
              <p class="tag">{E(tag_line(p))}</p>
              <h3{lang_attr(p)}><a class="card-link" href="projects/{slug}/">{E(p['title'])}</a></h3>
              <p>{E(p['summary'])}</p>
              {metrics_dl(p, 'card-metrics', 2)}
              {repo}
            </div>
          </li>""")
    return f"""      <section id="featured" class="archive" aria-labelledby="featured-title">
        <h2 id="featured-title">代表作</h2>
        <ul class="featured-list" role="list">
{chr(10).join(cards)}
        </ul>
      </section>"""


def projects_html() -> str:
    featured = set(DATA["featured"])
    rest = [p for p in PROJECTS if p["slug"] not in featured]
    buttons = ['<button type="button" data-filter="all" aria-controls="project-list" aria-pressed="true">全部</button>']
    for cid, label in CATS.items():
        buttons.append(f'<button type="button" data-filter="{cid}" aria-controls="project-list" aria-pressed="false">{E(label)}</button>')
    items = []
    for p in PROJECTS:
        extra = ' data-featured="true" hidden' if p["slug"] in featured else ""
        cls = f'archive-image {p["thumb_class"]}' if p.get("thumb_class") else "archive-image"
        value, label = p["metrics"][0]
        repo = (f'\n                <a class="repo-link" href="{E(p["repo"])}" aria-label="GitHub 仓库：{E(p["title"])}">GitHub 仓库</a>'
                if p.get("repo") else "")
        items.append(f"""          <li class="archive-item" data-category="{p['category']}"{extra}>
            <article>
              <img class="{cls}" src="{p['thumb']}" width="{p['thumb_w']}" height="{p['thumb_h']}" alt="{E(p['thumb_alt'])}" loading="lazy" decoding="async">
              <div class="archive-copy">
                <p class="tag">{E(tag_line(p))}</p>
                <h3{lang_attr(p)}><a href="projects/{p['slug']}/">{E(p['title'])}</a></h3>
                <p>{E(p['summary'])}</p>
                <p class="card-metric"><strong>{E(value)}</strong> {E(label)}</p>{repo}
              </div>
            </article></li>""")
    return f"""      <section id="projects" class="archive" aria-labelledby="archive-title">
        <div class="archive-heading">
          <h2 id="archive-title">全部项目</h2>
          <search class="project-filter" aria-label="筛选项目" hidden>
            {chr(10).join('            ' + b if i else b for i, b in enumerate(buttons)).strip()}
            <p class="visually-hidden project-count" role="status"></p>
          </search>
        </div>
        <p class="archive-note">筛选“全部”时只列代表作以外的 {len(rest)} 个项目；按类别筛选时包含代表作。</p>
        <ul class="project-list" id="project-list" role="list">
{chr(10).join(items)}
        </ul>
      </section>"""


def build_home() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'<header class="shell masthead">.*?</header>', lambda _: masthead("", True), text, count=1, flags=re.S)
    text = replace_block(text, "featured", featured_html())
    text = replace_block(text, "projects", projects_html())
    text = re.sub(r'assets/site\.css\?v=\w+', f'assets/site.css?v={CSS_V}', text)
    text = re.sub(r'assets/projects\.js\?v=\w+', f'assets/projects.js?v={HOME_JS_V}', text)
    write(path, text)


# ---------- project pages ----------

def pager_html(i: int) -> str:
    order = PROJECTS
    prev_p = order[i - 1]
    next_p = order[(i + 1) % len(order)]
    return f"""      <nav class="case-pager" aria-label="其他项目">
        <a rel="prev" href="../{prev_p['slug']}/"><span>上一个项目</span><strong{lang_attr(prev_p)}>{E(prev_p['title'])}</strong></a>
        <a class="case-pager-all" href="../../#projects"><span>返回</span><strong>全部项目</strong></a>
        <a rel="next" href="../{next_p['slug']}/"><span>下一个项目</span><strong{lang_attr(next_p)}>{E(next_p['title'])}</strong></a>
      </nav>"""


def build_page(i: int, p: dict) -> None:
    path = ROOT / "projects" / p["slug"] / "index.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'<header class="shell masthead">.*?</header>', lambda _: masthead("../../", False), text, count=1, flags=re.S)
    text = re.sub(r'<footer class="shell site-footer">.*?</footer>', FOOTER, text, count=1, flags=re.S)
    text = re.sub(r'assets/site\.css\?v=\w+', f'assets/site.css?v={CSS_V}', text)
    script = f'<script src="../../assets/case.js?v={CASE_JS_V}" defer></script>'
    if "assets/case.js" in text:
        text = re.sub(r'<script src="\.\./\.\./assets/case\.js\?v=\w+" defer></script>', script, text)
    else:
        text = text.replace("  </head>", f"    {script}\n  </head>", 1)
    strip = metrics_dl(p, "key-metrics", 3).replace('class="key-metrics"', 'class="key-metrics" aria-label="关键指标"')
    text = replace_block(text, "metrics", "      " + strip, before='      <dl class="case-summary"')
    text = replace_block(text, "pager", pager_html(i), before="    </main>")
    # Chapters are scroll targets of the table of contents; let them take focus.
    text = re.sub(r'<section class="chapter" id="([^"]+)">', r'<section class="chapter" id="\1" tabindex="-1">', text)
    write(path, text)


# ---------- generated files ----------

def build_extras() -> None:
    urls = [DATA["site"]] + [f'{DATA["site"]}projects/{p["slug"]}/' for p in PROJECTS]
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
               + "</urlset>\n")
    write(ROOT / "sitemap.xml", sitemap)
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {DATA['site']}sitemap.xml\n")
    links = "\n".join(
        f'          <li><a href="/projects/{p["slug"]}/"{lang_attr(p)}>{E(p["title"])}</a></li>' for p in PROJECTS)
    page = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light dark">
    <meta name="robots" content="noindex">
    <title>页面不存在 · 牛牧</title>
    <link rel="icon" href="/assets/mark.png" type="image/png">
    <link rel="stylesheet" href="/assets/site.css?v={CSS_V}">
  </head>
  <body id="top">
    {masthead("/", False)}
    <main id="main" class="shell case-shell" tabindex="-1">
      <div class="case-title">
        <h1>页面不存在</h1>
        <p class="lead">链接可能已经改名。可以从下面的项目进入，或回到<a href="/">首页</a>。</p>
      </div>
      <ul class="plain-list">
{links}
      </ul>
    </main>
    {FOOTER}
  </body>
</html>
"""
    write(ROOT / "404.html", page)


def write(path: Path, text: str) -> None:
    if CHECK_ONLY:
        return
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        print("wrote", path.relative_to(ROOT))


# ---------- checks ----------

def visible_text(page: str) -> str:
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S)
    attrs = " ".join(re.findall(r'(?:alt|aria-label|content|title)="([^"]*)"', page))
    return html.unescape(re.sub(r"<[^>]+>", " ", page) + " " + attrs)


def check() -> None:
    pages = sorted(p for p in ROOT.rglob("*.html") if "tools" not in p.parts and ".git" not in p.parts)
    ids = {p: set(re.findall(r'\sid="([^"]+)"', p.read_text(encoding="utf-8"))) for p in pages}
    private = []
    if PRIVATE_BANNED_FILE.exists():
        private = [w.strip() for w in PRIVATE_BANNED_FILE.read_text(encoding="utf-8").splitlines()
                   if w.strip() and not w.startswith("#")]
    else:
        warnings.append(f"private banned list not found: {PRIVATE_BANNED_FILE}")
    referenced: set[Path] = set()

    for page in pages:
        rel = page.relative_to(ROOT)
        text = page.read_text(encoding="utf-8")
        for attr, url in re.findall(r'\s(href|src|poster)="([^"]+)"', text):
            if re.match(r"^(https?:|mailto:|tel:|data:)", url):
                continue
            path_part, _, frag = url.partition("#")
            path_part = path_part.split("?")[0]
            if not path_part:
                target = page
            elif path_part.startswith("/"):
                target = ROOT / path_part.lstrip("/")
            else:
                target = (page.parent / path_part).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{rel}: broken {attr} -> {url}")
                continue
            referenced.add(target.resolve())
            if frag and target.suffix == ".html" and frag not in ids.get(target, set()) and frag != "top":
                errors.append(f"{rel}: missing anchor -> {url}")
        for img in re.findall(r"<img\b[^>]*>", text):
            for need in ("alt=", "width=", "height="):
                if need not in img:
                    errors.append(f"{rel}: <img> without {need[:-1]}: {img[:90]}")
        body = visible_text(text)
        for word in PUBLIC_BANNED:
            if word in body:
                errors.append(f"{rel}: banned wording {word!r}")
        for word in private:
            if word.lower() in body.lower():
                errors.append(f"{rel}: private banned phrase #{private.index(word) + 1}")

    for p in PROJECTS:
        if not (ROOT / "projects" / p["slug"] / "index.html").exists():
            errors.append(f"projects.json: no page for {p['slug']}")
    for d in (ROOT / "projects").iterdir():
        if d.is_dir() and d.name not in BY_SLUG:
            errors.append(f"projects/{d.name}: page not listed in projects.json")

    css_refs = set()
    for css in (ROOT / "assets").glob("*.css"):
        for url in re.findall(r"url\(['\"]?([^)'\"]+)", css.read_text(encoding="utf-8")):
            css_refs.add((css.parent / url).resolve())
    unused = sorted(
        str(f.relative_to(ROOT)) for f in (ROOT / "assets").rglob("*")
        if f.is_file() and f.resolve() not in referenced and f.resolve() not in css_refs
        and f.suffix in {".webp", ".png", ".jpg", ".mp4"})
    if unused:
        warnings.append(f"{len(unused)} media files not referenced by any page:\n    " + "\n    ".join(unused))


if __name__ == "__main__":
    if not CHECK_ONLY:
        build_home()
        for i, p in enumerate(PROJECTS):
            build_page(i, p)
        build_extras()
    check()
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e)
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)
