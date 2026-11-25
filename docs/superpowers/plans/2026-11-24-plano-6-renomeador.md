# Plano 6 — Renomeador de CT-e no Sistema Financeiro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar o Renomeador de CT-e (`ErikDeFreitas/Renomeador_CTE`) para módulo `renomeador_cte` com o visual do `tcm-ui`, mantendo o `RenomeadorCTE.exe` avulso (os usuários da 1.0.0 atualizam sozinhos), e incluí-lo na casca.

**Architecture:** Mesmo caminho do Mesclador (plano 4): pacote `src/renomeador_cte/` com `MODULO` no entry point `sistema_financeiro.modulos`; `cte_engine.py` só muda de lugar; a página "Separar e renomear" é reescrita com os componentes do `tcm-ui`; a página "Design System" sai (spec §6 item 5: a vitrine é o `python -m tcm_ui.demo`); o design system próprio (`components.py`, `icons.py`, `themes.py`, `styles.qss`) e o atualizador próprio (`updater.py`, `UpdateController`, `UpdateDialog`) saem e entram `tcm_ui` + `tcm_ui.atualizador`; `main.py` → `rodar_avulso`. O `tcm-ui` 1.4.0 ganha só o que falta (zona de arrastar arquivo, dica mutável no `Campo`, tabela ordenável por chave, 2 ícones).

**Tech Stack:** Python 3.13, PySide6, pypdf, pytest + pytest-qt (offscreen), PyInstaller, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md` (seções 2, 5.2, 5.4, 5.6, 5.7, 6 passos 4 e 5, 7).

**Pré-requisito:** planos 4 e 5 concluídos nos arquivos (`Tcm-ui` 1.3.0 com as correções da onda final do plano 4: tema `"light"`/`"dark"` convertido, `limpar_temporarios` apaga `.old`, `Modal.confirmar(texto_cancelar=)`; casca 1.2.0). Este plano parte desse estado. O plano 7 (Catraca) já conta com `tcm-ui` 1.4.0 e casca 1.3.0 vindos daqui.

## Global Constraints

- **Sem commit, push, tag ou release** até o Erik dizer "Salvar versão". Nenhum passo commita. Subagentes também não.
- Repositórios públicos: nada de admin do domínio, detalhes de rede, credenciais ou dados reais (CT-es, chaves de acesso, CNPJ, tomadores) em código, testes ou docs. Chaves de teste só geradas por `make_key` com o CNPJ fictício que os testes já usam; PDFs gerados em `tmp_path` (páginas em branco com `pypdf.PdfWriter.add_blank_page`).
- Repositórios em `C:\Users\erik.freitas\Projetos\` (`Tcm-ui`, `Renomeador_CTE`, `Sistema-Financeiro`).
- Versões: `tcm-ui` **1.4.0**, `renomeador-cte` **2.0.0** (hoje `version.py` = 1.0.0, tag `v1.0.0`), casca **1.3.0**. `__version__` commitado igual à tag; o workflow falha se diferente (não usa mais `build.py --tag`).
- Dependências: no `pyproject.toml` só faixa (`tcm-ui>=1.4.0`, `pypdf>=5.0`); o pino `@ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.4.0` fica só no `requirements.txt`. PySide6 vem do `tcm-ui` (não listar de novo).
- `MODULO`: id `renomeador_cte`, nome `Renomeador de CT-e`, ícone `tesoura`, grupo `SF-RenomeadorCTE`, repositório `ErikDeFreitas/Renomeador_CTE`, executável `RenomeadorCTE.exe` (de `RenomeadorCTE.spec`/`release.yml`/`updater.EXE_ASSET_NAME`), página `Pagina("separar", "Separar e renomear", "Um PDF por CT-e, nomeado pelo número. O arquivo original não é alterado.", "tesoura")`.
- Dados ficam onde estão (spec 5.6): o único dado persistente de hoje é o tema em `QSettings("TCM", "RenomeadorCTE")`, chave **`theme`** (`"light"`/`"dark"`) — não é a chave `aparencia/tema` do `tcm-ui`, então a conversão do `tcm-ui` não a cobre (ver Task 4, `migrar_tema`). `aplicacao_settings` do `MODULO` = `RenomeadorCTE` (stem do `.exe`), o mesmo `QSettings`. `MODULO.pasta_dados` = `%LOCALAPPDATA%\RenomeadorCTE` (nova, só para o log do avulso; nada criado no import); variável `RENOMEADOR_DADOS` substitui (testes).
- Testes nunca tocam o registro do Windows (QSettings em `.ini` temporário, como `pdf-merge/tests/conftest.py`), pastas reais, rede nem o FileServer.
- Dentro da casca o módulo nunca chama `setStyleSheet`/`tema.configurar`, não cria `QSettings` (não precisa de nenhum) e para a tarefa em `QApplication.aboutToQuit`.
- Regras de CT-e (`cte_engine.py`: chave, dígito verificador, agrupamento por chave/folha, avisos, nomes com sufixo, prefixo saneado, conflito substituir/manter ambos, origem nunca sobrescrita, gravação via `.part`) **não mudam**: só mudam de lugar. Os 20 testes de `tests/test_cte_engine.py` continuam passando só com a troca de import.
- O `.exe` avulso continua `RenomeadorCTE.exe`, com `RenomeadorCTE.exe.sha256` = `"<hash>  RenomeadorCTE.exe\n"`. O atualizador 1.0.0 exige: Release não rascunho/pré, tag `vX.Y.Z` maior, os dois ativos com esses nomes, `browser_download_url` começando por `https://github.com/ErikDeFreitas/Renomeador_CTE/releases/download/`, hash pela regex `^([0-9a-fA-F]{64})(?:\s|$)`; ele deixa `RenomeadorCTE.exe.old`, que a 2.0.0 precisa apagar.

