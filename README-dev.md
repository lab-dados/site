# Site do LabDados — guia para desenvolvedores

Site estático em **Quarto**, deploy automático no **GitHub Pages** via Actions.
O conteúdo de listas (equipe, ferramentas, pesquisas, cursos, parceiros) vem
de YAMLs em `_data/`, transformados em HTML por um script Python que roda
como `pre-render` do Quarto.

> Conteúdo institucional? Veja [`README.md`](./README.md).

---

## Stack

| Camada | Tecnologia |
|---|---|
| Render | Quarto ≥ 1.5 |
| Tema | SCSS + Bootstrap 5 (via Cosmo) |
| Tipografia | Inter, Space Grotesk, JetBrains Mono (Google Fonts) |
| Pre-render | Python 3.12 + PyYAML, gerenciado por `uv` |
| Conteúdo dinâmico | Listings nativos do Quarto + partials HTML em `_partials/` |
| CI/CD | GitHub Actions (`actions/deploy-pages`) |

Sem JS framework, sem build complicado. O único JS de runtime é um rotador
do bloco de código no hero (`index.qmd`, ~10 linhas).

---

## Estrutura

```
labdados-site/
├── _quarto.yml              # config do site, navbar, theme
├── index.qmd                # home
├── ferramentas/index.qmd    # seções
├── pesquisa/index.qmd
├── aprenda/index.qmd
├── equipe/index.qmd
├── sobre/index.qmd
├── blog/
│   ├── index.qmd            # listing
│   └── posts/<slug>/index.qmd
├── _data/                   # YAML editado por humanos
│   ├── equipe.yml
│   ├── ferramentas.yml
│   ├── pesquisas.yml
│   ├── cursos.yml
│   └── parceiros.yml
├── _partials/               # HTML gerado (gitignored)
├── tools/build_data.py      # pre-render: YAML/Sheets → HTML
├── assets/
│   ├── theme.scss           # paleta, tipografia, componentes
│   ├── styles.css           # ajustes leves
│   ├── fonts.html           # <link> para Google Fonts
│   ├── logo.svg
│   └── favicon.svg
├── pyproject.toml           # deps Python (só pyyaml por padrão)
└── .github/workflows/publish.yml
```

---

## Rodar localmente

