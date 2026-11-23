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

## Onde paramos (23/11/2026)

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
  vizinhos; pode sair agora que as tags existem), `requirements*.txt`,
  `.github/workflows/release.yml`, `README.md`. 35 testes. Ledger:
  `.superpowers/sdd/2026-11-23-plano-3-casca/`.
- Salvo em 23/11/2026, com tags e Releases: `Tcm-ui` `v1.1.0`, `Send_Agregados` `v2.0.0`
  (Release automática para os usuários do RoboAgregado), `Sistema-Financeiro` `v1.0.0` (Release
  do `SistemaFinanceiro.exe`). Grupo `SF-Admin` já existe no AD.

**Próximo**
1. Conferir no GitHub (aba Actions) que as Releases `v2.0.0` do Send_Agregados e `v1.0.0` desta
   casca foram geradas com o `.exe` e o `.sha256`.
2. Erik testa o envio real com o RoboAgregado 2.0.0 e a casca com o grupo `SF-Admin` (depois de
   sair e entrar no Windows).
3. Teste manual da casca fora da rede (VPN/cabo desligados) num computador do domínio, antes de
   distribuir: conferir se os grupos resolvem (o log avisa "grupo(s) do token sem nome").
4. Planos 4–7: Mesclador, Enviador PDF+XML, Renomeador de CT-e, Catraca, um por vez.
   Levar em conta: `enviar_fretes.carregar_env` põe `SMTP_SENHA` no `os.environ` do processo
   (compartilhado com os outros módulos na casca).

**Pendências gerais**
- Gerar o grafo do graphify para `Sistema-Financeiro` e `Tcm-ui` (regra global do Erik para
  projetos novos: validar dados sensíveis, `/graphify .`, `graphify claude install`,
  `graphify hook install`).
- Grupos `SF-Mesclador`, `SF-EnviadorPDFXML`, `SF-RenomeadorCTE`, `SF-Catraca`: a TI cria quando
  cada sistema entrar na casca.
