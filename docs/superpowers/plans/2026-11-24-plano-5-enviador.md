# Plano 5 — Enviador de PDF + XML no Sistema Financeiro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar o Enviador de PDF + XML (`ErikDeFreitas/pdf-xml-mailer`) para módulo `enviador_pdf_xml` com o visual do `tcm-ui`, mantendo o `EnviadorEmails.exe` avulso e a conta Microsoft já conectada dos usuários atuais, e incluí-lo na casca.

**Architecture:** Mesmo caminho do Mesclador (plano 4): pacote `src/enviador_pdf_xml/` com `MODULO` no entry point `sistema_financeiro.modulos`, núcleo (`envio`, `conta`, `configuracao`, `cli`, `worker`) só muda de lugar, tela e diálogos reescritos com os componentes do `tcm-ui`, `main.py` → `rodar_avulso`. O atualizador próprio (`core/atualizacao.py`, `ui/atualizacao.py`) sai e entra o `tcm_ui.atualizador`. O `tcm-ui` 1.3.0 ganha só o que falta ao Enviador (2 ícones e reajuste de altura do `Modal`).

**Tech Stack:** Python 3.13, PySide6, msal + msal-extensions (cache DPAPI), smtplib (XOAUTH2), pytest + pytest-qt (offscreen), PyInstaller, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md` (seções 2, 5.2, 5.4, 5.6, 5.7, 6 passo 4, 7).

**Pré-requisito:** plano 4 concluído nos arquivos (`Tcm-ui` 1.2.0, `Send_Agregados` 2.0.1, `pdf-merge` 3.0.0, casca 1.1.0). Este plano parte desse estado.

## Global Constraints

- **Sem commit, push, tag ou release** até o Erik dizer "Salvar versão". Nenhum passo commita. Subagentes também não.
- Repositórios públicos: nada de admin do domínio, detalhes de rede, e-mails reais, credenciais ou dados reais (faturas, CT-es, XMLs, CNPJ) em código, testes ou docs. Nos testes, só `@b.com`/`@tcm.com` fictícios como hoje. `CLIENT_ID`/`TENANT_ID` continuam como estão em `modelo.py` (cliente público, já publicados; não são segredo) e não são copiados para docs.
- Repositórios em `C:\Users\erik.freitas\Projetos\` (`Tcm-ui`, `pdf-xml-mailer`, `Sistema-Financeiro`).
- Versões: `tcm-ui` **1.3.0**, `enviador-pdf-xml` **2.0.0** (hoje 1.0.0), casca **1.2.0**. `__version__` commitado igual à tag; o workflow falha se diferente (não reescreve mais `version.py`).
- Dependências: no `pyproject.toml` só faixa (`tcm-ui>=1.3.0`, `msal>=1.39,<2`, `msal-extensions>=1.3.1,<2`); o pino `@ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.3.0` fica só no `requirements.txt`. PySide6 vem do `tcm-ui` (não listar `PySide6-Essentials` de novo).
- `MODULO`: id `enviador_pdf_xml`, nome `Enviador de PDF + XML`, ícone `email`, grupo `SF-EnviadorPDFXML`, repositório `ErikDeFreitas/pdf-xml-mailer`, executável `EnviadorEmails.exe` (de `EnviadorEmails.spec`/`release.yml`), página `Pagina("enviar", "Enviar PDF + XML", "Um e-mail por par de arquivos com o mesmo nome.", "enviar")`.
- Dados ficam onde estão (spec 5.6): `config.json` em `%APPDATA%\EnviadorEmails\`, cache MSAL em `%LOCALAPPDATA%\EnviadorEmails\token_cache.bin`. `MODULO.pasta_dados` = `%LOCALAPPDATA%\EnviadorEmails` (logs do avulso vão para `...\logs\`). Variável `ENVIADOR_DADOS` substitui as **duas** pastas (testes). Os caminhos são calculados na hora da chamada, nunca congelados no import.
- MSAL igual a hoje: mesmo `CLIENT_ID`, `TENANT_ID`, autoridade `https://login.microsoftonline.com/<TENANT_ID>`, `ESCOPOS`, `PersistedTokenCache(build_encrypted_persistence(...))` no mesmo arquivo. Login interativo continua numa thread daemon com `timeout=180`.
- Testes nunca tocam AppData real, registro do Windows (QSettings em `.ini` temporário, como no `pdf-merge/tests/conftest.py`), rede, SMTP real nem conta Microsoft real (`FakeApp`/`FakeConta`/`FakeSMTP` de hoje; `msal.PublicClientApplication` trocado por falso quando preciso).
- Dentro da casca o módulo nunca chama `setStyleSheet` no `QApplication`, não chama `tema.configurar`, cria `QSettings` só com `("TCM", "EnviadorEmails")` explícito e para o envio em `QApplication.aboutToQuit`.
- Testes existentes continuam passando depois da mudança para `src/`: os de núcleo só trocam imports (`core.` → `enviador_pdf_xml.`); exceções explícitas abaixo (`delenv("ENVIADOR_DADOS")` em 2 testes de caminho; testes de UI adaptados aos nomes do `tcm-ui` mantendo as mesmas asserções).
- Regras de envio (`envio.py`: pares, validações, XOAUTH2, reconexão, mover para `enviados/`/`erros/`, nunca reenviar "Enviado com aviso") não mudam.

