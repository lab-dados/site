"""Pre-render hook: turn YAML data files into HTML partials Quarto pages include.

Run by Quarto via `pre-render` in `_quarto.yml`. Two modes:

1. (default) Read YAMLs in `_data/` and write HTML to `_partials/`.
2. (opt-in) If env var `LABDADOS_SHEETS_CSV_<NAME>` is set, fetch CSV from that
   URL first and overwrite `_data/<name>.yml` before rendering. This lets a
   non-programmer maintain content via a published Google Sheet without giving
   them write access to the repo source.

The HTML produced here is intentionally simple — a flat list of `<div>`s using
the `.ld-card` / `.ld-person` / `.ld-pill` classes from `assets/theme.scss`.

Run manually:
    uv run python tools/build_data.py
"""

from __future__ import annotations

import csv
import html
import io
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data"
OUT = ROOT / "_partials"
OUT.mkdir(exist_ok=True)

# Names that may be overridden by a Google Sheet CSV.
SHEET_BACKED = ("equipe", "ferramentas", "pesquisas", "cursos", "parceiros")

# ---------------------------------------------------------------------------
# Optional: pull from published Google Sheets CSV before reading YAML.
# Format expected: each env var points to a "Publish to web" CSV URL.
# ---------------------------------------------------------------------------