## Review Focus

1. **Usuário do `RenomeadorCTE.exe` 1.0.0 recebe a 2.0.0**: nomes dos ativos, URL da Release e `.sha256` aceitos pelas regras do `updater.py` 1.0.0; a 2.0.0 apaga `RenomeadorCTE.exe.old` e abre no tema que o usuário tinha (`theme=dark` → escuro). Testes em `test_avulso.py` (Task 4).
2. **Fechar (casca ou avulso) no meio de uma leitura ou geração**: `pode_fechar` falso → confirmação da janela; ao confirmar, `aboutToQuit` → `parar()` + `aguardar()`: para depois do arquivo atual, nenhum `.part` sobra, nenhum Modal aparece durante o fechamento, nada de "QThread destroyed while running". Teste em `test_instancia.py`.
3. **PDF sem texto, corrompido ou com senha**: Modal "Nenhum CT-e encontrado" / "Falha ao ler o PDF" (tom `perigo`), zona de arquivo mostra o erro, a tela sai do estado ocupado e aceita outro PDF. Testes em `test_tela.py`.
4. **Arquivos já existem no destino**: "Cancelar" / "Substituir" / "Manter ambos" com o mesmo efeito de hoje; o PDF de origem nunca é sobrescrito; resumo "Arquivos gerados"/"Concluído com falhas" com "Abrir pasta". Testes em `test_tela.py`.
5. **Tabela com ordenação, filtro e prefixo**: ordenar por Número/Emissão/Páginas usa a chave (não o texto) e a `Etiqueta` de status anda junto com a linha; filtro "Prontos"/"Para revisar" + pesquisa esconde as linhas certas; mudar o prefixo renomeia a coluna Arquivo e a dica "Exemplo de nome". Testes no `tcm-ui` (Task 1) e em `test_tela.py`.

---

### Task 1: tcm-ui 1.4.0 — zona de arquivo, dica do campo, tabela ordenável e ícones