## Review Focus

1. **Conta Microsoft depois de atualizar para a 2.0.0**: o usuário abre o avulso ou a casca e continua conectado (mesmo cache, mesmo cliente/autoridade); "Sair da conta" e "Entrar com a Microsoft" funcionam. Testes `test_caminho_cache_usa_localappdata`, `test_criar_app_mesmos_parametros` (Task 2); conferência manual do Erik com a própria conta na Task 4.
2. **Fechar (casca ou avulso) no meio de um envio**: `pode_fechar` falso → Modal da janela; ao confirmar, `aboutToQuit` → `parar()` + `aguardar()`: termina o e-mail atual, não manda os seguintes, nada de "QThread destroyed while running" nem e-mail duplicado. Teste em `test_instancia.py`.
3. **Usuário do `EnviadorEmails.exe` 1.0.0 recebe a 2.0.0**: o atualizador antigo procura `EnviadorEmails.exe` + `EnviadorEmails.exe.sha256` e lê `split()[0]`; deixa `EnviadorEmails.exe.old`, que a 2.0.0 precisa apagar (o `tcm_ui` só limpa `.antigo`/`.novo`). Testes na Task 4.
4. **Sessão expirada / login travado dentro da casca**: `sessao_expirada` abre o diálogo de conta com `contexto.janela` como pai; Cancelar fecha mesmo com o navegador parado; o atualizador não troca o `.exe` durante envio (`modulos_com_tarefa`). Testes em `test_ui_conta.py` e `test_instancia.py`.
5. **Primeiro acesso, arrastar e soltar e MSAL sem rede**: sem conta/Para, o diálogo abre uma vez na primeira exibição da página; soltar PDFs/XMLs/pastas na página adiciona (antes era na janela, que agora é da casca); falha inesperada ao criar a `Conta` (ex.: sem rede) vira aviso na tela, não cartão de erro. Testes em `test_tela.py`.

---

### Task 1: tcm-ui 1.3.0 — ícones `email`/`sair` e `Modal.reajustar_altura`

**Files (em `C:\Users\erik.freitas\Projetos\Tcm-ui`):** Modify `src/tcm_ui/icons.py`, `src/tcm_ui/components.py`, `src/tcm_ui/__init__.py`, `pyproject.toml`, `README.md`, `src/tcm_ui/demo.py`; Create `tests/test_enviador_extras.py`.

Levantamento (o resto já existe no 1.2.0): `Badge` → `Etiqueta(clicavel=True, dica=...)`; tons `neutral/primary/success/warning/danger` → `neutro/primaria/sucesso/aviso/perigo`; `Card`→`Cartao` (`adicionar_acao`), `FormField`→`Campo` (`definir_erro`), `Input`→`CampoTexto`, `TextArea`→`AreaTexto`, `ProgressBar`→`BarraProgresso`, `DataTable`→`Tabela`, `Label` papéis `muted/hint/label` → `suave/dica/rotulo`, `Modal.confirm/alert` → `Modal.confirmar/escolher/informar`; ícones `send`→`enviar`, `settings`→`config`, `file-text`→`arquivo`, `folder-open`→`pasta`, `eraser`→`borracha`, `x`→`fechar`. Faltam:

