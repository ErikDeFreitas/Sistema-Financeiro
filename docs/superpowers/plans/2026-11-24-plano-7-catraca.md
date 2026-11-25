# Plano 7 — Sistema Catraca no Sistema Financeiro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar o Sistema Catraca (`ErikDeFreitas/Projeto_Catraca`) para módulo `sistema_catraca` com o visual do `tcm-ui`, com as duas páginas "Relatório de acessos" e "Usuários" direto na barra lateral, mantendo o `SistemaCatraca.exe` avulso e o que cada usuário já salvou (IP, usuário, lista e marcações), e incluí-lo na casca.

**Architecture:** Mesmo caminho do Mesclador (plano 4): pacote `src/sistema_catraca/` com `MODULO` no entry point `sistema_financeiro.modulos`. `catraca_core.py` (protocolo ControlID, CSV, períodos) só muda de lugar. A `UserStore` vira `usuarios.ListaUsuarios` (mesmas chaves do `QSettings`), a `BackgroundJob` vira `tarefa.TarefaFundo` (mesma thread daemon, agora com cancelamento que silencia os sinais), as duas páginas são reescritas com os componentes do `tcm-ui` e o `main.py` passa a ser `rodar_avulso`. O atualizador próprio (`updater.py`, `update_ui.py`) e o design system próprio (`components.py`, `themes.py`, `icons.py`, `styles.qss`) saem. O `tcm-ui` 1.5.0 ganha o que só a Catraca usa: campo de data com calendário, caixa de marcação na tabela, ordenação por chave e ícones.