**Files (em `C:\Users\erik.freitas\Projetos\Tcm-ui`):** Modify `src/tcm_ui/components.py`, `src/tcm_ui/styles.qss`, `src/tcm_ui/icons.py`, `src/tcm_ui/__init__.py`, `pyproject.toml`, `README.md`, `src/tcm_ui/demo.py` (mostrar os novos); Create `tests/test_renomeador_extras.py`.

Levantamento (o resto já existe): `Card`→`Cartao`, `StatCard`→`CartaoIndicador`, `ResponsiveRow`→`GradeResponsiva` (colunas iguais; a proporção 2:1 do topo some — aceito), `FormField`→`Campo`, `TextInput`→`CampoTexto`, `SearchInput`→`CampoPesquisa`, `ComboBox`→`Selecao`, `Button`→`Botao` (`primary/secondary/danger` → `primario/secundario/perigo`), `ProgressBar`→`BarraProgresso`, `text_label(..., "caption")`→`Texto(..., "dica")`, `EmptyState`→`EstadoVazio`, `DataTable`+badge→`Tabela`+`Etiqueta`, `Modal.ask`→`Modal.escolher/informar`; tons `success/info/danger` → `sucesso/aviso/perigo` ("Revisar" passa de `info` para `aviso`); ícones `file-text`→`arquivo`, `layers`→`camadas`, `check-circle`→`check_circulo`, `alert-circle`→`alerta`, `folder`→`pasta`. `Sidebar`, `Header`, `ColorSwatch`, `CheckBox`, `TextArea` e o `ThemeManager` só serviam à janela própria ou à página "Design System". Faltam:

**Interfaces — Produces:**
- `ZonaArquivo(titulo, descricao, texto_botao, extensoes=(".pdf",), parent=None)` (`QFrame#ZonaArquivo`), porta do `DropZone` de `..\Renomeador_CTE\components.py`: sinais `arquivo_solto = Signal(str)` (um único arquivo local com extensão aceita, sem diferenciar maiúsculas) e `procurar = Signal()` (clique esquerdo na área ou no botão `secundario` ícone `pasta`); `definir_arquivo(titulo, descricao, texto_botao)` (ícone vira `arquivo`); desativada não aceita arrasto nem clique. QSS: borda tracejada `borda_forte`, `[arrastando="true"]` com borda `primaria` e fundo `primaria_suave`; ícone `upload` na cor `primaria`, repintado em `tema.mudou`.
- `Campo.definir_dica(texto: str) -> None`: troca a dica; se houver erro mostrado, o erro continua e a nova dica volta quando `definir_erro(None)`.
- `Tabela.definir_celula(linha, coluna, valor, ordem=None)` (e `adicionar_linha(valores, ordens=None)`): com `ordem` (número ou texto) a célula ordena por essa chave e não pelo texto — item `ItemOrdenavel(QTableWidgetItem)` com `__lt__` pela chave em `PAPEL_ORDEM = Qt.UserRole + 2` (comparando mesmo tipo; sem chave, cai no texto/`UserRole` em minúsculas); vale para célula com widget (`Etiqueta`). Sem `ordem`, comportamento de hoje. É a mesma API que o plano 7 previa para a 1.5.0: lá ela passa a ser reaproveitada, não recriada.
- Ícones `tesoura` (SVG `scissors`) e `upload` de `..\Renomeador_CTE\icons.py`, mesmo traço.
- `__version__ = "1.4.0"` (e `version` no `pyproject.toml`). Demo mostra a zona, os ícones e uma tabela ordenável.