**Interfaces — Produces:**
- Ícones `email` (envelope, SVG `mail` de `..\pdf-xml-mailer\ui\icons.py`) e `sair` (SVG `log-out`), mesmo traço.
- `Modal.reajustar_altura() -> None`: recalcula a altura fixa para a largura atual (mesma conta do `showEvent`); para diálogos cujo conteúdo muda depois de exibido (erro em `Campo`, prévia que cresce, botão que aparece/some).
- `__version__ = "1.3.0"` (e `version` no `pyproject.toml`). Demo mostra os 2 ícones.

- [ ] Step 1: testes que falham — `test_icones_email_e_sair_renderizam` (pixmap não nulo nos dois temas), `test_modal_reajusta_altura_com_erro_no_campo` (Modal com `Campo`; `show()`; `definir_erro("x")`; `reajustar_altura()` → `height()` maior que antes; sem erro volta a diminuir).
- [ ] Step 2: rodar e ver falhar; Step 3: implementar; Step 4: suíte inteira passa (a do 1.2.0 + novos).
- [ ] Step 5: não commitar.

---

### Task 2: pacote `enviador_pdf_xml` — núcleo, dados e testes existentes

**Files (em `C:\Users\erik.freitas\Projetos\pdf-xml-mailer`):**
- Move (git mv): `core/{cli,configuracao,conta,envio,modelo,worker,__main__}.py` → `src/enviador_pdf_xml/`.
- Create: `pyproject.toml`, `src/enviador_pdf_xml/__init__.py`, `src/enviador_pdf_xml/dados.py`, `tests/test_dados.py`; reescreve `tests/conftest.py`.
- Delete: `core/__init__.py`, `core/atualizacao.py`, `version.py`, `pytest.ini` (vai para o `pyproject.toml`), `requirements.txt` (recriado na Task 4), `tests/test_esqueleto.py` (repo/exe passam para `test_modulo.py` na Task 3; o teste do tema antigo deixa de existir).
- Modify (só imports `core.` → `enviador_pdf_xml.`): `tests/test_cli.py`, `test_configuracao.py`, `test_conta.py`, `test_envio.py`, `test_lote.py`, `test_modelo_email.py`, `test_worker.py`. `tests/__init__.py` fica (os testes importam `tests.test_lote`).

**Interfaces — Produces:**
- `enviador_pdf_xml.__version__ = "2.0.0"`.
- `dados.NOME_PASTA = "EnviadorEmails"` (= `modelo.APLICACAO`); `dados.pasta_config() -> Path` (`ENVIADOR_DADOS` ou `%APPDATA%\EnviadorEmails`); `dados.pasta_local() -> Path` (`ENVIADOR_DADOS` ou `%LOCALAPPDATA%\EnviadorEmails`); `dados.PASTA: Path = pasta_local()`. Só stdlib, nada criado no import.
- `configuracao.caminho_padrao()` = `pasta_config() / "config.json"`; `conta.caminho_cache()` = `pasta_local() / "token_cache.bin"` (mesmos caminhos de hoje sem a variável).
- `worker.LoginWorker`, `worker.EnviarWorker` como hoje; `BaixarAtualizacaoWorker` sai (o atualizador agora é o do `tcm-ui`).
- `python -m enviador_pdf_xml "C:\Pasta" --vcto dd/mm/aaaa [--cco ...] [--dry-run]` como hoje `python -m core` (`prog` atualizado; códigos de saída iguais).
- `pyproject.toml` no modelo do `pdf-merge`: `name = "enviador-pdf-xml"`, versão dinâmica (`enviador_pdf_xml.__version__`), `dependencies = ["tcm-ui>=1.3.0", "msal>=1.39,<2", "msal-extensions>=1.3.1,<2"]`, extra `dev = ["pytest", "pytest-qt"]`, entry point `enviador_pdf_xml = "enviador_pdf_xml.modulo:MODULO"` (o `modulo.py` chega na Task 3), `testpaths = ["tests"]`, `addopts = "-p no:anyio"`.
- `tests/conftest.py` no modelo do `pdf-merge`: antes de qualquer import do pacote, `QT_QPA_PLATFORM=offscreen` e `ENVIADOR_DADOS` = pasta temporária; troca de `QtCore.QSettings` por `.ini` em pasta temporária; fixture autouse por teste `monkeypatch.setenv("ENVIADOR_DADOS", str(tmp_path / "dados"))`. Sem `sys.path.insert` (pacote instalado editável).