**Tech Stack:** Python 3.13, PySide6, requests, pytest + pytest-qt (offscreen), PyInstaller, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md` (seções 2, 3, 5.2, 5.3, 5.4, 5.6, 5.7, 6 passo 4, 7).

**Pré-requisito:** planos 4, 5 e 6 concluídos nos arquivos (`Tcm-ui` 1.2.0 → 1.3.0 → 1.4.0 se o plano 6 o subir, casca 1.3.0). Este plano parte desse estado. Se o plano 6 não subir o `tcm-ui`, a versão deste plano continua **1.5.0** (só pula um número) e a casca continua **1.4.0**.

## Global Constraints

- **Sem commit, push, tag ou release** até o Erik dizer "Salvar versão". Nenhum passo commita. Subagentes também não.
- Repositórios públicos: nada de admin do domínio, detalhes de rede, IPs reais, senha da catraca ou nomes/CPFs reais de colaboradores em código **novo**, testes novos ou docs. Nos testes novos só nomes fictícios ("Ana Teste", "Bruno Teste") e IPs de laboratório (`127.0.0.1:<porta>`; exemplos de texto `10.0.0.10`). Placeholder do campo IP: `"IP da catraca"` (o de hoje mostra o IP real). `catraca_core.py` vai igual, **exceto** `IP_PADRAO = ""`, `USUARIO_PADRAO = ""` e `COLABORADORES_PADRAO = ()` (decisão do Erik, ver Riscos); o protocolo com a catraca não muda.
- Repositórios em `C:\Users\erik.freitas\Projetos\` (`Tcm-ui`, `Projeto_Catraca`, `Sistema-Financeiro`).
- Versões: `tcm-ui` **1.5.0**, `sistema-catraca` **2.0.0** (hoje `version.py` = 1.0.0; o repositório não tem tags locais — conferir na aba Releases do GitHub antes da Task 4, sem mexer em nada), casca **1.4.0**. `__version__` commitado igual à tag; o workflow falha se diferente.
- Dependências: no `pyproject.toml` só faixa (`tcm-ui>=1.5.0`, `requests>=2.31,<3`); o pino `@ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.5.0` fica só no `requirements.txt`. PySide6 vem do `tcm-ui`.
- `MODULO`: id `sistema_catraca` (já está em `descoberta.ORDEM`), nome `Sistema Catraca`, ícone `porta`, grupo `SF-Catraca`, repositório `ErikDeFreitas/Projeto_Catraca`, executável `SistemaCatraca.exe` (de `SistemaCatraca.spec` `name="SistemaCatraca"` e `release.yml`), `pasta_dados` = `%LOCALAPPDATA%\SistemaCatraca` (só logs do avulso; variável `CATRACA_DADOS` para testes), páginas:
  - `Pagina("relatorio", "Relatório de acessos", "Consulte os acessos do período e salve em CSV.", "arquivo")`
  - `Pagina("usuarios", "Usuários", "Escolha quem entra no relatório.", "usuarios")`
- Dados ficam onde estão (spec 5.6): `QSettings("TCM", "SistemaCatraca")`, que é também o `MODULO.aplicacao_settings` (stem do exe). Chaves mantidas com o mesmo formato: `catraca/ip`, `catraca/usuario`, `colaboradores` (JSON de lista), `selecionados` (JSON de lista; ausente = todos marcados), `ultima_pasta`. A **senha nunca é salva** (hoje fica só no campo; continua assim, em memória da página). Tema antigo: chave `theme` (`light`/`dark`) — só o avulso migra (Task 4); na casca vale o tema da casca.
- Dentro da casca o módulo nunca chama `setStyleSheet` no `QApplication`, nem `tema.configurar`, nem `QLocale.setDefault`; cria `QSettings` só com `("TCM", "SistemaCatraca")` explícito (helper `dados.configuracoes()`).
- Rede: a consulta continua numa thread daemon (o `requests` não pode ser interrompido; timeouts e `Retry` do `catraca_core` iguais). Cancelar/fechar só **descarta** o resultado; nunca bloqueia a interface esperando a catraca.
- Testes nunca tocam rede real, a catraca, o registro do Windows (QSettings em `.ini` temporário, como `pdf-merge/tests/conftest.py`) nem AppData real. HTTP só contra a catraca simulada em `127.0.0.1` que os testes de hoje já usam, ou com `catraca_core.gerar_relatorio`/`listar_usuarios` trocados por falsos nos testes de tela.
- Testes existentes: `tests/test_catraca_core.py` continua passando trocando só o import (`from sistema_catraca import catraca_core as core`, sem `sys.path.insert`). `tests/test_updater.py` sai junto com `updater.py` (exceção explícita); o que importa dele para os usuários atuais (nomes dos arquivos da Release e formato do `.sha256`) vira `tests/test_avulso.py` na Task 4.
- Capturas de tela só por `widget.grab()` pelo Python, nunca da tela. Ninguém roda a GUI interativa nem fala com a catraca real; a conferência com a catraca de verdade é do Erik (Task 4 Step 3).

## Review Focus

1. **Catraca desligada / fora da rede / timeout**: com retry, o erro leva até ~1 min; a página mostra o progresso, "Cancelar" devolve a tela na hora, e a falha vira `Modal.informar(..., tom="perigo")` com a mensagem do `catraca_core` ("Não foi possível falar com a catraca em ..."), sem travar nem deixar botões desabilitados. Testes em `test_tela_relatorio.py` e `test_tarefa.py`.
2. **Configuração salva depois de atualizar para a 2.0.0**: IP, usuário, lista de usuários, marcações e última pasta aparecem iguais no avulso e na casca (mesmo `QSettings`, mesmas chaves, mesmo JSON); "sem marcação salva = todos marcados" continua. Testes em `test_usuarios.py` e `test_tela_relatorio.py` gravando as chaves no formato da 1.0.0.
3. **Fechar (casca ou avulso) durante a consulta**: `pode_fechar` falso → a `JanelaPrincipal` pergunta; ao confirmar, `aboutToQuit` → `cancelar()` nas duas páginas: o processo sai sem esperar o `requests` e a thread daemon não emite sinal nenhum depois disso (nada de "Internal C++ object already deleted" ou access violation). Teste em `test_instancia.py`.
4. **Usuário do `SistemaCatraca.exe` 1.0.0 recebe a 2.0.0**: o atualizador antigo exige os assets `SistemaCatraca.exe` + `SistemaCatraca.exe.sha256` com URL em `https://github.com/ErikDeFreitas/Projeto_Catraca/releases/download/`, lê o hash com `^([0-9a-fA-F]{64})(?:\s|$)` e deixa `SistemaCatraca.exe.old` (que o `tcm-ui` apaga desde a onda final do plano 4). Testes na Task 4.
5. **Filtro de datas**: atalhos (quinzena atual/anterior, mês atual/anterior, últimos 15 dias) preenchem os dois `CampoData`; data final antes da inicial é recusada antes de conectar; calendário em português e legível no tema escuro; o nome sugerido do CSV continua `Relatório 2° Quinzena Outubro.csv`. Testes em `test_campo_data` (tcm-ui) e `test_tela_relatorio.py`.