- [ ] Step 1: testes que falham — `test_zona_aceita_um_pdf` (`QDragEnterEvent`/`QDropEvent` com `QMimeData` de uma URL `tmp_path/"a.PDF"` → `arquivo_solto` com o caminho), `test_zona_recusa_outros` (`.txt`, dois PDFs, ou zona desativada → drag ignorado, nada emitido), `test_zona_clique_pede_procurar`, `test_campo_definir_dica` (troca o texto; com erro ativo o erro fica; `definir_erro(None)` mostra a dica nova), `test_tabela_ordena_pela_chave_e_move_widgets` (linhas `"10"`/`"9"`/`"–"` com `ordem` 10/9/-1 e uma `Etiqueta` diferente em cada → `sortItems(0)` dá `–, 9, 10` e `cellWidget(0, 1)` contém a etiqueta da linha `–`), `test_icones_tesoura_e_upload_renderizam` (pixmap não nulo nos dois temas), `test_qss_tem_zona_arquivo` (QSS gerado nos dois temas contém `#ZonaArquivo` e `[arrastando="true"]`).
- [ ] Step 2: rodar e ver falhar; Step 3: implementar; Step 4: suíte inteira passa (a do 1.3.0 + novos). Conferir também que `atualizador.limpar_temporarios` já apaga `.old` (onda final do plano 4); se não, incluir aqui com teste.
- [ ] Step 5: não commitar.

---

### Task 2: pacote `renomeador_cte` — motor, dados, worker e testes existentes

**Files (em `C:\Users\erik.freitas\Projetos\Renomeador_CTE`):**
- Move (git mv): `cte_engine.py` → `src/renomeador_cte/cte_engine.py` (conteúdo idêntico).
- Create: `pyproject.toml`, `src/renomeador_cte/__init__.py`, `src/renomeador_cte/dados.py`, `src/renomeador_cte/worker.py`, `tests/conftest.py`, `tests/test_worker.py`.
- Modify: `tests/test_cte_engine.py` (só tirar o `sys.path.insert` e trocar `import cte_engine as engine` por `from renomeador_cte import cte_engine as engine`; continua `unittest.TestCase`, roda no pytest).
- Delete: `version.py`, `requirements.txt` (recriado na Task 4). `tests/test_updater.py` sai com o `updater.py` na Task 4 (o `tcm_ui.atualizador` tem os próprios testes; a compatibilidade com o 1.0.0 vira `test_avulso.py`).

**Interfaces — Produces:**
- `renomeador_cte.__version__ = "2.0.0"`.
- `dados.NOME_PASTA = "RenomeadorCTE"`; `dados.pasta_dados() -> Path` (`RENOMEADOR_DADOS` ou `%LOCALAPPDATA%\RenomeadorCTE`); `dados.PASTA`. Só stdlib, nada criado no import.
- `worker.Cancelado(Exception)`; `worker.Tarefa(QThread)` — `Tarefa(funcao: Callable[[Callable[[int, int], None]], object], parent=None)`; sinais `progresso(int, int)`, `concluida(object)`, `falhou(str)`, `cancelada()`; `cancelar()` liga um `threading.Event`. O callback de progresso passado à `funcao` emite `progresso` e, se cancelado, lança `Cancelado` — assim `analyze_pdf` para depois da página atual e `export_documents` depois do arquivo atual **sem mudar o motor** (o progresso é chamado fora do `try` de cada arquivo; o `.part` é limpo pelo `finally` de `_write_pages`). `PdfAnalysisError` → `falhou(str(exc))`; outra exceção → `falhou(f"Erro inesperado: {exc}")` (igual ao `TaskThread` de hoje).
- `pyproject.toml` no modelo do `pdf-merge`: `name = "renomeador-cte"`, versão dinâmica (`renomeador_cte.__version__`), `dependencies = ["tcm-ui>=1.4.0", "pypdf>=5.0"]`, extra `dev = ["pytest", "pytest-qt"]`, entry point `renomeador_cte = "renomeador_cte.modulo:MODULO"` (o `modulo.py` chega na Task 3), `testpaths = ["tests"]`.
- `tests/conftest.py` no modelo do `pdf-merge`: antes de qualquer import do pacote, `QT_QPA_PLATFORM=offscreen` e `RENOMEADOR_DADOS` = pasta temporária; troca de `QtCore.QSettings` por `.ini` em pasta temporária. Fixtures compartilhadas: `make_key`/`pdf_em_branco(tmp_path, paginas)`/`resultado_falso(pdf, numeros)` (`AnalysisResult` com `CteDocument` fictícios sobre o PDF em branco).

