"""Pre-render hook: turn YAML data files into HTML partials Quarto pages include.

Run by Quarto via `pre-render` in `_quarto.yml`. Two modes:

1. (default) Read YAMLs in `_data/` and write HTML to `_partials/`.
2. (opt-in) If env var `LABDADOS_SHEETS_CSV_<NAME>` is set, fetch CSV from that
   URL first and overwrite `_data/<name>.yml` before rendering.

Cards are `<div>`s with a stretched-link pattern, not `<a>`s, because Pandoc
does not preserve `<a>` wrapping block-level content.

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
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data"
OUT = ROOT / "_partials"
OUT.mkdir(exist_ok=True)

SHEET_BACKED = ("equipe", "ferramentas", "pesquisas", "cursos", "parceiros")


# ---------------------------------------------------------------------------
# Optional Google Sheets sync
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
    except Exception as exc:
        print(f"[build_data] WARNING: failed to fetch {env}: {exc}", file=sys.stderr)
        return
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        print(f"[build_data] WARNING: {env} returned no rows", file=sys.stderr)
        return
    cleaned = []
    for r in rows:
        item: dict = {}
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
# Helpers
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
        f'<a href="{_e(href)}" target="_blank" rel="noopener" '
        f'aria-label="{_e(label)}" title="{_e(label)}">'
        f'<i class="bi bi-{icon}"></i></a>'
    )


def _obfuscate_email(addr: str) -> str:
    """Render an email as text safe-ish from naive scrapers (uses [at]/[.])."""
    local, _, domain = addr.partition("@")
    domain = domain.replace(".", " [.] ")
    return f"{local} [at] {domain}".strip()


def _status_pill(status: str) -> str:
    cls = "ld-pill"
    if status in {"estavel", "concluida"}:
        cls += " ld-pill--green"
    elif status in {"em-andamento", "beta"}:
        cls += " ld-pill--navy"
    elif status in {"alpha", "experimental", "planejada"}:
        cls += " ld-pill--coral"
    return f'<span class="{cls}">{_e(status)}</span>'


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
        if p.get("site"):
            links.append(_icon_link("globe", p["site"], "Site pessoal"))
        if p.get("fgv"):
            links.append(_icon_link("mortarboard", p["fgv"], "Página na FGV"))
        if p.get("lattes"):
            links.append(_icon_link("file-earmark-text", p["lattes"], "Currículo Lattes"))
        if p.get("orcid"):
            links.append(_icon_link("hash", p["orcid"], "ORCID"))
        if p.get("email"):
            links.append(_icon_link("envelope", f"mailto:{p['email']}", "E-mail"))

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


def _ferramenta_card(it: dict) -> str:
    # Primary click goes to the docs (where users actually want to land);
    # fallback to repo or other link when there is no docs site.
    primary = it.get("docs") or it.get("repo") or it.get("link") or "#"
    tags = []
    if it.get("linguagem"):
        tags.append(f'<code>{_e(it["linguagem"])}</code>')
    if it.get("pip"):
        tags.append(f'<code>pip install {_e(it["pip"])}</code>')
    if it.get("status"):
        tags.append(_status_pill(it["status"]))

    extras = []
    if it.get("repo"):
        extras.append(f'<a href="{_e(it["repo"])}" target="_blank" rel="noopener">repo</a>')
    if it.get("docs"):
        extras.append(f'<a href="{_e(it["docs"])}" target="_blank" rel="noopener">docs</a>')
    if it.get("link") and it.get("link") not in (it.get("repo"), it.get("docs")):
        extras.append(f'<a href="{_e(it["link"])}" target="_blank" rel="noopener">site</a>')
    extras_html = (
        f'<div class="ld-card__links">{" · ".join(extras)}</div>' if extras else ""
    )
    return (
        '<div class="ld-card">'
        f'<span class="ld-card__tag">{_e(it.get("categoria", ""))}</span>'
        f'<h3><a class="ld-card__link" href="{_e(primary)}" target="_blank" rel="noopener">'
        f'{_e(it.get("nome", ""))}</a></h3>'
        f'<p>{_e(it.get("descricao", ""))}</p>'
        f'<div class="ld-card__meta">{" ".join(tags)}</div>'
        f"{extras_html}"
        "</div>"
    )


def render_ferramentas() -> str:
    items = _load("ferramentas")
    groups: dict[str, list[dict]] = {}
    label = {
        "pacote": "Pacotes Python",
        "skill": "Skills do Claude Code",
        "dados": "Dados abertos",
    }
    for it in items:
        groups.setdefault(it.get("categoria", "outros"), []).append(it)

    blocks = []
    for cat in ("pacote", "skill", "dados"):
        bucket = groups.get(cat)
        if not bucket:
            continue
        cards = [_ferramenta_card(it) for it in bucket]
        blocks.append(
            f'<h3 id="cat-{cat}" style="margin-top:2.25rem">{_e(label.get(cat, cat.title()))}</h3>'
            '<div class="ld-grid">' + "".join(cards) + "</div>"
        )
    if not blocks:
        return '<p class="text-muted">Sem ferramentas cadastradas.</p>'
    return "\n".join(blocks) + "\n"


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
        href = it.get("repo") or it.get("link")
        title = _e(it.get("titulo", ""))
        if href:
            title_html = (
                f'<h3><a class="ld-card__link" href="{_e(href)}" target="_blank" '
                f'rel="noopener">{title}</a></h3>'
            )
        else:
            title_html = f"<h3>{title}</h3>"
        cards.append(
            '<div class="ld-card">'
            '<span class="ld-card__tag">pesquisa</span>'
            f"{title_html}"
            f'<p>{_e(it.get("resumo", ""))}</p>'
            f'<div class="ld-card__meta">{" ".join(meta_bits)}</div>'
            "</div>"
        )
    if not cards:
        return '<p class="text-muted">Sem pesquisas cadastradas.</p>'
    return '<div class="ld-grid">' + "".join(cards) + "</div>\n"


def render_cursos() -> str:
    items = _load("cursos")
    label = {"curso": "Curso", "oficina": "Oficina", "livro": "Livro", "palestra": "Palestra"}
    cards = []
    for it in items:
        meta = [_status_pill(it.get("tipo", "")), f'<code>{_e(it.get("ano", ""))}</code>']
        href = it.get("link")
        title = _e(it.get("titulo", ""))
        if href:
            title_html = (
                f'<h3><a class="ld-card__link" href="{_e(href)}" target="_blank" '
                f'rel="noopener">{title}</a></h3>'
            )
        else:
            title_html = f"<h3>{title}</h3>"
        cards.append(
            '<div class="ld-card">'
            f'<span class="ld-card__tag">{_e(label.get(it.get("tipo", ""), it.get("tipo", "")))}</span>'
            f"{title_html}"
            f'<p>{_e(it.get("descricao", ""))}</p>'
            f'<div class="ld-card__meta">{" ".join(meta)}</div>'
            "</div>"
        )
    if not cards:
        return '<p class="text-muted">Sem materiais cadastrados.</p>'
    return '<div class="ld-grid">' + "".join(cards) + "</div>\n"


def render_parceiros() -> str:
    items = _load("parceiros")
    cards = []
    for it in items:
        href = it.get("link") or "#"
        title = _e(it.get("nome", ""))
        cards.append(
            '<div class="ld-card">'
            '<span class="ld-card__tag">parceiro</span>'
            f'<h3><a class="ld-card__link" href="{_e(href)}" target="_blank" '
            f'rel="noopener">{title}</a></h3>'
            f'<p>{_e(it.get("papel", ""))}</p>'
            "</div>"
        )
    if not cards:
        return '<p class="text-muted">Sem parceiros cadastrados.</p>'
    return '<div class="ld-grid">' + "".join(cards) + "</div>\n"


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
    }
    for name, fn in renderers.items():
        out = OUT / f"{name}.html"
        out.write_text(fn(), encoding="utf-8")
        print(f"[build_data] wrote {out.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
