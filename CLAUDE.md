# Sistema Financeiro — instruções do projeto

Programa desktop único (PySide6) que reúne os 5 sistemas do financeiro da TCM numa barra
lateral, com acesso por grupos do AD e cada sistema no seu próprio repositório.

## Regras

- Sem commit, push, tag ou release até o Erik dizer "Salvar versão" (regra global dele).
- Este repositório e o `Tcm-ui` são **públicos**: não escrever nos docs quem é admin do
  domínio nem outros detalhes sensíveis da rede.
- Repositórios locais ficam em `C:\Users\erik.freitas\Projetos\`, fora do OneDrive.
- As pastas do FileServer (`15. Automações\Projetos_Financeiro`) são só leitura.
- Economize tokens: trabalhe direto, sem subagentes; não releia planos nem ledgers inteiros;
  use `graphify query` antes de ler código.

## Estrutura

- Design (autoridade): `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md`.
  Planos 1 a 8 em `docs/superpowers/plans/`; ledgers com as decisões em `.superpowers/sdd/`
  (local, fora do git). Consulte só quando precisar do porquê de uma decisão.
- Casca: `src/sistema_financeiro/` (`acesso`, `descoberta`, `app`), `main.py` (`--verificar`),
  `ferramentas/args_pyinstaller.py`, `build.ps1`.
- Biblioteca comum: `Tcm-ui` (design system, `JanelaPrincipal`, contrato de módulo
  `tcm_ui.modulo`, atualizador, `rodar_avulso`, log, login Microsoft `tcm_ui.microsoft`).

| Barra lateral        | Repositório      | Id do módulo        | Grupo AD            |
|----------------------|------------------|---------------------|---------------------|
| RoboAgregado         | `Send_Agregados` | `robo_agregado`     | `SF-RoboAgregado`   |
| Mesclador de PDFs    | `pdf-merge`      | `mesclador`         | `SF-Mesclador`      |
| Enviador de PDF + XML| `pdf-xml-mailer` | `enviador_pdf_xml`  | `SF-EnviadorPDFXML` |
| Renomeador de CT-e   | `Renomeador_CTE` | `renomeador_cte`    | `SF-RenomeadorCTE`  |
| Renomeador de XML    | `Renomeador_CTE` | `renomeador_xml`    | `SF-RenomeadorCTE`  |
| Sistema Catraca      | `Projeto_Catraca`| `sistema_catraca`   | `SF-Catraca`        |

Admin: grupo `SF-Admin`. Todos os grupos já existem no AD.

## Versões atuais (lançadas em 26/11/2026)

`Tcm-ui` v1.6.1 (tag), Releases `Send_Agregados` v2.1.1, `pdf-merge` v3.0.0, `pdf-xml-mailer`
v2.1.0, `Renomeador_CTE` v2.1.0, `Projeto_Catraca` v2.0.1, `Sistema-Financeiro` v1.6.0.
Os usuários recebem pela atualização automática (testada e funcionando).
A 1.5.1 trouxe o refino pós-lançamento: no Renomeador, PDF com AES, fechamento e pasta digitada;
no RoboAgregado, espera do e-mail atual ao fechar; no calendário do Tcm-ui, os dias da semana
inteiros; e os READMEs.
A 1.6.0 trouxe o Renomeador de XML (módulo `renomeador_xml` no `Renomeador_CTE` 2.1.0, mesmo
grupo `SF-RenomeadorCTE`; a Release do `Renomeador_CTE` leva também o `RenomeadorXML.exe`).

## Como trabalhar

- Testes: `.venv\Scripts\python -m pytest -q` em cada repositório. Última contagem: `Tcm-ui`
  194, `Projeto_Catraca` 129, casca 51, `Renomeador_CTE` 84, `pdf-xml-mailer` 123,
  `pdf-merge` 27, `Send_Agregados` 57.
- Build: `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1`. Na casca, `-Local`
  instala os clones vizinhos (`../Tcm-ui`, `../Send_Agregados` etc.) com `--no-cache-dir`.
- Pins dos módulos em `requirements.txt`; versões das bibliotecas de terceiros em
  `versoes.txt` (incluído pelos dois `requirements*.txt`). Ao mudar, testar o `.exe` antes de salvar.
- Ordem ao lançar: `Tcm-ui` primeiro (e atualizar os pins `@vX` dos irmãos e da casca), depois
  os módulos, a casca por último. Cada `release.yml` falha se a tag ≠ `__version__`. Uma tag
  nova de módulo chega a todos os usuários do `.exe` avulso.
- Verificação do `.exe`: usa proxy morto (a Conta Microsoft faz um GET ao ser criada) e
  `CATRACA_DADOS` temporário; os testes trocam `instancia.FABRICA_CONTA` por uma fábrica sem rede.
- Visual sem captura de tela: `widget.grab()` com `QT_QPA_PLATFORM=offscreen`. Em offscreen o
  diálogo de primeiro acesso do Enviador trava o script: deixe esse módulo de fora.
- Atenção: `enviar_fretes.carregar_env` põe `SMTP_SENHA` no `os.environ` do processo, que é
  compartilhado com os outros módulos na casca.

## Pendente

- Grafo do `Tcm-ui` gerado em 26/11 (só AST; o README ficou fora da extração semântica). O
  `graphify.exe` falha com "uv trampoline failed to canonicalize script path"; use
  `C:\Users\erik.freitas\.local\graphify-venv\Scripts\python.exe -m graphify ...`. Os hooks do
  `.claude/settings.json` do Tcm-ui chamam o `.exe` e podem falhar até ele ser reinstalado.
- **Não remova a seção "graphify" abaixo** (é a instrução de consultar o grafo). Depois de
  mudanças grandes aqui: `graphify update .`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. When the answer is under a Markdown heading, `graphify section "<heading>"` prints that section's text, so the .md need not be opened. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