- [ ] Step 1: testes que falham — `tests/test_worker.py`: `test_tarefa_emite_progresso_e_concluida` (qtbot.waitSignal), `test_cancelar_para_exportacao_depois_do_arquivo_atual` (`export_documents` de 3 documentos sobre PDF em branco; cancelar no 1º progresso → `cancelada`, 1 arquivo gerado, nenhum `*.part` na pasta), `test_cancelar_analise` (`analyze_pdf` de PDF em branco com 5 páginas), `test_erro_de_pdf_vira_falhou` (arquivo `.pdf` com bytes inválidos → `falhou` com a mensagem do motor); `test_dados_variavel_e_padrao` (`RENOMEADOR_DADOS`; sem ela, `LOCALAPPDATA` em `tmp_path`), `test_importar_nao_cria_pasta`.
- [ ] Step 2: rodar e ver falhar; Step 3: mover, criar, `pip install -e ..\Tcm-ui -e .[dev]` num `.venv` do repositório; Step 4: passar (20 do motor + novos). `git diff --no-index` do `cte_engine.py` antigo × novo: idêntico.
- [ ] Step 5: não commitar.

---

### Task 3: tela, instância e `MODULO`

**Files:** Create `src/renomeador_cte/tela.py`, `src/renomeador_cte/instancia.py`, `src/renomeador_cte/modulo.py`, `tests/test_tela.py`, `tests/test_instancia.py`, `tests/test_modulo.py`.

**Interfaces:**
- Consumes: Task 1 (`ZonaArquivo`, `Campo.definir_dica`, `Tabela.definir_celula(..., ordem=)`, `tesoura`), `tcm_ui.components` (`Pagina`, `Cartao`, `Campo`, `CampoTexto`, `CampoPesquisa`, `Selecao`, `Botao`, `BarraProgresso`, `CartaoIndicador`, `GradeResponsiva`, `EstadoVazio`, `Tabela`, `Etiqueta`, `Modal`, `Texto`), `tcm_ui.modulo`, Task 2.
- Produces:
  - `tela.TelaRenomear(contexto)` (subclasse de `Pagina`), porta de `main.py:RenamePage`: atributos `zona`, `campo_pasta`, `botao_procurar`, `campo_prefixo`, `campo_prefixo_field` (o `Campo`), `botao_gerar`, `progresso`, `rotulo_progresso`, `indicadores` (dict `paginas/ctes/prontos/revisar`), `pesquisa`, `filtro_status`, `tabela`, `vazio`; propriedades `rodando`, `resultado`; métodos `analisar(caminho: str)`, `gerar()`, `parar()`, `aguardar()`. Constantes `COLUNAS = ["Número", "Emissão", "Tomador", "Páginas", "Arquivo", "Status"]`, `COL_STATUS = 5`, `FILTROS = ["Todos os status", "Prontos", "Para revisar"]`.
  - `instancia.Renomeador(contexto)`: `widget("separar")` cria a tela uma vez, outra chave → `KeyError`; `acoes_cabecalho` → `[]`; `pode_fechar` → `tela is None or (not tela.rodando and not tela.pendente)`, onde `tela.pendente` é verdadeiro quando há PDF analisado e ainda não gerado (a 1.0.0 já segurava a atualização nesse caso; decisão do controlador em 24/11).
  - `modulo.MODULO` com os valores dos Global Constraints, `pasta_dados=dados.PASTA`, importando a instância só dentro de `criar`.

