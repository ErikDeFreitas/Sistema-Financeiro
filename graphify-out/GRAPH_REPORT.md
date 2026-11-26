# Graph Report - Sistema-Financeiro  (2026-11-26)

## Corpus Check
- 19 files · ~10,326 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 3)

## Summary
- 241 nodes · 367 edges · 14 communities (10 shown, 4 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 48 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b4b38bc3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Janela e Execução da Casca
- Utilitários e Args PyInstaller
- Planos e Arquitetura
- Acesso por Grupos AD
- Workflow de Release
- Fixtures de Testes
- Descoberta de Módulos
- Testes de Args PyInstaller
- Controle de Acesso (Spec)
- Estado e Regras do Projeto
- Pacote Raiz
- Login Microsoft padronizado (Enviador + RoboAgregado)

## God Nodes (most connected - your core abstractions)
1. `carregar_modulos()` - 20 edges
2. `criar_janela()` - 17 edges
3. `verificar_modulos()` - 14 edges
4. `permitidos()` - 13 edges
5. `Login Microsoft padronizado (Enviador + RoboAgregado)` - 10 edges
6. `Casca (Sistema-Financeiro)` - 9 edges
7. `Contrato de modulo (Modulo, Pagina, InstanciaModulo, Contexto)` - 9 edges
8. `tcm-ui (design system unico)` - 9 edges
9. `_linhas()` - 8 edges
10. `rodar()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Workflow Release (tag vX.Y.Z = __version__)` --semantically_similar_to--> `Build e release (PyInstaller, tag = __version__)`  [INFERRED] [semantically similar]
  README.md → docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md
- `test_ultima_pagina_de_sistema_perdido_abre_a_primeira_permitida()` --calls--> `criar_janela()`  [INFERRED]
  tests/test_app.py → src/sistema_financeiro/app.py
- `test_robo_agregado_abre_na_casca()` --calls--> `criar_janela()`  [INFERRED]
  tests/test_app.py → src/sistema_financeiro/app.py
- `test_so_o_grupo_do_enviador_mostra_so_o_enviador()` --calls--> `carregar_modulos()`  [INFERRED]
  tests/test_app.py → src/sistema_financeiro/descoberta.py
- `test_grupo_do_renomeador_mostra_os_dois_renomeadores()` --calls--> `carregar_modulos()`  [INFERRED]
  tests/test_app.py → src/sistema_financeiro/descoberta.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Sistemas do financeiro que implementam o contrato de modulo** — docs_superpowers_specs_2026_11_19_sistema_financeiro_design_robo_agregado, docs_superpowers_specs_2026_11_19_sistema_financeiro_design_mesclador, docs_superpowers_specs_2026_11_19_sistema_financeiro_design_enviador_pdf_xml, docs_superpowers_specs_2026_11_19_sistema_financeiro_design_renomeador_cte, docs_superpowers_specs_2026_11_19_sistema_financeiro_design_catraca [EXTRACTED 1.00]
- **Fluxo de versoes: requirements, build.ps1 e release workflow** — requirements, readme_build_ps1, readme_release_workflow, claude_ordem_salvar_versao [INFERRED 0.85]

## Communities (14 total, 4 thin omitted)

### Community 0 - "Janela e Execução da Casca"
Cohesion: 0.08
Nodes (28): permitidos(), criar_janela(), pasta_dados(), rodar(), verificar_modulos(), test_admin_ve_todos_na_ordem(), _Instancia, test_abrir_o_enviador_na_casca_nao_tenta_rede_externa() (+20 more)

### Community 1 - "Utilitários e Args PyInstaller"
Cohesion: 0.09
Nodes (5): _normalizar(), usuario_windows(), _importacoes_faltando(), test_usuario_windows_com_dominio(), test_usuario_windows_sem_dominio()

### Community 2 - "Planos e Arquitetura"
Cohesion: 0.09
Nodes (27): Plano 1 - Tcm-ui v1.0.0, Plano 2 - RoboAgregado 2.0.0 / Tcm-ui 1.1.0, Plano 3 - casca 1.0.0, Plano 4 - Mesclador (casca 1.1.0, nao salvo), Plano 5 - Enviador PDF + XML (casca 1.2.0, nao salvo), Proximos: planos 6-7 (Renomeador, Catraca) e teste fora da rede, Arquitetura proposta: modulos por entry points do pip, Colisao de nomes de modulo entre projetos (+19 more)

### Community 3 - "Acesso por Grupos AD"
Cohesion: 0.12
Nodes (15): grupos_do_token(), grupos_do_usuario(), _ErroWin, _falsificar_win32(), procurar(), test_dev_ignorado_quando_congelado(), test_dev_substitui_token_quando_nao_congelado(), test_falha_na_leitura_do_token_vira_conjunto_vazio() (+7 more)

### Community 4 - "Workflow de Release"
Cohesion: 0.07
Nodes (26): runs-on, steps, QT_QPA_PLATFORM, TAG, jobs, build, name, on (+18 more)

### Community 5 - "Fixtures de Testes"
Cohesion: 0.11
Nodes (11): configuracoes(), _conta_microsoft_sem_rede(), criar_modulo_falso(), modulos_abc(), _qsettings_fora_do_registro(), _QSettingsIni, _sem_grupos_dev(), tentativas_de_rede() (+3 more)

### Community 6 - "Descoberta de Módulos"
Cohesion: 0.20
Nodes (9): carregar_modulos(), test_robo_agregado_abre_na_casca(), _Ponto, test_id_repetido_fica_o_primeiro(), test_modulo_que_nao_importa_nao_derruba_os_outros(), test_objeto_que_nao_e_modulo_e_ignorado(), test_ordem_fixa_e_desconhecidos_por_id_no_fim(), test_robo_agregado_instalado_pelo_entry_point() (+1 more)

### Community 7 - "Testes de Args PyInstaller"
Cohesion: 0.36
Nodes (8): _linhas(), _tem_par(), test_args_pyinstaller_inclui_catraca(), test_args_pyinstaller_inclui_enviador(), test_args_pyinstaller_inclui_renomeador(), test_inclui_dados_do_tcm_ui(), test_inclui_pacote_e_metadados_do_mesclador(), test_inclui_pacote_e_metadados_do_robo_agregado()

### Community 9 - "Estado e Regras do Projeto"
Cohesion: 0.40
Nodes (4): CLAUDE.md - estado do projeto, Ordem do Salvar versao (Tcm-ui, Send_Agregados, pdf-merge, pdf-xml-mailer, casca), Sistema Financeiro - ideias e analise inicial, Sistema Financeiro - design (spec)

### Community 12 - "Login Microsoft padronizado (Enviador + RoboAgregado)"
Cohesion: 0.12
Nodes (15): Abordagens consideradas, Casca `Sistema-Financeiro` 1.5.0, Decisões minhas (para o Erik conferir), Desenho, Fica com quem implementar, Fora do escopo, Login Microsoft padronizado (Enviador + RoboAgregado), Não pode acontecer (+7 more)

## Knowledge Gaps
- **15 isolated node(s):** `sistema-financeiro`, `Plano 1 - Tcm-ui v1.0.0`, `Plano 2 - RoboAgregado 2.0.0 / Tcm-ui 1.1.0`, `Plano 3 - casca 1.0.0`, `Plano 4 - Mesclador (casca 1.1.0, nao salvo)` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 107 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `carregar_modulos()` connect `Descoberta de Módulos` to `Janela e Execução da Casca`, `Utilitários e Args PyInstaller`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `carregar_modulos()` (e.g. with `chave()` and `test_abrir_o_enviador_na_casca_nao_tenta_rede_externa()`) actually correct?**
  _`carregar_modulos()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sistema-financeiro`, `Plano 1 - Tcm-ui v1.0.0`, `Plano 2 - RoboAgregado 2.0.0 / Tcm-ui 1.1.0` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Janela e Execução da Casca` be split into smaller, more focused modules?**
  _Cohesion score 0.07505285412262157 - nodes in this community are weakly interconnected._
- **Why does `criar_janela()` connect `Janela e Execução da Casca` to `Utilitários e Args PyInstaller`, `Descoberta de Módulos`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `criar_janela()` (e.g. with `test_abrir_o_enviador_na_casca_nao_tenta_rede_externa()` and `test_barra_da_catraca_tem_secao_e_dois_itens_sem_abas_internas()`) actually correct?**
  _`criar_janela()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `Utilitários e Args PyInstaller` be split into smaller, more focused modules?**
  _Cohesion score 0.08669354838709678 - nodes in this community are weakly interconnected._