---

### Task 1: tcm-ui 1.5.0 — `CampoData`, marcação e ordenação na `Tabela`, ícones

**Files (em `C:\Users\erik.freitas\Projetos\Tcm-ui`):** Modify `src/tcm_ui/components.py`, `src/tcm_ui/styles.qss`, `src/tcm_ui/icons.py`, `src/tcm_ui/__init__.py`, `pyproject.toml`, `README.md`, `src/tcm_ui/demo.py`; Create `tests/test_catraca_extras.py`.

Levantamento (o resto já existe): `Card`→`Cartao`, `FormField`→`Campo` (`set_helper`/`set_invalid` → `definir_erro`), `TextInput`→`CampoTexto`, `PasswordInput`→`CampoSenha`, `SearchInput`→`CampoPesquisa`, `ComboBox`→`Selecao`, `ProgressBar.set_busy(True)`→`BarraProgresso.setRange(0, 0)`, `StatCard`→`CartaoIndicador`, `ResponsiveRow`→`GradeResponsiva`, `EmptyState`→`EstadoVazio`, `DataTable` + `BADGE_TONE_ROLE`→`Tabela` + `Etiqueta` na célula, `Modal.ask`→`Modal.escolher/confirmar(texto_cancelar=)/informar`, `text_label`→`Texto`; `Sidebar`/`Header`/`ThemeFade` são da `JanelaPrincipal`. Ícones já existentes: `usuarios`, `arquivo`, `check`, `fechar`, `camadas`, `pasta`. Faltam:

**Interfaces — Produces:**
- `CampoData(QDateEdit)`: calendário em popup, formato `dd/MM/yyyy`, `setLocale(QLocale(Portuguese, Brazil))` no próprio widget (o módulo não pode mexer no `QLocale` global), altura `TAMANHOS["campo"]`, fim de semana na cor normal, cursor de mão; `valor() -> date`, `definir_valor(d: date) -> None`. Porta de `..\Projeto_Catraca\components.py:DateInput`.
- QSS (dois temas): `QDateEdit` igual a `QLineEdit`/`QComboBox` (borda, foco, desabilitado, `::drop-down`/`::down-arrow`), `QCalendarWidget` (barra de navegação, `QToolButton` mês/ano, setas, `QAbstractItemView` com seleção `@primaria`), `QTableWidget::indicator` (mesmo visual do `QCheckBox::indicator`, com `@icone_check`). Base: `..\Projeto_Catraca\styles.qss` linhas 184–240, 264–315, 364–380, trocando os tokens pelos do `tcm-ui`.
- `Tabela.definir_celula(linha, coluna, valor, ordem=None)`: com `ordem` (número, data ISO ou texto) a célula ordena por essa chave e não pelo texto (item `ItemOrdenavel(QTableWidgetItem)` com `__lt__` pela chave em `Qt.UserRole + 2`); vale também para célula com widget (ex.: `Etiqueta`). Sem `ordem`, comportamento de hoje.
- Ícones (mesmo traço; SVGs de `..\Projeto_Catraca\icons.py`): `porta` (door-open), `baixar` (download), `mais` (plus), `lixeira` (trash), `usuario_check`, `usuario_x`, `calendario`, `seta_esquerda`, `seta_direita` (setas do calendário). Se o plano 6 já tiver criado algum, reaproveitar e não duplicar.
- `__version__ = "1.5.0"` (e `version` no `pyproject.toml`). Demo: cartão com dois `CampoData`, tabela com marcação e coluna ordenável, ícones novos.

- [ ] Step 1: testes que falham — `test_campo_data_valor_e_locale` (`definir_valor(date(2026, 10, 16))` → `valor()` igual; `displayFormat() == "dd/MM/yyyy"`; `locale().language() == Portuguese`; o `QLocale()` global não muda), `test_qss_tem_calendario_e_indicador_da_tabela` (QSS gerado nos dois temas contém `QCalendarWidget`, `QDateEdit` e `QTableWidget::indicator`), `test_tabela_ordena_pela_chave` (valores `"10"`, `"9"`, `"–"` com `ordem` 10, 9, -1 → ordem crescente `–, 9, 10`; idem coluna com `Etiqueta`), `test_icones_catraca_renderizam` (pixmap não nulo para cada nome novo, nos dois temas).
- [ ] Step 2: rodar e ver falhar; Step 3: implementar; Step 4: suíte inteira passa.
- [ ] Step 5: não commitar.

