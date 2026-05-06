# Site do LabDados

Site institucional do **Laboratório de Dados e Pesquisa Empírica em Direito**
da FGV Direito SP — <https://lab-dados.github.io/site>.

> Este README é para **quem vai escrever conteúdo** (texto, equipe, lista de
> ferramentas etc.). Se você é programador(a) e quer mexer no código,
> estilos ou deploy, leia o [`README-dev.md`](./README-dev.md).

---

## O que dá pra editar sem programar

Praticamente todo conteúdo do site fica em dois lugares:

1. **Páginas de texto** — em `index.qmd` (home), e nas pastas
   `sobre/`, `pesquisa/`, `aprenda/`, `ferramentas/`, `equipe/` e `blog/`.
   São arquivos `.qmd` (Markdown). Você edita o texto direto.

2. **Listas de cartões** (equipe, ferramentas, pesquisas, cursos, parceiros)
   — em arquivos YAML dentro de `_data/`. Cada arquivo é uma lista de itens,
   um por bloco.

Se mexer só nesses dois lugares, o site se atualiza sozinho assim que a
mudança chegar no branch `main`.

---

## Editar pelo navegador (sem instalar nada)

1. Vá para o repositório no GitHub: <https://github.com/lab-dados/site>.
2. Abra o arquivo que você quer mudar (ex.: `_data/equipe.yml`).
3. Clique no ícone de **lápis** (✏️) no canto superior direito.
4. Edite, role pra baixo, escreva uma mensagem curta como
   *"adiciona Fulana à equipe"* e clique em **Commit changes**.
5. Pronto. Em ~2 minutos, o site novo está no ar. Acompanhe em
   [Actions](https://github.com/lab-dados/site/actions).

> Se você não tem permissão de escrita no repositório, peça a um(a)
> coordenador(a). Alternativa: use o botão **Fork** + abra um Pull Request.

---

## Como editar cada coisa

### Adicionar uma pessoa à equipe

Arquivo: [`_data/equipe.yml`](./_data/equipe.yml)

Copie um dos blocos existentes e troque os campos. Tudo é opcional, exceto
`nome`, `papel` e `bio`.

```yaml
- nome: "Maria Souza"
  papel: "Pesquisadora"
  bio: "Uma frase curta sobre o que ela faz no laboratório."
  foto: "https://github.com/mariasouza.png"   # use a foto do GitHub se tiver
  github: "mariasouza"
  linkedin: "maria-souza"
  email: "maria@fgv.br"
```

Dicas:

- A **foto** pode ser qualquer URL pública. Se a pessoa tem GitHub, basta usar
  `https://github.com/<usuario>.png` — não precisa subir imagem.
- A ordem dos blocos no YAML é a ordem em que aparecem no site.

### Adicionar uma ferramenta

Arquivo: [`_data/ferramentas.yml`](./_data/ferramentas.yml)

```yaml
- nome: "Nome da ferramenta"
  categoria: "pacote"      # pacote, sdk, skill, dados, servico
  status: "estavel"        # estavel, beta, alpha, experimental
  descricao: "Uma frase explicando o que ela faz."
  linguagem: "Python"
  repo: "https://github.com/lab-dados/sua-ferramenta"
  pip: "sua-ferramenta"    # opcional, só se estiver no PyPI
```

A categoria define em qual seção o cartão aparece na página de
[Ferramentas](https://lab-dados.github.io/site/ferramentas/).

### Adicionar uma pesquisa

Arquivo: [`_data/pesquisas.yml`](./_data/pesquisas.yml)

```yaml
- titulo: "Pesquisa sobre X"
  status: "em-andamento"   # em-andamento, concluida, planejada
  resumo: "Uma ou duas frases sobre a pergunta de pesquisa."
  parceiros: ["Instituição A", "Instituição B"]
  ano_inicio: 2026
  repo: "https://github.com/lab-dados/projeto-x"   # opcional
```

### Adicionar um curso, oficina ou livro

Arquivo: [`_data/cursos.yml`](./_data/cursos.yml)

```yaml
- titulo: "Nome do curso"
  tipo: "curso"            # curso, oficina, livro, palestra
  ano: 2026
  descricao: "Pra quem é o curso e o que ele cobre, em uma frase."
  link: "https://link-para-os-materiais.com"
```

### Escrever um post de blog

O blog do LabDados fica no **Substack**, não neste repositório. Para postar:

1. Vá para <https://labdados.substack.com> (ou o nome que escolhermos).
2. Faça login com a conta institucional.
3. Clique em **New post** e escreva direto no editor do Substack.
4. Publique. Em até 24h o site puxa o post novo automaticamente (também
   dá pra forçar agora indo em
   [Actions → Render and deploy site → Run workflow](https://github.com/lab-dados/site/actions/workflows/publish.yml)).

> Por que Substack e não aqui? Distribuição por e-mail é grátis e funciona
> melhor que reinventar a roda. O site puxa os 5 posts mais recentes via
> RSS e mostra na home e na página `/blog/`.

---

## Edição via Google Sheets (opcional)

Se preferir manter equipe / ferramentas / pesquisas em uma planilha do Google,
o site sabe importar isso automaticamente.

1. Crie uma planilha no Google Sheets com as **mesmas colunas** do YAML
   correspondente (ex.: `nome,papel,bio,foto,github,linkedin,email` para
   equipe). Cada linha vira um item.
2. No menu **Arquivo → Compartilhar → Publicar na web**, escolha **CSV** e
   copie a URL gerada.
3. No GitHub, vá em
   [**Settings → Secrets and variables → Actions**](https://github.com/lab-dados/site/settings/secrets/actions)
   e crie um secret com o nome certo (ex.: `LABDADOS_SHEETS_CSV_EQUIPE`)
   colando a URL. Os nomes de secret aceitos são:

   - `LABDADOS_SHEETS_CSV_EQUIPE`
   - `LABDADOS_SHEETS_CSV_FERRAMENTAS`
   - `LABDADOS_SHEETS_CSV_PESQUISAS`
   - `LABDADOS_SHEETS_CSV_CURSOS`
   - `LABDADOS_SHEETS_CSV_PARCEIROS`

4. Toda vez que alguém editar a planilha, basta disparar o deploy: na aba
   [Actions](https://github.com/lab-dados/site/actions) → workflow
   *Render and deploy site* → **Run workflow**. Em ~2 minutos o site reflete
   o que está na planilha.

> **Quando usar Sheets x YAML?** Se a sua equipe tem gente que não usa
> GitHub, Sheets é mais confortável. Para 90% dos casos, editar o YAML
> direto pelo navegador é mais simples.

---

## Quem pode publicar?

Qualquer pessoa com permissão de escrita no repositório `lab-dados/site`.
Quem não tem, abre Pull Request e um(a) coordenador(a) revisa.

## Onde pedir ajuda

- Bug ou problema visual: abra uma issue em
  <https://github.com/lab-dados/site/issues>.
- Dúvida de conteúdo: mande mensagem no canal interno do laboratório.
- Quebrou o site? Não se preocupe — o GitHub Actions só publica versões
  que renderizam sem erro. Se algo está errado no que você editou, o site
  no ar continua igual; é só corrigir o YAML que ele volta.