- [ ] Step 1: testes que falham — `tests/test_dados.py`: `test_enviador_dados_substitui_as_duas_pastas`, `test_sem_variavel_usa_appdata_e_localappdata` (delenv + `APPDATA`/`LOCALAPPDATA` em `tmp_path`), `test_importar_nao_cria_pasta`, `test_criar_app_mesmos_parametros` (troca `msal.PublicClientApplication` por falso que guarda os argumentos: `client_id == modelo.CLIENT_ID`, `authority == f"https://login.microsoftonline.com/{modelo.TENANT_ID}"`, `token_cache` é `PersistedTokenCache` em `caminho_cache()`). Em `test_configuracao.py::test_caminho_padrao_usa_appdata` e `test_conta.py::test_caminho_cache_usa_localappdata` (e `test_cache_de_token_criptografado_funciona`) acrescentar só `monkeypatch.delenv("ENVIADOR_DADOS")`.
- [ ] Step 2: rodar e ver falhar; Step 3: mover, `dados.py`, imports absolutos `enviador_pdf_xml.x`, `pip install -e ..\Tcm-ui -e .[dev]` num `.venv` do repositório; Step 4: passar (66 testes de núcleo + novos).
- [ ] Step 5: não commitar.

---

### Task 3: telas, instância e `MODULO`

**Files:** Create `src/enviador_pdf_xml/tela.py`, `src/enviador_pdf_xml/dialogos.py`, `src/enviador_pdf_xml/instancia.py`, `src/enviador_pdf_xml/modulo.py`, `tests/test_modulo.py`, `tests/test_instancia.py`, `tests/test_tela.py`. Modify (adaptar a nomes/propriedades do `tcm-ui`, mesmas asserções): `tests/test_ui_conta.py`, `tests/test_ui_email.py`, `tests/test_ui_janela.py` (fixture `janela` passa a criar `TelaEnviar`; `property("variant") == "primary"` → `property("variante") == "primario"`; tema aplicado com `tema.aplicar(app)` do `tcm-ui`).

**Interfaces:**
- Consumes: Task 1 (`email`, `sair`, `Modal.reajustar_altura`), `tcm_ui.components` (`Pagina`, `Cartao`, `Campo`, `CampoTexto`, `AreaTexto`, `Botao`, `BarraProgresso`, `Tabela`, `Etiqueta`, `Modal`, `Texto`), `tcm_ui.modulo`, Task 2.
- Produces:
  - `dialogos.DialogoConta(conta, cfg, parent=None, caminho_config=None, primeiro_acesso=False, sessao_expirada=False)` (porta de `ui/conta.py`, `Modal` tom `info`; mantém `rotulo_conta`, `aviso`, `botao_entrar`, `botao_sair` (ícone `sair`), `campo_para(_field)`, `campo_cco(_field)`, `botao_salvar`, `resultado`, `done()` que abandona o login; chama `reajustar_altura()` ao mudar estado/erros).
  - `dialogos.DialogoEmail(cfg, parent=None, caminho_config=None)` (porta de `ui/email.py`; `campo_assunto`, `campo_corpo`, `previa_assunto`, `previa_corpo`, `restaurar_padrao()`, `resultado`; "Restaurar padrão" como botão `fantasma` no rodapé; `reajustar_altura()` no lugar do `setMinimumHeight/adjustSize`).
  - `tela.STATUS` (mesmo dicionário de hoje com tons `neutro/primaria/sucesso/aviso/perigo/aviso`); `tela.TelaEnviar(contexto, conta, caminho_config=None)` (subclasse de `tcm_ui.components.Pagina`), com os mesmos atributos e métodos públicos de `main.py:EnviarPage` (`lbl_conta`, `lbl_para`, `btn_config`, `btn_arquivos`, `btn_limpar`, `btn_pasta` primário, `botao_enviar` perigo, `botao_cancelar`, `btn_email`, `campo_vcto`, `lbl_assunto`, `lbl_resumo`, `tabela`, `rodando`, `adicionar()`, `limpar()`, `status_de()`, `parar()`, `aguardar()`, `recarregar_conta()`, `abrir_configuracoes()`, `abrir_email()`, `pronto_para_configurar()`).
  - `instancia.FABRICA_CONTA: Callable = conta.Conta` (testes trocam); `instancia.criar_conta(log) -> tuple[Conta | None, str]` (`ContaNaoConfigurada` → `(None, "O login Microsoft ainda não foi configurado nesta versão. Fale com a TI.")`; outra exceção → `log.exception` e `(None, "Não foi possível iniciar o login Microsoft. Detalhes no log.")`).
  - `instancia.Enviador(contexto)`: `widget("enviar")` cria a `TelaEnviar` uma vez (com a `Conta` criada aí, não no `MODULO`), outra chave → `KeyError`; `acoes_cabecalho` → `[]` ("Configurações" continua no cartão "Conta e destino"); `pode_fechar` → `tela is None or not tela.rodando`.
  - `modulo.MODULO` com os valores dos Global Constraints, `pasta_dados=dados.PASTA`, importando a instância só dentro de `criar`.