---

### Task 2: pacote `sistema_catraca` — núcleo, dados, lista de usuários e testes existentes

**Files (em `C:\Users\erik.freitas\Projetos\Projeto_Catraca`):**
- Move (git mv, sem editar): `catraca_core.py` → `src/sistema_catraca/catraca_core.py`; `assets/app.ico` fica onde está.
- Create: `pyproject.toml`, `src/sistema_catraca/__init__.py`, `src/sistema_catraca/dados.py`, `src/sistema_catraca/usuarios.py`, `tests/conftest.py`, `tests/test_dados.py`, `tests/test_usuarios.py`.
- Modify: `tests/test_catraca_core.py` (só o import; tira o `sys.path.insert`).
- Delete: `version.py`, `updater.py`, `update_ui.py`, `tests/test_updater.py`, `requirements.txt` (recriado na Task 4). (`main.py`, `build.py` e o design system antigo quebram até a Task 4 — aceitável, igual aos planos 2 e 4.)

**Interfaces — Produces:**
- `sistema_catraca.__version__ = "2.0.0"`.
- `dados.NOME_APLICACAO = "SistemaCatraca"`; `dados.pasta_dados() -> Path` (`CATRACA_DADOS` ou `%LOCALAPPDATA%\SistemaCatraca`); `dados.PASTA: Path`; `dados.configuracoes() -> QSettings` = `QSettings("TCM", "SistemaCatraca")` (import de `QtCore` só dentro da função, para o `modulo.py` continuar leve). Nada criado no import.
- `usuarios.ListaUsuarios(QObject)` — porta fiel de `main.py:UserStore` (sinais `mudou`, `marcacao_mudou`; propriedades `nomes`, `marcados`; `esta_marcado`, `marcar(nomes, marcado)`, `adicionar(nome)` (entra marcado; `ValueError` com a mensagem do `catraca_core`), `remover(nome)`, `mesclar(encontrados) -> list[str]` (novos entram desmarcados)). Mesmas chaves `colaboradores`/`selecionados`, mesmo `json.dumps(..., ensure_ascii=False)`, só grava depois da primeira alteração, lista vazia/inválida no `QSettings` → `catraca_core.COLABORADORES_PADRAO`. Recebe `configuracoes: QSettings | None = None` (padrão `dados.configuracoes()`).
- `pyproject.toml` no modelo do `pdf-merge`: `name = "sistema-catraca"`, versão dinâmica (`sistema_catraca.__version__`), `dependencies = ["tcm-ui>=1.5.0", "requests>=2.31,<3"]`, extra `dev = ["pytest", "pytest-qt"]`, entry point `sistema_catraca = "sistema_catraca.modulo:MODULO"` (o `modulo.py` chega na Task 3), `testpaths = ["tests"]`, `package-data` não é preciso (sem `.qss` próprio).
- `tests/conftest.py` no modelo do `pdf-merge`: antes de qualquer import do pacote, `QT_QPA_PLATFORM=offscreen` e `CATRACA_DADOS` = pasta temporária; troca de `QtCore.QSettings` por `.ini` em pasta temporária; fixture `configuracoes` que limpa o `.ini` de `("TCM", "SistemaCatraca")` a cada teste.

- [ ] Step 1: testes que falham — `test_dados.py`: `test_catraca_dados_substitui_a_pasta`, `test_sem_variavel_usa_localappdata`, `test_importar_nao_cria_pasta`, `test_configuracoes_usa_tcm_sistemacatraca` (`organizationName()`/`applicationName()`). `test_usuarios.py` (valores gravados como a 1.0.0 grava, nomes fictícios): `test_sem_nada_salvo_usa_padrao_e_todos_marcados`, `test_le_lista_e_marcacao_da_versao_1`, `test_json_invalido_cai_no_padrao`, `test_adicionar_entra_marcado_e_recusa_repetido`, `test_mesclar_novos_entram_desmarcados`, `test_remover_tira_da_marcacao`, `test_grava_no_mesmo_formato` (relê o `.ini` com `json.loads` → lista igual; acento preservado).
- [ ] Step 2: rodar e ver falhar; Step 3: mover, criar, `pip install -e ..\Tcm-ui -e .[dev]` num `.venv` do repositório; Step 4: passar (os testes de `test_catraca_core.py` de hoje + novos). Conferir com `git diff --no-index` (ou hash) que `catraca_core.py` não mudou nenhum byte.
- [ ] Step 5: não commitar.