- Tela (textos e comportamento de hoje): `GradeResponsiva(320)` com cartão "1. Arquivo" ("PDF com um ou mais CT-es."; `ZonaArquivo("Arraste o PDF para cá", "ou clique para selecionar no computador", "Selecionar PDF")`, progresso + rótulo escondidos fora de tarefa) e cartão "2. Destino" (`Campo("Pasta de destino")` com `CampoTexto` + "Procurar"; `Campo("Prefixo do nome (opcional)", dica="Exemplo de nome: <prefixo>774.pdf")` atualizada com `definir_dica` usando `cte_engine.sanitize_prefix` e o 1º número lido; botão `primario` `lg` "Separar e renomear" ícone `tesoura`). `GradeResponsiva(200)` com 4 `CartaoIndicador` (Páginas `arquivo` neutro, CT-es `camadas` primaria, Prontos `check_circulo` sucesso, Para revisar `alerta` perigo; "–" sem resultado; contas de `_update_stats` iguais). Cartão "Documentos" com `pesquisa` ("Pesquisar por número, tomador ou arquivo") + `filtro_status` e `QStackedLayout` `EstadoVazio("Nenhum documento carregado", "Selecione um PDF para ver os CT-es aqui.", "arquivo")` × `tabela` (`coluna_flexivel=2`, mín. 300 px).
- Linhas: mesmas regras de `_add_document_row`/`_add_unidentified_row`; `ordem` = número inteiro, data `aaaammdd`, 1ª página, status; linha "Páginas não identificadas" com `ordem` -1. Status = `Etiqueta(status, tom, clicavel=bool(detalhe) and tom != "sucesso", dica=detalhe)` (Erro `perigo`, Revisar `aviso`, Salvo/Pronto `sucesso`); clicada → `Modal.informar(contexto.janela, status, detalhe, tom)`. Flag de revisão no item da coluna Status (`Qt.UserRole + 20`, como hoje); filtro próprio (pesquisa em todas as colunas + status), não `Tabela.filtrar`. `setSortingEnabled(False)` ao preencher, `True` depois.
- Escolha de PDF/pasta: `QFileDialog` com `contexto.janela` como pai. Pasta padrão `CTEs_<nome do PDF>` ao lado do PDF enquanto o usuário não escolher outra (como hoje). Motor chamado como `cte_engine.analyze_pdf`/`export_documents` (atributo do módulo, para os testes trocarem).
- Conflito: `Modal.escolher(contexto.janela, "Arquivos já existem", <texto de hoje>, [("Cancelar", "secundario", None), ("Substituir", "perigo", "substituir"), ("Manter ambos", "primario", "manter")], "info")`. Fim: "Arquivos gerados" (`sucesso`) ou "Concluído com falhas" (`perigo`, 3 primeiras falhas) com `[("Fechar", "secundario", False), ("Abrir pasta", "primario", True)]` → `QDesktopServices.openUrl`. "Nenhum CT-e encontrado" e "Falha ao ler o PDF" com `Modal.informar(..., "perigo")` e os textos de hoje.
- Thread: uma `worker.Tarefa` por vez; no fim `wait()` antes de `deleteLater` (achado do plano 4). `cancelada` só limpa o estado (sem Modal). Ao sair: `QApplication.aboutToQuit` → `parar()` + `aguardar()`; com o app fechando, os callbacks não abrem Modal.