Pré-requisitos: [Quarto ≥ 1.5](https://quarto.org/docs/get-started/),
[`uv`](https://docs.astral.sh/uv/), Python 3.12.

```bash
uv sync                           # instala pyyaml no .venv
uv run quarto preview             # http://127.0.0.1:4200 com hot reload
```

Render single-shot:

```bash
uv run quarto render
```

Quarto chama `tools/build_data.py` automaticamente como pre-render
(declarado em `_quarto.yml`). O script:

1. **Opcional:** se houver env var `LABDADOS_SHEETS_CSV_<NOME>` apontando
   para um CSV publicado pelo Google Sheets, baixa e sobrescreve o
   `_data/<nome>.yml`. Se a env var não estiver setada, ignora.
2. Lê os YAMLs em `_data/` e escreve `_partials/<nome>.html` com cards
   prontos (classes `.ld-card`, `.ld-person`, `.ld-pill` definidas no SCSS).
3. As páginas `.qmd` incluem esses partials via
   `{{< include /_partials/<nome>.html >}}`.

Para rodar só o pre-render (debug):

```bash
uv run python tools/build_data.py
```

---

## Tema e paleta

`assets/theme.scss` define:

- **Paleta** — navy `#0a1f44` (primário, herdeiro do azul FGV), green
  `#00a37a` (acento de ciência aberta), amber `#f5a524`, coral `#ef4444`.
  Tons exportados como custom properties (`--ld-navy`, etc.) para uso em CSS
  inline ocasional.
- **Tipografia** — `Space Grotesk` em headings, `Inter` no corpo,
  `JetBrains Mono` em código. Carregadas via `assets/fonts.html`
  (`include-in-header`).
- **Componentes** — `.ld-hero`, `.ld-codecard`, `.ld-stats`/`.ld-stat`,
  `.ld-grid` + `.ld-card`, `.ld-people` + `.ld-person`, `.ld-pill`,
  `.ld-section`, `.ld-manifesto`, `.ld-cta`. Pensados para serem usados
  via Pandoc fenced divs (`::: {.ld-card}`) ou raw HTML quando há
  necessidade de wrappear um link.

> ⚠️ Pandoc não aceita `[ ::: {.ld-card} … :::](href)` (link em torno de
> fenced div). Para cards clicáveis, use raw HTML — `<a class="ld-card" href>`.

---

## Conteúdo dinâmico

### Blog (Substack RSS)

O blog vive no Substack — não temos posts locais. `tools/build_data.py`
busca o feed RSS da publicação quando a env var `LABDADOS_SUBSTACK_URL`
estiver setada (ex.: `https://labdados.substack.com`) e gera
`_partials/blog.html` com os 5 posts mais recentes. As páginas
`blog/index.qmd` e a home incluem esse partial.

Sem dependência externa: parser é `xml.etree.ElementTree` da stdlib.

Para evitar que o site fique desatualizado quando ninguém der push, o
workflow tem um cron diário (06:00 UTC) que re-renderiza e republica.

### Partials a partir de YAML

Tudo que não é blog (equipe, ferramentas, pesquisas, cursos, parceiros) usa
os partials gerados por `tools/build_data.py`. Esse approach é deliberado:

- **YAML é editável por leigos** via interface web do GitHub.
- **Não precisa de listing custom** (template `.ejs`, R chunks etc.).
- **Sheets continua possível** — basta setar a env var; o YAML é
  sobrescrito, e o caminho é o mesmo.

Para adicionar uma nova seção orientada a YAML:

1. Crie `_data/novo.yml` no formato lista de dicts.
2. Adicione um renderer em `tools/build_data.py` (siga `render_pesquisas`
   como exemplo).
3. Em `main()`, registre `"novo": render_novo` no dict `renderers`.
4. Adicione `"novo"` em `SHEET_BACKED` se quiser permitir sync via Sheet.
5. Inclua o partial onde quiser: `{{< include /_partials/novo.html >}}`.

---

## Deploy

`.github/workflows/publish.yml` roda em todo push para `main`:

1. Checkout.
2. Setup `uv` + `uv sync`.
3. Setup Quarto.
4. `quarto render` (que chama o pre-render).
5. Upload de `_site/` como artifact do GitHub Pages.
6. Deploy.

Variáveis de ambiente injetadas no step de render (todas opcionais; se
ausentes, o script usa os YAMLs versionados):

- `LABDADOS_SUBSTACK_URL` — URL da publicação no Substack (configurar como
  *variable*, não secret, em **Settings → Secrets and variables → Actions
  → Variables**).
- `LABDADOS_SHEETS_CSV_EQUIPE`
- `LABDADOS_SHEETS_CSV_FERRAMENTAS`
- `LABDADOS_SHEETS_CSV_PESQUISAS`
- `LABDADOS_SHEETS_CSV_CURSOS`
- `LABDADOS_SHEETS_CSV_PARCEIROS`

Configure os `*_CSV_*` como secrets em **Settings → Secrets → Actions**.

### Habilitar Pages

No GitHub do repo: **Settings → Pages → Source: GitHub Actions**. Não usar
branch `gh-pages` — o workflow já publica direto via `actions/deploy-pages`.

### Domínio próprio

Quando definirmos o domínio (`lab-dados.com`, `labdados.ai.br`...):

1. Crie um arquivo `CNAME` na raiz com o domínio (já está em `resources` no
   `_quarto.yml`, então é copiado pro `_site/`).
2. Atualize `site-url` em `_quarto.yml`.
3. Configure DNS conforme docs do Pages.

---

## Convenções de conteúdo

- **Texto curto e direto.** Sem "bem-vindo!", "navegue à vontade", etc.
- **Português.** Todo o conteúdo público é em português; nomes técnicos
  ficam em inglês quando estabilizados (`pacote`, `cjpg`).
- **Datas** em ISO (`2026-05-05`).
- **Links externos** abrem em nova aba (`link-external-newwindow: true` no
  `_quarto.yml`).

---

## Como reusar este site como template

O laboratório decidiu manter este repositório simples justamente para servir
de template para outros grupos de pesquisa. Para reusar:

1. Use **"Use this template"** no GitHub.
2. Substitua `_data/*.yml` pelo seu conteúdo.
3. Edite `assets/theme.scss` (ao menos `$ld-navy` e `$ld-green`) e
   `assets/logo.svg`.
4. Atualize `_quarto.yml` (`title`, `description`, `site-url`, `repo-url`,
   navbar, footer).
5. Habilite Pages como descrito acima.

Não há nada específico do LabDados no código — só nos dados e no logo.

---

## Roadmap técnico curto

- [ ] Domínio próprio + CNAME.
- [ ] Setar `LABDADOS_SUBSTACK_URL` quando a publicação estiver criada.
- [ ] Embed da agenda Google Calendar em `aprenda/`.
- [ ] Página `/template/` com instruções para outros laboratórios.

## Licença

Código sob **MIT**, conteúdo sob **CC BY 4.0**.