---

### Task 3: as duas páginas, a instância e o `MODULO`

**Files:** Create `src/sistema_catraca/tarefa.py`, `src/sistema_catraca/tela_relatorio.py`, `src/sistema_catraca/tela_usuarios.py`, `src/sistema_catraca/instancia.py`, `src/sistema_catraca/modulo.py`, `tests/test_tarefa.py`, `tests/test_tela_relatorio.py`, `tests/test_tela_usuarios.py`, `tests/test_instancia.py`, `tests/test_modulo.py`.

**Interfaces:**
- Consumes: Task 1 (`CampoData`, `Tabela.definir_celula(..., ordem=)`, indicador da tabela, ícones), `tcm_ui.components` (`Pagina`, `Cartao`, `Campo`, `CampoTexto`, `CampoSenha`, `CampoPesquisa`, `Selecao`, `Botao`, `BarraProgresso`, `CartaoIndicador`, `GradeResponsiva`, `EstadoVazio`, `Tabela`, `Etiqueta`, `Modal`, `Texto`), `tcm_ui.modulo`, Task 2.
- Produces:
  - `tarefa.TarefaFundo(QObject)`: porta de `BackgroundJob` (`progresso(int, str)`, `sucesso(int, object)`, `falha(int, str)`; `CatracaError` → mensagem pronta; outra exceção → `"Erro inesperado: ..."`; `threading.Thread(daemon=True)`), mais `cancelar()` (um `threading.Event`): depois dele a thread não emite nada. Os sinais ligam com `QueuedConnection`.
  - `tela_relatorio.TelaRelatorio(contexto, lista)` (subclasse de `Pagina`) — mesma tela de `main.py:ReportPage`: cartão "Conexão com a catraca" (subtítulo "A senha não é salva: digite-a a cada abertura do programa."; `campo_ip`, `campo_usuario`, `campo_senha` (`CampoSenha`, Enter gera)), cartão "Período do relatório" (`data_inicial`, `data_final` = `CampoData`; `botoes_periodo` com os 5 atalhos do `catraca_core`; abre na quinzena atual), linha de ação (`botao_gerar` primário ícone `arquivo`, `rotulo_marcados` "X de N usuários marcados... Altere na página Usuários.", `rotulo_progresso`, `progresso` indeterminado, `botao_cancelar`), 4 `CartaoIndicador` (Registros `camadas` primaria, Colaboradores `usuarios` neutro, Com registro `usuario_check` sucesso, Sem registro `usuario_x` perigo), cartão de resultado (`pesquisa` com espera de 150 ms + `Tabela.filtrar`, `selecao_visao` "Por colaborador"/"Todos os acessos", `botao_salvar` ícone `baixar`, `rotulo_resumo`, `EstadoVazio`, `tabela_resumo` com Situação = `Etiqueta` sucesso/perigo e colunas ordenáveis por `ordem=`, `tabela_acessos` só com texto — pode ter milhares de linhas: `setUpdatesEnabled(False)` ao preencher e larguras medidas uma vez). Clique numa linha do resumo com registros → pesquisa pelo nome + visão "Todos os acessos". Públicos: `rodando`, `relatorio`, `conexao() -> (ip, usuario, senha)`, `lembrar_conexao(ip, usuario, senha)` (grava só `catraca/ip` e `catraca/usuario`), `gerar()`, `cancelar()`, `salvar_csv()`; `limpar_host` igual ao `clean_host` de hoje. Validações e textos de hoje: campo vazio → `Campo.definir_erro` + foco; data final < inicial → `Modal.informar("Período inválido", ..., "perigo")` sem conectar; nenhum marcado → `Modal.informar("Nenhum usuário marcado", ...)`. Salvar: `QFileDialog.getSaveFileName(contexto.janela, ...)` em `ultima_pasta` + `catraca_core.nome_sugerido`, acrescenta `.csv`, `catraca_core.salvar_csv`, grava `ultima_pasta`, `Modal.escolher` "Relatório salvo" com "Fechar"/"Abrir pasta".
  - `tela_usuarios.TelaUsuarios(contexto, lista, relatorio: TelaRelatorio)` — mesma tela de `main.py:UsersPage`: cartão "Adicionar usuários" (`botao_buscar` "Buscar na catraca" ícone `baixar` + progresso; `campo_nome` + `botao_adicionar` ícone `mais`, erro no `Campo`), cartão da lista (`rotulo_contagem`, `pesquisa`, `botao_marcar_todos`, `botao_desmarcar_todos`, `botao_remover` perigo ícone `lixeira`, texto de ajuda, `tabela` com uma coluna "Usuário" e caixa de marcação; clique na linha ou Espaço alterna). Buscar sem IP/usuário → `Modal.informar("Conexão incompleta", ...)`; sem senha → `pedir_senha(host, usuario) -> str` (`Modal` com `Campo("Senha", CampoSenha)`, "Cancelar"/"Buscar"); sucesso → `lista.mesclar` + `Modal.informar` com o mesmo resumo de hoje (`MAX_NOMES_NA_MENSAGEM = 8`); remover → `Modal.confirmar(..., texto_ok="Remover", destrutivo=True)`. Públicos: `rodando`, `cancelar()`.
  - `instancia.Catraca(contexto)`: cria `ListaUsuarios` e a `TelaRelatorio` na primeira chamada de `widget` (qualquer página, porque Usuários usa a conexão do Relatório); `widget("relatorio")`/`widget("usuarios")` criam uma vez cada; outra chave → `KeyError`; `acoes_cabecalho` → `[]` nas duas (como hoje: as ações ficam nos cartões); `pode_fechar` → nenhuma das duas `rodando` (relatório na tela sem salvar não bloqueia, como hoje). Liga `QApplication.aboutToQuit` → `cancelar()` nas duas páginas (sem esperar a rede).
  - `modulo.MODULO` com os valores dos Global Constraints, `pasta_dados=dados.PASTA`, importando a instância só dentro de `criar`.