- [ ] Step 1: testes que falham — `test_modulo.py` (valores do `MODULO`, `nome_exe == "RenomeadorCTE.exe"`, `aplicacao_settings == "RenomeadorCTE"`, `paginas` só com `separar` (sem "Design System"), entry point carrega, `import renomeador_cte.modulo` num subprocesso não importa `pypdf` nem `renomeador_cte.tela`); `test_instancia.py` (widget único, `KeyError`, `acoes_cabecalho == []`, `pode_fechar` falso com tarefa presa num `threading.Event`, `aboutToQuit` emitido → tarefa cancelada, thread terminada, sem Modal); `test_tela.py` (`analyze_pdf` trocado por `resultado_falso` com números 774, 775, 775 → 3 linhas, sufixo `_2`, indicadores 3/3/…; `test_ordenar_por_numero_move_etiquetas`; `test_filtro_para_revisar_e_pesquisa`; `test_prefixo_renomeia_coluna_e_dica`; `test_pdf_sem_texto_mostra_nenhum_cte` e `test_pdf_invalido_mostra_falha` com `Modal.informar` trocado por falso e tela livre depois; `test_conflito_cancelar_substituir_manter` com `Modal.escolher` trocado — PDFs em `tmp_path`, origem intacta; `test_etiqueta_revisar_abre_detalhe`; `test_soltar_pdf_na_zona_analisa`).
- [ ] Step 2: falhar; Step 3: implementar; Step 4: passar (suíte inteira).
- [ ] Step 5: não commitar.

---

### Task 4: `.exe` avulso, build e Release do Renomeador

**Files:** Modify `main.py` (reescrito), `.gitignore`, `.github/workflows/release.yml`; Create `build.ps1`, `requirements.txt`, `README.md`, `tests/test_avulso.py`; Delete `components.py`, `icons.py`, `themes.py`, `styles.qss`, `updater.py`, `build.py`, `RenomeadorCTE.spec`, `tests/test_updater.py`; mantém `assets/app.ico`.

**Interfaces — Produces:** `main.migrar_tema(config: QSettings) -> None` (se `aparencia/tema` não existe e `theme` é `"light"`/`"dark"`, grava `aparencia/tema` = `"claro"`/`"escuro"`; não apaga `theme`; outro valor não faz nada); `main()` = `migrar_tema(QSettings("TCM", "RenomeadorCTE"))` → `sys.exit(rodar_avulso(MODULO))`. O `.old` do atualizador 1.0.0 é apagado pelo `tcm_ui.atualizador.limpar_temporarios` (Task 1).

- `requirements.txt`: `tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.4.0`.
- `build.ps1` no modelo do `pdf-merge\build.ps1` (`-Python`): `$nome = "RenomeadorCTE"`, `--icon assets/app.ico`, `--collect-data tcm_ui --collect-data renomeador_cte`, `--exclude-module` do `.spec` atual (`tkinter`, `numpy`, `PIL`, `matplotlib`, `pandas`, `pytest`) + os de Qt do Mesclador (`QtWebEngineCore`, `QtWebEngineWidgets`, `QtQml`, `QtQuick`, `QtPdf`, `QtMultimedia`); `dist\RenomeadorCTE.exe.sha256` = `"<hash>  RenomeadorCTE.exe\n"`; versão lida de `src\renomeador_cte\__init__.py`.
- `release.yml` no modelo do `pdf-merge` (3.0.0): instala `-r requirements.txt . pytest pytest-qt pyinstaller`; confere tag = `renomeador_cte.__version__`; testes offscreen; `./build.ps1 -Python python`; publica `RenomeadorCTE.exe` + `RenomeadorCTE.exe.sha256` (softprops; os `browser_download_url` seguem `https://github.com/ErikDeFreitas/Renomeador_CTE/releases/download/`).
- `.gitignore`: mantém `*.pdf`, `CTEs_*/`, `build/`, `dist/`, `.venv/`; acrescenta `*.egg-info/`; tira a linha `app.ico` (o `assets/app.ico` é rastreado).
- README (não existe hoje): o que faz, uso (janela, arrastar PDF), o que fica salvo (só o tema), desenvolver (`.venv` + `..\Tcm-ui` editável ou `-r requirements.txt`), lançar versão, módulo da casca (grupo `SF-RenomeadorCTE`). Sem exemplos com dados reais.
- [ ] Step 1: testes que falham — `test_build_usa_nome_do_exe` (`build.ps1`, `release.yml` e `MODULO.nome_exe` usam `RenomeadorCTE.exe`), `test_release_aceita_pelo_atualizador_1_0_0` (cópia, no teste, de `_HASH_RE` e das regras de `parse_release` do `updater.py` 1.0.0: payload com tag `v2.0.0`, os dois ativos e URLs do prefixo acima → aceito; conteúdo do `.sha256` no formato acima → mesmo hash pela regex antiga e pela do `tcm_ui.atualizador`), `test_migrar_tema` (QSettings `.ini` temporário: `theme=dark` → `escuro`; `theme=light` → `claro`; `aparencia/tema` já gravado não muda; `theme` continua lá), `test_workflow_confere_versao` (texto do `release.yml` contém `renomeador_cte.__version__`).
- [ ] Step 2: `powershell -File build.ps1` (venv do repositório com `..\Tcm-ui` editável) gera `dist\RenomeadorCTE.exe`; rodar com `RENOMEADOR_DADOS` temporário e `QT_QPA_PLATFORM=offscreen` por alguns segundos e fechar (sem erro no log). O controlador confere a janela real nos dois temas (capturas pelo Python, grab do widget, nunca da tela).
- [ ] Step 3: conferência manual do Erik (não automatizável): separar um PDF real dele numa pasta local, conferir nomes e páginas iguais aos da 1.0.0; nada disso vai para o repositório.
- [ ] Step 4: não commitar.