def _maybe_sync_sheet(name: str) -> None:
    env = f"LABDADOS_SHEETS_CSV_{name.upper()}"
    url = os.environ.get(env)
    if not url:
        return
    print(f"[build_data] syncing {name} from {env}", file=sys.stderr)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            text = resp.read().decode("utf-8")
    except Exception as exc:  # network errors should not break the build
        print(f"[build_data] WARNING: failed to fetch {env}: {exc}", file=sys.stderr)
        return
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        print(f"[build_data] WARNING: {env} returned no rows", file=sys.stderr)
        return
    # Strip empty values; split list-like columns on `;`.
    cleaned = []
    for r in rows:
        item = {}
        for k, v in r.items():
            if v is None:
                continue
            v = v.strip()
            if v == "":
                continue
            if k in ("parceiros", "tags"):
                item[k] = [s.strip() for s in v.split(";") if s.strip()]
            else:
                item[k] = v
        if item:
            cleaned.append(item)
    target = DATA / f"{name}.yml"
    target.write_text(
        yaml.safe_dump(cleaned, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------


def _e(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def _load(name: str) -> list[dict]:
    p = DATA / f"{name}.yml"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return [d for d in data if isinstance(d, dict)]


def _icon_link(icon: str, href: str, label: str) -> str:
    return (
        f'<a href="{_e(href)}" target="_blank" rel="noopener" aria-label="{_e(label)}">'
        f'<i class="bi bi-{icon}"></i></a>'
    )


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def render_equipe() -> str:
    items = _load("equipe")
    cards = []
    for p in items:
        links = []
        if p.get("github"):
            links.append(_icon_link("github", f"https://github.com/{p['github']}", "GitHub"))
        if p.get("linkedin"):
            links.append(_icon_link("linkedin", f"https://linkedin.com/in/{p['linkedin']}", "LinkedIn"))
        if p.get("email"):
            links.append(_icon_link("envelope", f"mailto:{p['email']}", "E-mail"))
        if p.get("site"):
            links.append(_icon_link("globe", p["site"], "Site"))
        if p.get("lattes"):
            links.append(_icon_link("file-earmark-text", p["lattes"], "Lattes"))
        if p.get("orcid"):
            links.append(_icon_link("hash", p["orcid"], "ORCID"))

        photo = p.get("foto") or "https://github.com/identicons/labdados.png"
        cards.append(
            f"""
<div class="ld-person">
  <img src="{_e(photo)}" alt="{_e(p.get('nome',''))}" loading="lazy">
  <h4>{_e(p.get('nome',''))}</h4>
  <p class="role">{_e(p.get('papel',''))}</p>
  <p>{_e(p.get('bio',''))}</p>
  <p class="links">{' '.join(links)}</p>
</div>""".strip()
        )
    if not cards:
        return '<p class="text-muted">Equipe ainda não cadastrada.</p>'
    return '<div class="ld-people">\n' + "\n".join(cards) + "\n</div>\n"


def _status_pill(status: str) -> str:
    cls = "ld-pill"
    if status in {"estavel", "concluida"}:
        cls += " ld-pill--green"
    elif status in {"em-andamento", "beta"}:
        cls += " ld-pill--navy"
    elif status in {"alpha", "experimental", "planejada"}:
        cls += " ld-pill--coral"
    return f'<span class="{cls}">{_e(status)}</span>'


def render_ferramentas() -> str:
    items = _load("ferramentas")
    # Group by categoria, keeping insertion order.
    groups: dict[str, list[dict]] = {}
    label = {
        "pacote": "Pacotes",
        "sdk": "SDKs",
        "skill": "Skills do Claude",
        "dados": "Dados abertos",
        "servico": "Serviços",
    }
    for it in items:
        groups.setdefault(it.get("categoria", "outros"), []).append(it)

    blocks = []
    for cat in ("pacote", "sdk", "skill", "servico", "dados"):
        bucket = groups.get(cat)
        if not bucket:
            continue
        cards = []
        for it in bucket:
            tags = []
            if it.get("linguagem"):
                tags.append(f'<code>{_e(it["linguagem"])}</code>')
            if it.get("pip"):
                tags.append(f'<code>pip install {_e(it["pip"])}</code>')
            if it.get("status"):
                tags.append(_status_pill(it["status"]))
            href = it.get("repo") or it.get("link") or it.get("docs") or "#"
            extras = []
            if it.get("docs"):
                extras.append(f'<a href="{_e(it["docs"])}" target="_blank" rel="noopener">docs</a>')
            if it.get("repo") and href != it.get("repo"):
                extras.append(f'<a href="{_e(it["repo"])}" target="_blank" rel="noopener">repo</a>')
            extras_html = (
                '<div class="ld-card__meta">' + " · ".join(extras) + "</div>" if extras else ""
            )
            cards.append(
                f"""
<a class="ld-card" href="{_e(href)}" target="_blank" rel="noopener">
  <span class="ld-card__tag">{_e(it.get('categoria',''))}</span>
  <h3>{_e(it.get('nome',''))}</h3>
  <p>{_e(it.get('descricao',''))}</p>
  <div class="ld-card__meta">{' '.join(tags)}</div>
  {extras_html}
</a>""".strip()
            )
        blocks.append(
            f'<h3 id="cat-{cat}" style="margin-top:2rem">{_e(label.get(cat, cat.title()))}</h3>\n'
            '<div class="ld-grid">\n' + "\n".join(cards) + "\n</div>"
        )
    if not blocks:
        return '<p class="text-muted">Sem ferramentas cadastradas.</p>'
    return "\n\n".join(blocks) + "\n"


def render_pesquisas() -> str:
    items = _load("pesquisas")
    cards = []
    for it in items:
        meta_bits = []
        if it.get("ano_inicio"):
            meta_bits.append(f'<code>desde {_e(it["ano_inicio"])}</code>')
        if it.get("status"):
            meta_bits.append(_status_pill(it["status"]))
        if it.get("parceiros"):
            for p in it["parceiros"]:
                meta_bits.append(f'<span class="ld-pill">{_e(p)}</span>')
        href = it.get("repo") or it.get("link") or "#"
        is_link = href != "#"
        tag_html = '<a class="ld-card"' if is_link else '<div class="ld-card"'
        end_tag = "</a>" if is_link else "</div>"
        href_attr = f' href="{_e(href)}" target="_blank" rel="noopener"' if is_link else ""
        cards.append(
            f"""
{tag_html}{href_attr}>
  <span class="ld-card__tag">pesquisa</span>
  <h3>{_e(it.get('titulo',''))}</h3>
  <p>{_e(it.get('resumo',''))}</p>
  <div class="ld-card__meta">{' '.join(meta_bits)}</div>
{end_tag}""".strip()
        )
    if not cards:
        return '<p class="text-muted">Sem pesquisas cadastradas.</p>'
    return '<div class="ld-grid">\n' + "\n".join(cards) + "\n</div>\n"


def render_cursos() -> str:
    items = _load("cursos")
    label = {"curso": "Curso", "oficina": "Oficina", "livro": "Livro", "palestra": "Palestra"}
    cards = []
    for it in items:
        meta = [_status_pill(it.get("tipo", "")), f'<code>{_e(it.get("ano",""))}</code>']
        href = it.get("link") or "#"
        is_link = href != "#"
        tag_html = '<a class="ld-card"' if is_link else '<div class="ld-card"'
        end_tag = "</a>" if is_link else "</div>"
        href_attr = f' href="{_e(href)}" target="_blank" rel="noopener"' if is_link else ""
        cards.append(
            f"""
{tag_html}{href_attr}>
  <span class="ld-card__tag">{_e(label.get(it.get('tipo',''), it.get('tipo','')))}</span>
  <h3>{_e(it.get('titulo',''))}</h3>
  <p>{_e(it.get('descricao',''))}</p>
  <div class="ld-card__meta">{' '.join(meta)}</div>
{end_tag}""".strip()
        )
    if not cards:
        return '<p class="text-muted">Sem materiais cadastrados.</p>'
    return '<div class="ld-grid">\n' + "\n".join(cards) + "\n</div>\n"


def render_parceiros() -> str:
    items = _load("parceiros")
    cards = []
    for it in items:
        href = it.get("link") or "#"
        cards.append(
            f"""
<a class="ld-card" href="{_e(href)}" target="_blank" rel="noopener">
  <span class="ld-card__tag">parceiro</span>
  <h3>{_e(it.get('nome',''))}</h3>
  <p>{_e(it.get('papel',''))}</p>
</a>""".strip()
        )
    if not cards:
        return '<p class="text-muted">Sem parceiros cadastrados.</p>'
    return '<div class="ld-grid">\n' + "\n".join(cards) + "\n</div>\n"


# ---------------------------------------------------------------------------
# Substack RSS — blog lives on Substack; we just mirror the latest posts here.
# ---------------------------------------------------------------------------


def _fetch_substack_items(url: str, max_items: int = 5) -> list[dict]:
    """Fetch RSS from a Substack publication and return parsed items.

    Accepts both the publication root (`https://labdados.substack.com`) and
    a direct feed URL ending in `/feed`.
    """
    feed_url = url.rstrip("/")
    if not feed_url.endswith("/feed"):
        feed_url = f"{feed_url}/feed"
    req = urllib.request.Request(feed_url, headers={"User-Agent": "labdados-site/0.1"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml = resp.read()
    root = ET.fromstring(xml)
    channel = root.find("channel")
    if channel is None:
        return []
    items: list[dict] = []
    for item in channel.findall("item")[:max_items]:
        def t(tag: str) -> str:
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""
        # Description in Substack RSS is HTML; strip tags for a teaser.
        desc_html = t("description")
        teaser = " ".join(
            ET.fromstring(f"<x>{desc_html}</x>").itertext()
        ).strip() if desc_html else ""
        teaser = teaser[:220].rstrip() + ("…" if len(teaser) > 220 else "")
        try:
            dt = parsedate_to_datetime(t("pubDate"))
            date_str = dt.strftime("%d %b %Y")
        except Exception:
            date_str = ""
        items.append(
            {
                "title": t("title"),
                "link": t("link"),
                "date": date_str,
                "teaser": teaser,
            }
        )
    return items


def render_blog(max_items: int = 5) -> str:
    url = os.environ.get("LABDADOS_SUBSTACK_URL", "").strip()
    pub_url = url.rstrip("/") if url else ""
    if not url:
        return (
            '<div class="ld-card" style="grid-column: 1 / -1; max-width: 720px;">'
            '<span class="ld-card__tag">em breve</span>'
            '<h3>O blog do LabDados está sendo aberto no Substack</h3>'
            '<p>Vamos publicar notas técnicas, anúncios de versões e relatos de pesquisa.'
            ' Quando o canal estiver no ar, esta página passa a listar os posts mais recentes'
            ' automaticamente — e você pode assinar por e-mail direto do Substack.</p>'
            "</div>\n"
        )
    try:
        items = _fetch_substack_items(url, max_items=max_items)
    except Exception as exc:  # network errors should not break the build
        print(f"[build_data] WARNING: Substack fetch failed: {exc}", file=sys.stderr)
        items = []
    if not items:
        return (
            '<div class="ld-card" style="grid-column: 1 / -1; max-width: 720px;">'
            '<span class="ld-card__tag">blog</span>'
            '<h3>Nosso blog fica no Substack</h3>'
            f'<p>Acesse <a href="{_e(pub_url)}" target="_blank" rel="noopener">'
            f'{_e(pub_url)}</a> e assine por e-mail.</p>'
            "</div>\n"
        )
    cards = []
    for it in items:
        cards.append(
            f"""
<a class="ld-card" href="{_e(it['link'])}" target="_blank" rel="noopener">
  <span class="ld-card__tag">post · substack</span>
  <h3>{_e(it['title'])}</h3>
  <p>{_e(it['teaser'])}</p>
  <div class="ld-card__meta"><code>{_e(it['date'])}</code></div>
</a>""".strip()
        )
    follow = (
        f'<p style="margin-top:1.25rem;"><a class="ld-cta ld-cta--ghost" '
        f'href="{_e(pub_url)}" target="_blank" rel="noopener">'
        f'Assinar no Substack →</a></p>'
    )
    return (
        '<div class="ld-grid">\n' + "\n".join(cards) + "\n</div>\n" + follow
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    for name in SHEET_BACKED:
        _maybe_sync_sheet(name)

    renderers = {
        "equipe": render_equipe,
        "ferramentas": render_ferramentas,
        "pesquisas": render_pesquisas,
        "cursos": render_cursos,
        "parceiros": render_parceiros,
        "blog": render_blog,
    }
    for name, fn in renderers.items():
        out = OUT / f"{name}.html"
        out.write_text(fn(), encoding="utf-8")
        print(f"[build_data] wrote {out.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