- Diálogos de arquivo e `Modal` sempre com `contexto.janela` como pai.

- [ ] Step 1: testes que falham —
  - `test_modulo.py`: valores do `MODULO` (duas páginas, chaves/ícones, `nome_exe == "SistemaCatraca.exe"`, `aplicacao_settings == "SistemaCatraca"`, `grupo_ad == "SF-Catraca"`), entry point carrega, `import sistema_catraca.modulo` num subprocesso não importa `requests` nem `sistema_catraca.catraca_core`.
  - `test_tarefa.py`: sucesso/`CatracaError`/exceção qualquer chegam pelos sinais certos; tarefa presa num `threading.Event` + `cancelar()` + liberar → nenhum sinal emitido.
  - `test_tela_relatorio.py` (`catraca_core.gerar_relatorio` trocado por falso; `Modal.informar`/`escolher` e `QFileDialog.getSaveFileName` trocados por falsos): lê `catraca/ip`/`catraca/usuario` gravados antes; senha vazia → erro no campo e nada chamado; data final < inicial → modal e nada chamado; atalho "Mês anterior" preenche as datas; sucesso preenche indicadores, resumo (Etiqueta "Sem registro" para quem não tem acesso) e acessos, e grava IP/usuário mas não a senha; falha "Não foi possível falar com a catraca" → modal perigo e botões de volta; `cancelar()` no meio → tela livre na hora e o resultado tardio é ignorado; salvar grava o CSV em `tmp_path` com o nome sugerido e `ultima_pasta`; ordenação do resumo por "Registros" é numérica.
  - `test_tela_usuarios.py` (`listar_usuarios` falso): marcar/desmarcar pela linha e por Espaço; marcar todos com pesquisa ativa vale só para os visíveis; adicionar repetido → erro no campo; buscar sem senha abre `pedir_senha` (falso) e cancelar não busca; sucesso mescla novos desmarcados e o resumo lista quem não existe na catraca.
  - `test_instancia.py`: widgets únicos por página, `KeyError`, Usuários antes de Relatório funciona, `acoes_cabecalho == []`, `pode_fechar` falso durante consulta (falso preso num `Event`) e verdadeiro depois, `aboutToQuit` emitido → as duas páginas canceladas, nenhum sinal depois e o teste termina sem esperar a "rede".