---

### Task 5: casca 1.3.0 com o Renomeador

**Files (em `C:\Users\erik.freitas\Projetos\Sistema-Financeiro`):** Modify `requirements.txt`, `requirements-local.txt`, `build.ps1` (só o comentário/linha do `-Local`), `pyproject.toml`, `src/sistema_financeiro/__init__.py`, `README.md`, `CLAUDE.md`; tests.

- `requirements.txt`: `tcm-ui@v1.4.0`, `robo-agregado@v2.0.1`, `mesclador@v3.0.0`, `enviador-pdf-xml@v2.0.0`, `renomeador-cte @ git+https://github.com/ErikDeFreitas/Renomeador_CTE@v2.0.0`. `pyproject.toml`: `tcm-ui>=1.4.0`. `__version__ = "1.3.0"`.
- `-Local`/`requirements-local.txt`: acrescentar `../Renomeador_CTE`.
- `descoberta.ORDEM` já tem `renomeador_cte` (nada a mudar). `ferramentas/args_pyinstaller.py` já pega o entry point (nada a mudar).
- Testes: `verificar_modulos()` com os quatro módulos → 0; ordem na barra: RoboAgregado, Mesclador de PDFs, Enviador de PDF + XML, Renomeador de CT-e; `test_args_pyinstaller_inclui_renomeador` (`--collect-all renomeador_cte` e `--copy-metadata renomeador-cte`); com `SF_GRUPOS_DEV="SF-RenomeadorCTE"` só o Renomeador aparece.
- [ ] Step 1: venv da casca com os seis repositórios locais editáveis; `pip install` resolve um único `tcm-ui` 1.4.0 e um único `pypdf` (faixas do Mesclador e do Renomeador compatíveis); suíte passa.
- [ ] Step 2: `powershell -File build.ps1 -Local` → `dist\SistemaFinanceiro.exe`, `--verificar` OK com os quatro módulos (`PIL` continua no `.exe` da casca por causa do Mesclador). O controlador confere a janela (capturas pelo Python com `SF_GRUPOS_DEV`), incluindo a tela do Renomeador no tema escuro com uma tabela preenchida por `resultado_falso`.
- [ ] Step 3: README (grupo `SF-RenomeadorCTE`), `CLAUDE.md` ("Onde paramos"; ordem do "Salvar versão": Tcm-ui v1.4.0 → Renomeador_CTE v2.0.0 → Sistema-Financeiro v1.3.0, depois das tags dos planos 4 e 5; a TI cria `SF-RenomeadorCTE`; a tag v2.0.0 chega a todos os usuários do avulso, então só depois da Task 4 Step 3).
- [ ] Step 4: não commitar.