- Tela: mesmos três cartões de hoje ("Conta e destino" com ação "Configurações"; "Envio" com Vencimento (`setInputMask("99/99/9999;_")`), prévia do assunto + "Configurar e-mail", progresso, resumo, Cancelar/Escolher pasta/Enviar; "Arquivos" com Escolher arquivos/Limpar + `Tabela(["Nome", "PDF", "XML", "Status"])`). Status = `Etiqueta(texto, tom, clicavel=bool(detalhe), dica="Clique para ver os detalhes")` ligada ao `Modal.informar` com tom `perigo` (Erro) ou `aviso`; clique na linha também abre (nome do par em `Qt.UserRole + 1` da coluna 0). Confirmações com `Modal.escolher` para manter os textos de hoje ("Cancelar envio?" → "Continuar"/"Cancelar envio"). Diálogos de arquivo e Modais com `contexto.janela` como pai.
- Arrastar e soltar: `TelaEnviar.setAcceptDrops(True)`, `dragEnterEvent`/`dropEvent` (recusa enquanto `rodando`).
- Primeiro acesso: no primeiro `showEvent`, `QTimer.singleShot(300, ...)` abre `DialogoConta(primeiro_acesso=True)` se `pronto_para_configurar()`; só uma vez por instância.
- Ao sair: `QApplication.aboutToQuit` → `parar()` + `aguardar()` (a confirmação vem do `pode_fechar` na `JanelaPrincipal`). `_ao_expirar` não abre diálogo se o app estiver fechando.
- [ ] Step 1: testes que falham — `test_modulo.py` (valores do `MODULO`, `nome_exe == "EnviadorEmails.exe"`, `repositorio`, `aplicacao_settings == "EnviadorEmails"`, entry point carrega, `import enviador_pdf_xml.modulo` não importa `msal`, `smtplib` nem `PySide6.QtWidgets` — conferir `sys.modules` num subprocesso); `test_instancia.py` (widget único, `KeyError`, `acoes_cabecalho == []`, `pode_fechar` falso com thread de envio parada num `threading.Event`, `aboutToQuit` emitido → worker cancelado e thread terminada, `FABRICA_CONTA` que lança `OSError` → tela abre com o aviso e sem `Conta`); `test_tela.py` (`test_soltar_arquivos_adiciona` com `QDropEvent` e `QMimeData` de URLs em `tmp_path`; `test_primeiro_acesso_abre_uma_vez` trocando `DialogoConta.exec` por falso; `test_etiqueta_de_erro_abre_detalhe` trocando `Modal.informar`; `test_sessao_expirada_abre_conta`); os 27 testes de UI adaptados.
- [ ] Step 2: falhar; Step 3: implementar; Step 4: passar (suíte inteira).
- [ ] Step 5: não commitar.

---

### Task 4: `.exe` avulso, build e Release do Enviador

**Files:** Modify `main.py` (reescrito), `README.md`, `.gitignore` (`*.egg-info/`), `.graphifyignore` (tirar `ui/`, se listado), `.github/workflows/release.yml`; Create `build.ps1`, `requirements.txt`, `tests/test_avulso.py`; Delete `ui/`, `core/` (vazia), `EnviadorEmails.spec`; mantém `assets/EnviadorEmails.ico` e `docs/`.

**Interfaces — Produces:** `main.py` = `sys.exit(rodar_avulso(MODULO))`. Não precisa de `limpar_legado` nem `migrar_tema`: o `tcm-ui` 1.2.0 (plano 4) já apaga `<exe>.old`/`.new` em `limpar_temporarios` e lê `"light"`/`"dark"` em `aparencia/tema` como `"claro"`/`"escuro"`.