- [ ] Step 2: falhar; Step 3: implementar; Step 4: suíte inteira passa (rodar 5× seguidas para pegar instabilidade de thread).
- [ ] Step 5: não commitar.

---

### Task 4: `.exe` avulso, build e Release da Catraca

**Files:** Modify `main.py` (reescrito), `README.md`, `.gitignore` (`*.egg-info/`, `build/`, `dist/`, `.venv/` — manter `*.csv` e `.env`), `.github/workflows/release.yml`; Create `build.ps1`, `requirements.txt`, `tests/test_avulso.py`; Delete `components.py`, `icons.py`, `themes.py`, `styles.qss`, `build.py`, `SistemaCatraca.spec`; mantém `assets/app.ico`.

**Interfaces — Produces:** `main.migrar_tema(config: QSettings) -> None` (se `aparencia/tema` não existe e `theme` é `"light"`/`"dark"`, grava `"claro"`/`"escuro"` em `aparencia/tema`; não apaga `theme`); `main()` = `migrar_tema(dados.configuracoes())` → `sys.exit(rodar_avulso(MODULO))`. A limpeza do `SistemaCatraca.exe.old` é do `tcm-ui` (onda final do plano 4); não duplicar aqui.

- `requirements.txt`: `tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.5.0`.
- `build.ps1` no modelo do `Send_Agregados\build.ps1` (`-Python`): `$nome = "SistemaCatraca"`, `--icon assets\app.ico`, `--collect-data tcm_ui --collect-data sistema_catraca`, os `--exclude-module` do `.spec` atual (`tkinter`, `numpy`, `PIL`, `matplotlib`, `pandas`, `pytest`, `PySide6.QtWebEngineCore`, `PySide6.QtWebEngineWidgets`, `PySide6.QtQml`, `PySide6.QtQuick`, `PySide6.QtPdf`, `PySide6.QtMultimedia`, `PySide6.QtNetwork`), `dist\SistemaCatraca.exe.sha256` = `"<hash>  SistemaCatraca.exe\n"` (ASCII, LF); versão lida de `src\sistema_catraca\__init__.py`. (O corte de binários Qt do `.spec` pode ficar de fora, como no Mesclador.)
- `release.yml` no modelo do `pdf-merge` (plano 4): instala `-r requirements.txt . pytest pytest-qt pyinstaller`; confere tag = `sistema_catraca.__version__`; `python -m pytest -q` offscreen; `./build.ps1 -Python python`; publica `dist/SistemaCatraca.exe` + `dist/SistemaCatraca.exe.sha256` (mesmos nomes de hoje).
- README: o que faz, uso (as duas páginas, senha nunca salva, onde ficam as configurações — sem IP nem nomes reais), desenvolver (`.venv` + `..\Tcm-ui` editável ou `-r requirements.txt`; `python -m pytest`), lançar versão, módulo da casca (grupo `SF-Catraca`).
- [ ] Step 1: testes que falham — `test_build_usa_nome_do_exe` (`build.ps1`, `release.yml` e `MODULO.nome_exe` usam `SistemaCatraca.exe`), `test_sha256_legivel_pelos_dois_atualizadores` (conteúdo no formato acima casa com a regex antiga `^([0-9a-fA-F]{64})(?:\s|$)` — copiada no teste como constante — e com a do `tcm_ui.atualizador`, dando o mesmo hash), `test_release_aceita_pelo_atualizador_1_0_0` (payload falso com `tag_name "v2.0.0"` e os dois assets em `https://github.com/ErikDeFreitas/Projeto_Catraca/releases/download/v2.0.0/...` passa pelas regras do `parse_release` antigo copiadas no teste: mais nova que `1.0.0`, os dois nomes, o prefixo), `test_migrar_tema` (QSettings `.ini`: `dark`→`escuro`, `light`→`claro`, `aparencia/tema` existente fica), `test_workflow_confere_versao` (texto do `release.yml` contém `sistema_catraca.__version__` e os dois nomes de asset).
- [ ] Step 2: `powershell -File build.ps1` (venv do repositório com `..\Tcm-ui` editável) gera `dist\SistemaCatraca.exe`; rodar com `CATRACA_DADOS` temporário e `QT_QPA_PLATFORM=offscreen` por alguns segundos e fechar (sem erro no log; sem tocar a catraca). O controlador confere as duas páginas por `grab()` nos dois temas, incluindo o calendário aberto.
- [ ] Step 3: conferência manual do Erik (não automatizável): abrir o `.exe` novo **sem** `CATRACA_DADOS` e ver IP, usuário, lista e marcações de antes; gerar um relatório real de uma quinzena e comparar o CSV com um gerado pela 1.0.0 (deve ser idêntico byte a byte); "Buscar na catraca"; desligar o cabo/VPN e ver a mensagem de catraca inacessível.
- [ ] Step 4: não commitar.

