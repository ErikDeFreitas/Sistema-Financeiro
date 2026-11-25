# Sistema Financeiro — instruções e estado do projeto

Programa desktop único (PySide6) que reúne os 5 sistemas do financeiro da TCM numa barra
lateral, com acesso por grupos do AD e cada sistema no seu próprio repositório.

## Leia antes de qualquer coisa

- Design (autoridade): `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md`
- Plano 1 (concluído): `docs/superpowers/plans/2026-11-19-plano-1-tcm-ui.md`
- Ledger do plano 1, com as decisões tomadas e os pontos pendentes para os planos 2 e 3:
  `.superpowers/sdd/2026-11-19-plano-1-tcm-ui/progress.md` (local, fora do git)

## Regras

- Sem commit, push, tag ou release até o Erik dizer "Salvar versão" (regra global dele).
- Este repositório e o `Tcm-ui` são **públicos**: não escrever nos docs quem é admin do
  domínio nem outros detalhes sensíveis da rede.
- Repositórios locais ficam em `C:\Users\erik.freitas\Projetos\`, fora do OneDrive.
- As pastas do FileServer (`15. Automações\Projetos_Financeiro`) são só leitura.

## Onde paramos (25/11/2026)

**Feito**
- Plano 1 — `Tcm-ui` v1.0.0: design system do RoboAgregado, `JanelaPrincipal`, contrato de
  módulo (`tcm_ui.modulo`), atualizador, `rodar_avulso`, vitrine (`python -m tcm_ui.demo`).
  Salvo: tag `v1.0.0` em `ErikDeFreitas/Tcm-ui`.
- Docs (design + plano 1) salvos neste repositório (commit `cdc5080`).
- Plano 2 — `docs/superpowers/plans/2026-11-23-plano-2-roboagregado.md`, implementado e
  revisado:
  - `Tcm-ui` 1.1.0: `rodar_avulso(..., atualizar=)`, `tcm_ui.registro.configurar_log` (log em
    `<pasta_dados>\logs\<id>.log` + exceções não tratadas), reinício falho avisado, `sync` ao fechar.
    85 testes.
  - `Send_Agregados` 2.0.0: pacote `src/robo_agregado/` (`dados.py`, `modulo.py`, `tela.py`,
    `instancia.py`), `main.py`, `build.ps1` com `--collect-data`, `release.yml` que falha se a
    tag ≠ `__version__`. Dados continuam em `%LOCALAPPDATA%\RoboAgregado`; `config.ini` só é
    trocado quando chega versão mais nova. 22 testes. `.exe` gerado e conferido nos 2 temas.
  - Ledger com as decisões: `.superpowers/sdd/2026-11-23-plano-2-roboagregado/progress.md`.

- Plano 3 (a casca) — `docs/superpowers/plans/2026-11-23-plano-3-casca.md`, implementado e
  revisado: pacote `src/sistema_financeiro/` (`acesso`, `descoberta`, `app`), `main.py`
  (`--verificar`), `ferramentas/args_pyinstaller.py`, `build.ps1` (`-Local` usa os clones
  vizinhos), `requirements*.txt`,
  `.github/workflows/release.yml`, `README.md`. 35 testes. Ledger:
  `.superpowers/sdd/2026-11-23-plano-3-casca/`.
- Salvo em 23/11/2026, com tags e Releases: `Tcm-ui` `v1.1.0`, `Send_Agregados` `v2.0.0`
  (Release automática para os usuários do RoboAgregado), `Sistema-Financeiro` `v1.0.0` (Release
  do `SistemaFinanceiro.exe`). Grupo `SF-Admin` já existe no AD.
- Plano 4 (Mesclador) — `docs/superpowers/plans/2026-11-23-plano-4-mesclador.md`, implementado,
  salvo sem tag. Casca 1.1.0: `requirements.txt` com `tcm-ui@v1.2.0`,
  `robo-agregado@v2.0.1`, `mesclador@v3.0.0`; `build.ps1 -Local` instala `../Tcm-ui`,
  `../Send_Agregados`, `../pdf-merge` e a casca juntos (`--no-cache-dir`). Barra: RoboAgregado,
  Mesclador de PDFs. Ledger: `.superpowers/sdd/2026-11-23-plano-4-mesclador/`.
  A ordem de salvar está no plano 7, logo abaixo (a casca 1.1.0 não sai sozinha: vai
  junto na 1.4.0). A TI cria o grupo `SF-Mesclador`.

- Plano 5 (Enviador PDF + XML) — `docs/superpowers/plans/2026-11-24-plano-5-enviador.md`,
  implementado, salvo sem tag. Casca 1.2.0: `requirements.txt` com
  `tcm-ui@v1.3.0` e `enviador-pdf-xml@v2.0.0` (repositório `pdf-xml-mailer`); `build.ps1 -Local`
  também instala `../pdf-xml-mailer`; `msal`/`msal_extensions` entram no `.exe` por
  `--hidden-import`; a verificação do `.exe` usa proxy morto (a Conta Microsoft faz um GET ao ser
  criada) e os testes trocam `instancia.FABRICA_CONTA` por uma fábrica que falha sem rede. Barra:
  RoboAgregado, Mesclador de PDFs, Enviador de PDF + XML. 40 testes. Ledger:
  `.superpowers/sdd/2026-11-24-plano-5-enviador/`.
  A ordem de salvar mudou: está no plano 7, logo abaixo (planos 4 a 7 saem juntos).

- Plano 6 (Renomeador de CT-e) — `docs/superpowers/plans/2026-11-24-plano-6-renomeador.md`,
  implementado, salvo sem tag. Casca 1.3.0: `requirements.txt` com
  `tcm-ui@v1.4.0` e `renomeador-cte@v2.0.0` (repositório `Renomeador_CTE`, pacote
  `renomeador_cte`, grupo `SF-RenomeadorCTE`); `build.ps1 -Local` também instala
  `../Renomeador_CTE`; nada mudou em `descoberta.ORDEM` nem em `args_pyinstaller.py`. Barra:
  RoboAgregado, Mesclador de PDFs, Enviador de PDF + XML, Renomeador de CT-e. 47 testes. Ledger:
  `.superpowers/sdd/2026-11-24-plano-6-renomeador/`.
  (A ordem de salvar dos planos 4 a 7 está no plano 7, logo abaixo.) A TI cria os grupos
  `SF-Mesclador`, `SF-EnviadorPDFXML` e `SF-RenomeadorCTE`.

- Plano 7 (Catraca) — `docs/superpowers/plans/2026-11-24-plano-7-catraca.md`, implementado,
  salvo sem tag. Casca 1.4.0: `requirements.txt` com `tcm-ui@v1.5.0` e
  `sistema-catraca @ ...Projeto_Catraca@v2.0.0` (pacote `sistema_catraca`, grupo `SF-Catraca`);
  `build.ps1 -Local` também instala `../Projeto_Catraca` e a verificação do `.exe` usa
  `CATRACA_DADOS` temporário; `descoberta.ORDEM` e `args_pyinstaller.py` não mudaram. Barra:
  RoboAgregado, Mesclador de PDFs, Enviador de PDF + XML, Renomeador de CT-e, Sistema Catraca
  (itens "Relatório de acessos" e "Usuários", sem abas internas). 51 testes. Ledger:
  `.superpowers/sdd/2026-11-24-plano-7-catraca/`.
  **Ordem do "Salvar versão" (planos 4 a 7 juntos)**: `Tcm-ui` v1.5.0 (cobre 1.2.0 a 1.5.0; os
  pins `@v1.2.0`/`@v1.3.0`/`@v1.4.0` dos repositórios irmãos e da casca passam a `@v1.5.0` na
  hora de salvar) → `Send_Agregados` v2.0.1 → `pdf-merge` v3.0.0 → `pdf-xml-mailer` v2.0.0 →
  `Renomeador_CTE` v2.0.0 → `Projeto_Catraca` v2.0.0 → `Sistema-Financeiro` v1.4.0. As tags v2.0.0
  chegam a todos os usuários dos `.exe` avulsos. A TI cria o grupo `SF-Catraca`.
  Pendências do Erik antes/ao salvar: testar a casca fora da rede; conferir a conta Microsoft real
  com o novo `EnviadorEmails.exe` (antes da tag do `pdf-xml-mailer`); testar um PDF real no
  Renomeador (antes da tag do `Renomeador_CTE`); testar um relatório real na Catraca (CSV idêntico
  ao da 1.0.0, antes da tag do `Projeto_Catraca`; conferir também a aba Releases do
  `Projeto_Catraca`, pois a 1.0.0 pode nunca ter sido publicada).

- Plano 8 (login Microsoft padronizado) — spec `docs/superpowers/specs/2026-11-25-login-microsoft-design.md`,
  plano `docs/superpowers/plans/2026-11-25-plano-8-login-microsoft.md`, **implementado, testado pelo Erik
  e lançado em 25/11/2026**.
  `Tcm-ui` 1.6.0: `tcm_ui.microsoft` (Conta MSAL, cache DPAPI compartilhado em
  `%LOCALAPPDATA%\TCM\ContaMicrosoft`, `TCM_CONTA_MICROSOFT` troca a pasta, `abrir_smtp` XOAUTH2,
  `criar_conta_em_segundo_plano`) e `tcm_ui.microsoft_ui.CartaoContaMicrosoft`; extra `tcm-ui[microsoft]`.
  194 testes. `pdf-xml-mailer` 2.1.0 usa o Tcm-ui e migra o login antigo (123 testes).
  `Send_Agregados` 2.1.0: método `microsoft` (padrão; `smtp` antigo vira `microsoft`), botão "Conta de
  envio..." com "Enviar como", `.env` migrado e apagado, `ErroSessao` reabre o diálogo; sem internet não
  abre diálogo sozinho (55 testes). Casca 1.5.0 (51 testes, `.exe` verificado). Ledger:
  `.superpowers/sdd/2026-11-25-plano-8-login-microsoft/`.
  Lançado na ordem: `Tcm-ui` v1.6.0 (tag) → Releases `pdf-xml-mailer` v2.1.0 → `Send_Agregados` v2.1.0
  → `Sistema-Financeiro` v1.5.0. (A primeira tentativa da Release do Enviador falhou numa queda do
  GitHub; a tag foi recriada no mesmo commit.)

**Retomando numa sessão nova (leia isto primeiro)**
- Economize tokens (pedido do Erik): trabalhe direto, sem subagentes; não releia planos nem
  ledgers inteiros; use `graphify query` antes de ler código.
- Estado: planos 1 a 8 implementados, salvos e **lançados em 25/11/2026**. Versões atuais: `Tcm-ui`
  v1.6.0 (tag), Releases `Send_Agregados` v2.1.0, `pdf-merge` v3.0.0, `pdf-xml-mailer` v2.1.0,
  `Renomeador_CTE` v2.0.0, `Projeto_Catraca` v2.0.0 e `Sistema-Financeiro` v1.5.0. Os usuários
  recebem pela atualização automática.
- Testes na última rodada: `Tcm-ui` 194, `Projeto_Catraca` 129, casca 51, `Renomeador_CTE` 58,
  `pdf-xml-mailer` 123, `pdf-merge` 27, `Send_Agregados` 55. Cada um com
  `.venv\Scripts\python -m pytest -q`.
- Build: `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1` (casca: `-Local`).
- A revisão final do plano 7 (integração dos cinco módulos) foi **concluída em 25/11, sem nada que
  impeça o lançamento**: contratos, estado compartilhado, barra lateral em 900×600, versões × pins e
  compatibilidade dos atualizadores antigos com as Releases novas. A busca por dados reais nos 7
  repositórios também foi feita (só dados fictícios).
- Visual sem captura de tela: `widget.grab()` com `QT_QPA_PLATFORM=offscreen`. Em offscreen o
  diálogo de primeiro acesso do Enviador trava o script: deixe esse módulo de fora.

**Refino a fazer com o Erik (nenhum é grave)**
1. Renomeador: PDF com criptografia AES dá erro em inglês no `.exe` avulso (falta `cryptography`).
2. Renomeador: a confirmação ao fechar fala em "tarefa em andamento" com PDF só lido; `aguardar()`
   espera sem limite; caminho de destino digitado relativo ou com aspas.
3. READMEs: Renomeador (log), `Tcm-ui` (rodapé com a versão do módulo), Catraca (quem nunca editou a
   lista de usuários na 1.0.0 precisa buscá-la de novo).
4. Conferir à mão o calendário e a marcação da tabela da Catraca nos dois temas.
5. RoboAgregado: "Fechar mesmo assim" durante o envio mata a thread sem pedir parada; se cair entre
   o envio e o registro no log, aquele extrato pode ser reenviado depois (janela estreita).

**Próximo**
1. Testes manuais do Erik em 25/11: tudo o que pôde testar funcionou, inclusive a conta Microsoft
   no `EnviadorEmails.exe` novo e o CSV da Catraca igual ao da 1.0.0. **Falta só a casca fora da rede** (VPN/cabo desligados, computador
   do domínio): conferir se os grupos resolvem (o log avisa "grupo(s) do token sem nome").
2. Versões das bibliotecas de terceiros fixadas em `versoes.txt` (incluído pelos dois
   `requirements*.txt`); para atualizar, mudar lá e testar o `.exe` antes de salvar.
3. Atualização automática testada pelo Erik em 25/11 depois do lançamento: funcionou. Próximo: o
   refino acima, quando ele pedir.
4. Feito e lançado no plano 8: login Microsoft (OAuth) também no RoboAgregado, porque a
   Microsoft vai desligar o SMTP com autenticação básica: desligado por padrão no fim de 12/2026
   (o administrador ainda pode religar), data final a anunciar em 2027. Pode usar o mesmo registro de
   aplicativo da Azure do Enviador (permissão delegada `SMTP.Send`).
   Lembrete: `enviar_fretes.carregar_env` põe `SMTP_SENHA` no `os.environ` do processo
   (compartilhado com os outros módulos na casca).

**Pendências gerais**
- O grafo do graphify já foi gerado para `Sistema-Financeiro`; **não remova a seção "graphify"
  deste CLAUDE.md** (ela é a instrução de consultar o grafo). Falta o grafo do `Tcm-ui` (regra
  global do Erik para projetos novos: validar dados sensíveis, `/graphify .`,
  `graphify claude install`, `graphify hook install`). Depois de mudanças grandes aqui:
  `graphify update .`.
- Grupos `SF-Mesclador`, `SF-EnviadorPDFXML`, `SF-RenomeadorCTE`, `SF-Catraca`: já criados no AD
  (informado em 25/11).

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. When the answer is under a Markdown heading, `graphify section "<heading>"` prints that section's text, so the .md need not be opened. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