- `requirements.txt`: `tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.3.0`.
- `build.ps1` no modelo do `Send_Agregados\build.ps1` (`-Python`): `$nome = "EnviadorEmails"`, `--icon assets\EnviadorEmails.ico`, `--collect-data tcm_ui --collect-data enviador_pdf_xml --hidden-import msal --hidden-import msal_extensions`, os `--exclude-module` do `.spec` atual (`tkinter`, `numpy`, `PySide6.QtWebEngineCore`, `PySide6.QtWebEngineWidgets`, `PySide6.QtQml`, `PySide6.QtQuick`, `PySide6.QtPdf`, `PySide6.QtMultimedia`, `PySide6.QtNetwork`), `dist\EnviadorEmails.exe.sha256` = `"<hash>  EnviadorEmails.exe\n"`; versão lida de `src\enviador_pdf_xml\__init__.py`.
- `release.yml` no modelo do `Send_Agregados` (2.0.1): instala `-r requirements.txt . pytest pytest-qt pyinstaller`; confere tag = `enviador_pdf_xml.__version__`; **mantém** o passo "Conferir valores fixos (login Microsoft)" com `from enviador_pdf_xml.modelo import pendencias_release`; testes offscreen; `./build.ps1 -Python python`; publica `EnviadorEmails.exe` + `EnviadorEmails.exe.sha256`.
- README: o que faz, uso (janela, arrastar arquivos, `python -m enviador_pdf_xml`), onde ficam os dados (sem alterar nada), desenvolver (`.venv` + `..\Tcm-ui` editável ou `-r requirements.txt`), lançar versão, módulo da casca (grupo `SF-EnviadorPDFXML`).
- [ ] Step 1: testes que falham — `test_build_usa_nome_do_exe` (`build.ps1`, `release.yml` e `MODULO.nome_exe` usam `EnviadorEmails.exe`), `test_sha256_legivel_pelos_dois_atualizadores` (conteúdo no formato acima: `split()[0]` do 1.0.0 e a regex do `tcm_ui.atualizador` dão o mesmo hash), `test_tema_antigo_e_lido` (QSettings `.ini` temporário com `aparencia/tema = dark` → `tema.configurar` resulta em `escuro`; confirma que a regra do `tcm-ui` cobre o Enviador), `test_workflow_confere_login_e_versao` (texto do `release.yml` contém `pendencias_release` e `__version__`).
- [ ] Step 2: `powershell -File build.ps1` (venv do repositório com `..\Tcm-ui` editável) gera `dist\EnviadorEmails.exe`; rodar com `ENVIADOR_DADOS` temporário e `QT_QPA_PLATFORM=offscreen` por alguns segundos e fechar (sem erro no log). O controlador confere a janela real (capturas pelo Python, nunca da tela).
- [ ] Step 3: conferência manual do Erik (não automatizável): abrir o `.exe` novo **sem** `ENVIADOR_DADOS` e ver a própria conta já conectada e o Para/Cco/assunto de antes; envio real só se ele quiser.
- [ ] Step 4: não commitar.

---

### Task 5: casca 1.2.0 com o Enviador

**Files (em `C:\Users\erik.freitas\Projetos\Sistema-Financeiro`):** Modify `requirements.txt`, `requirements-local.txt`, `build.ps1` (só a linha do `-Local`), `pyproject.toml`, `src/sistema_financeiro/__init__.py`, `README.md`, `CLAUDE.md`; tests.