---

### Task 5: casca 1.4.0 com a Catraca

**Files (em `C:\Users\erik.freitas\Projetos\Sistema-Financeiro`):** Modify `requirements.txt`, `requirements-local.txt`, `build.ps1` (comentário do `-Local`), `pyproject.toml`, `src/sistema_financeiro/__init__.py`, `README.md`, `CLAUDE.md`; tests (`test_args_pyinstaller.py`, `test_descoberta.py`, `test_app.py`).

- `requirements.txt`: `tcm-ui@v1.5.0`, os pinos dos planos 4–6 (robo-agregado, mesclador, enviador-pdf-xml, o do Renomeador como o plano 6 deixar), `sistema-catraca @ git+https://github.com/ErikDeFreitas/Projeto_Catraca@v2.0.0`. `pyproject.toml`: `tcm-ui>=1.5.0`. `__version__ = "1.4.0"`.
- `requirements-local.txt`: acrescentar `../Projeto_Catraca`.
- `descoberta.ORDEM` já tem `sistema_catraca` no fim (nada a mudar).
- Testes: `verificar_modulos()` com os cinco módulos instalados → 0; ordem na barra termina em "Sistema Catraca" com os itens "Relatório de acessos" e "Usuários" sob o título da seção (sem abas internas, spec 5.3); `test_args_pyinstaller_inclui_catraca` (`--collect-all sistema_catraca` e `--copy-metadata sistema-catraca`; `requests` entra no `.exe`); com `SF_GRUPOS_DEV="SF-Catraca"` só a Catraca aparece e abre em "Relatório de acessos".
- [ ] Step 1: venv da casca com os repositórios locais editáveis; suíte passa.
- [ ] Step 2: `powershell -File build.ps1 -Local` → `dist\SistemaFinanceiro.exe`, `--verificar` OK com os cinco módulos. O controlador confere a janela por `grab()` com `SF_GRUPOS_DEV`, tema escuro nas duas páginas da Catraca.
- [ ] Step 3: README (grupo `SF-Catraca`), `CLAUDE.md` ("Onde paramos"; ordem do "Salvar versão": Tcm-ui v1.5.0 → Projeto_Catraca v2.0.0 → Sistema-Financeiro v1.4.0, depois das tags dos planos 4–6; a TI cria `SF-Catraca`; a tag v2.0.0 chega a todos os usuários do avulso, então só depois da Task 4 Step 3).
- [ ] Step 4: não commitar.

---

## Riscos e perguntas para o Erik

- **Decidido pelo Erik (24/11/2026):** tirar do código os valores reais. `IP_PADRAO = ""`, `USUARIO_PADRAO = ""`, `COLABORADORES_PADRAO = ()`; na primeira vez (sem IP salvo) a pessoa preenche a conexão e fica salvo no `QSettings` como hoje; a lista inicial vem da "Buscar na catraca". `tests/test_catraca_core.py` troca o nome real por fictício. Quem já usa a 1.0.0 não percebe (os valores já estão salvos no `QSettings`). O histórico do git continua com os valores antigos.
- Não há tag local em `Projeto_Catraca`, e o README diz que ainda não havia Release: se a 1.0.0 nunca foi publicada, quem usa o `.exe` 1.0.0 recebeu por cópia e só atualiza sozinho a partir da v2.0.0. Conferir a aba Releases antes do "Salvar versão".
- Fechar durante a consulta não espera a catraca (até ~5 min no relatório): o processo sai e a consulta é abandonada, como hoje. Dentro da casca isso agora pede confirmação.