- `requirements.txt`: `tcm-ui@v1.3.0`, `robo-agregado@v2.0.1`, `mesclador@v3.0.0`, `enviador-pdf-xml @ git+https://github.com/ErikDeFreitas/pdf-xml-mailer@v2.0.0`. `pyproject.toml`: `tcm-ui>=1.3.0`. `__version__ = "1.2.0"`.
- `-Local`/`requirements-local.txt`: acrescentar `../pdf-xml-mailer` aos repositórios vizinhos.
- `descoberta.ORDEM` já tem `enviador_pdf_xml` (nada a mudar).
- Testes: `verificar_modulos()` com os três módulos instalados → 0; ordem na barra: RoboAgregado, Mesclador de PDFs, Enviador de PDF + XML; `test_args_pyinstaller_inclui_enviador` (`--collect-all enviador_pdf_xml` e `--copy-metadata enviador-pdf-xml`); com `SF_GRUPOS_DEV="SF-EnviadorPDFXML"` só o Enviador aparece.
- [ ] Step 1: venv da casca com os cinco repositórios locais editáveis; suíte passa.
- [ ] Step 2: `powershell -File build.ps1 -Local` → `dist\SistemaFinanceiro.exe`, `--verificar` OK com os três módulos (confere que `msal`/`msal_extensions` entraram no `.exe`). O controlador confere a janela (capturas pelo Python com `SF_GRUPOS_DEV`), incluindo tema escuro na tela do Enviador e nos dois diálogos.
- [ ] Step 3: README (grupo `SF-EnviadorPDFXML`), `CLAUDE.md` ("Onde paramos"; ordem do "Salvar versão": Tcm-ui v1.3.0 → pdf-xml-mailer v2.0.0 → Sistema-Financeiro v1.2.0, depois das tags do plano 4; a TI cria `SF-EnviadorPDFXML`; a tag v2.0.0 chega a todos os usuários do avulso, então só depois da Task 4 Step 3).
- [ ] Step 4: não commitar.

---

### Task 6 (acrescentada em 24/11 por decisão do Erik): atualização automática padronizada no tcm-ui 1.3.0

**Decisão do Erik:** em todos os sistemas a atualização avisa que vai atualizar, mostra a barra de progresso do download e reinicia — sem pedir permissão.

**Files (em `C:\Users\erik.freitas\Projetos\Tcm-ui`):** Modify `src/tcm_ui/atualizador.py`, `src/tcm_ui/atualizacao_ui.py`, `README.md`, `src/tcm_ui/demo.py` (se mostrar o fluxo), tests.

**Interfaces — Produces:**
- `atualizador.baixar_e_verificar(info, destino, progresso: Callable[[int, int], None] | None = None)` — chama `progresso(lidos, total)` a cada bloco (`total` do `Content-Length` ou `info["tamanho"]`, 0 se desconhecido); resto igual (SHA-256, limites, `MZ`, apaga se falhar).
- `atualizacao_ui.VerificadorAtualizacao` (mesma assinatura e `iniciar()`): ao achar versão nova, **na thread da interface**: se `janela.modulos_com_tarefa()` → não atualiza agora (log; tenta na próxima abertura). Senão abre `DialogoAtualizacao` (modal, sem botão de fechar/cancelar; Esc e o X não fecham): título "Atualização", texto `"Atualizando para a versão {versao}. O programa será reiniciado ao terminar."`, `BarraProgresso` (indeterminada até saber o total) e texto `"{x} de {y} MB"`. O download roda numa thread e manda o progresso por sinal. Ao terminar → `aplicar_e_reiniciar` (mesmo tratamento de erro de hoje: `ErroAtualizacao` → aviso "continuará na versão atual"; `OSError` no reinício → aviso "abra-o novamente"). Falha no download → fecha o diálogo e mostra `Modal.informar(..., "perigo")` com a mensagem segura; o programa continua.
- Sem o `Modal.informar("Nova versão ... instalada")` de antes (o diálogo já avisou).

- [ ] Step 1: testes que falham — `test_baixar_reporta_progresso` (servidor falso/`_abrir` falso: chamadas crescentes, última = total), `test_com_tarefa_nao_atualiza` (`modulos_com_tarefa` → `["X"]`: nenhum diálogo, nada baixado), `test_dialogo_mostra_versao_e_progresso` (sinal de progresso atualiza barra e texto MB), `test_dialogo_nao_fecha_com_esc`, `test_falha_no_download_avisa_e_continua` (`ErroAtualizacao` → diálogo fecha, `Modal.informar` com tom perigo, `aplicar_e_reiniciar` não chamado), `test_sucesso_chama_aplicar_e_reiniciar` (falso; não reinicia de verdade). Nada de rede real: `_abrir`/`buscar_atualizacao` falsos.
- [ ] Step 2: falhar; Step 3: implementar; Step 4: suítes do Tcm-ui, pdf-merge, Sistema-Financeiro e Send_Agregados passam (usam `..\Tcm-ui` editável).
- [ ] Step 5: README "Novidades da 1.3.0" descreve o novo fluxo. Não commitar.
