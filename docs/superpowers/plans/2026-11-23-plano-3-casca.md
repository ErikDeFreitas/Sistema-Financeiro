# Plano 3 — Casca do Sistema Financeiro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o programa `SistemaFinanceiro.exe`: uma janela com barra lateral que mostra só os sistemas liberados pelos grupos `SF-*` do AD, começando só com o RoboAgregado.

**Architecture:** Pacote `sistema_financeiro` (layout `src/`) neste repositório. A casca descobre os módulos pelo entry point `sistema_financeiro.modulos`, filtra pelos grupos do token do Windows e entrega a lista à `tcm_ui.janela.JanelaPrincipal` (modo `"casca"`), que já faz carregamento preguiçoso, isolamento de erro e confirmação ao fechar. Log via `tcm_ui.registro.configurar_log`, atualização via `tcm_ui.atualizacao_ui.VerificadorAtualizacao`.

**Tech Stack:** Python 3.13, PySide6, pywin32 (`win32security`), tcm-ui 1.1.0, robo-agregado 2.0.0, pytest + pytest-qt (offscreen), PyInstaller `--onefile --windowed`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md` (seções 5.3, 5.5, 5.6, 5.7 e 7).

## Global Constraints

- **Sem commit, push, tag ou release** até o Erik dizer "Salvar versão". Nenhum passo deste plano commita.
- Repositório público: não escrever nos docs quem é admin do domínio nem detalhes sensíveis da rede.
- Repositórios em `C:\Users\erik.freitas\Projetos\`; pastas do FileServer não são tocadas.
- Versão da casca: `1.0.0`, em `src/sistema_financeiro/__init__.py` (`__version__`), commitada igual à tag.
- Grupos: `SF-RoboAgregado`, `SF-Mesclador`, `SF-EnviadorPDFXML`, `SF-RenomeadorCTE`, `SF-Catraca`, `SF-Admin` (vê todos). Comparação pelo nome sem domínio, sem diferenciar maiúsculas/minúsculas.
- Grupos lidos do **token do Windows** (`win32security.GetTokenInformation(..., TokenGroups)` + `LookupAccountSid`); não consulta o AD pela rede.
- `SF_GRUPOS_DEV="SF-Mesclador;SF-Catraca"` substitui o token **só quando não está congelado** (`sys.frozen` ausente).
- Tela sem acesso: título `Você não tem acesso a nenhum sistema.`, texto com o usuário (para a TI saber quem liberar).
- Rodapé da barra: usuário do Windows (`TCMSP\fulano`) e `Versão <versao>`.
- Só a casca chama `tema.aplicar(app)`; tema guardado em `QSettings("TCM", "SistemaFinanceiro")`.
- Log da casca: `%LOCALAPPDATA%\TCM\SistemaFinanceiro\logs\sistema_financeiro.log`; módulos usam `sistema_financeiro.<id>` (já feito pela `JanelaPrincipal`).
- Atualizador: repositório `ErikDeFreitas/Sistema-Financeiro`, executável `SistemaFinanceiro.exe`. Dentro da casca os atualizadores dos módulos não rodam.
- Release: `SistemaFinanceiro.exe` + `SistemaFinanceiro.exe.sha256` (formato `"<hash>  SistemaFinanceiro.exe\n"`); workflow falha se a tag ≠ `__version__`.
- Ordem na barra lateral: `robo_agregado`, `mesclador`, `enviador_pdf_xml`, `renomeador_cte`, `sistema_catraca`; desconhecidos depois, por id.

## Review Focus

1. **Um SID do token que não resolve** (offline, grupo apagado, SID de capacidade): `LookupAccountSid` lança erro → ignorar só aquele SID; os outros grupos continuam valendo. Teste em `test_acesso.py`.
2. **Módulo que não importa** (dependência faltando, erro no `modulo.py`, objeto que não é `Modulo`): os outros módulos continuam aparecendo e o erro vai para o log. Teste em `test_descoberta.py`.
3. **Leitura do token falha inteira**: o programa abre na tela "sem acesso" e registra a exceção, sem fechar. Teste em `test_acesso.py`.
4. **Última página salva pertence a um sistema que o usuário perdeu**: abre a primeira página permitida. Teste em `test_app.py`.
5. **`.exe` gerado sem os dados/metadados de um módulo** (entry point não encontrado, `.qss` faltando): o build falha em vez de publicar. Coberto pelo `--verificar` da Task 3.

---

### Task 1: Pacote da casca e controle de acesso

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `src/sistema_financeiro/__init__.py`, `src/sistema_financeiro/acesso.py`
- Test: `tests/conftest.py`, `tests/test_acesso.py`

**Interfaces:**
- Produces (em `sistema_financeiro.acesso`):
  - `GRUPO_ADMIN = "SF-Admin"`
  - `grupos_do_token() -> set[str]` — nomes dos grupos do token do processo, sem domínio.
  - `grupos_do_usuario(*, congelado: bool | None = None, ambiente: Mapping[str, str] | None = None, leitor: Callable[[], set[str]] = grupos_do_token) -> set[str]`
  - `permitidos(modulos: Sequence[Modulo], grupos: Iterable[str]) -> list[Modulo]`
  - `usuario_windows(ambiente: Mapping[str, str] | None = None) -> str`

- [ ] **Step 1: Criar o pacote**

`pyproject.toml` no modelo do `Send_Agregados`: `name = "sistema-financeiro"`, versão dinâmica de `sistema_financeiro.__version__`, `requires-python = ">=3.11"`, `dependencies = ["tcm-ui", "pywin32; sys_platform == 'win32'"]` (as versões fixas ficam no `requirements.txt` da Task 3), extra `dev = ["pytest", "pytest-qt"]`, `testpaths = ["tests"]`. `__init__.py`: `__version__ = "1.0.0"`. `.gitignore`: `.venv/`, `build/`, `dist/`, `*.egg-info/`, `.pytest_cache/`, `__pycache__/`, `.superpowers/`.

Venv de desenvolvimento (os tags `Tcm-ui v1.1.0` e `Send_Agregados v2.0.0` ainda não existem; usar os clones locais):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ..\Tcm-ui -e ..\Send_Agregados -e ".[dev]"
```

`tests/conftest.py`: `QT_QPA_PLATFORM=offscreen`; fixture autouse que aponta `SISTEMA_FINANCEIRO_DADOS` e `ROBO_AGREGADO_DADOS` para `tmp_path`, define `SMTP_USUARIO`/`SMTP_SENHA` falsos e apaga `SF_GRUPOS_DEV`; QSettings em arquivos `.ini` (mesma técnica `_QSettingsIni` do `Send_Agregados/tests/conftest.py`), para os testes nunca gravarem no registro.

- [ ] **Step 2: Escrever os testes que falham** (`tests/test_acesso.py`)

```python
def test_dev_substitui_token_quando_nao_congelado():
    g = grupos_do_usuario(congelado=False, ambiente={"SF_GRUPOS_DEV": " SF-Mesclador ; SF-Catraca;"},
                          leitor=lambda: pytest.fail("não deve ler o token"))
    assert g == {"SF-Mesclador", "SF-Catraca"}

def test_dev_ignorado_quando_congelado():
    g = grupos_do_usuario(congelado=True, ambiente={"SF_GRUPOS_DEV": "SF-Admin"}, leitor=lambda: {"Users"})
    assert g == {"Users"}

def test_falha_na_leitura_do_token_vira_conjunto_vazio(caplog):
    def quebra(): raise OSError("sem token")
    assert grupos_do_usuario(congelado=True, ambiente={}, leitor=quebra) == set()
    assert "sem token" in caplog.text

def test_permitidos_por_grupo_sem_caixa_e_sem_dominio():
    # módulos falsos a, b, c com grupo_ad SF-A, SF-B, SF-C (fábrica em conftest)
    assert [m.id for m in permitidos([a, b, c], {"TCMSP\\sf-b", "sf-c"})] == ["b", "c"]

def test_admin_ve_todos_na_ordem():
    assert [m.id for m in permitidos([a, b, c], {"sf-admin"})] == ["a", "b", "c"]

def test_sem_grupo_nenhum_modulo():
    assert permitidos([a, b, c], {"Users"}) == []

def test_sid_que_nao_resolve_e_ignorado(monkeypatch):
    # falsificar win32security: 3 SIDs; LookupAccountSid lança pywintypes.error no 2º
    # e devolve ("SF-A", "TCMSP", tipo) / ("Users", "BUILTIN", tipo) nos outros
    assert grupos_do_token() == {"SF-A", "Users"}

def test_grupo_so_para_negacao_e_ignorado(monkeypatch):
    # SID com atributo SE_GROUP_USE_FOR_DENY_ONLY não entra no conjunto

@pytest.mark.skipif(sys.platform != "win32", reason="token só no Windows")
def test_token_real_devolve_nomes():
    g = grupos_do_token()
    assert g and all(isinstance(n, str) and "\\" not in n for n in g)

def test_usuario_windows_com_dominio():
    assert usuario_windows({"USERDOMAIN": "TCMSP", "USERNAME": "fulano"}) == "TCMSP\\fulano"
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest tests/test_acesso.py -v` — Expected: FAIL (`ModuleNotFoundError: sistema_financeiro.acesso`).

- [ ] **Step 4: Implementar `acesso.py`**

- `grupos_do_token`: `OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY)` → `GetTokenInformation(token, TokenGroups)` → para cada `(sid, atributos)` sem `SE_GROUP_USE_FOR_DENY_ONLY`, `LookupAccountSid(None, sid)[0]`; `pywintypes.error` naquele SID → pula. Importar `win32security`/`win32api` dentro da função (o módulo importa em qualquer plataforma).
- `grupos_do_usuario`: `congelado` padrão `getattr(sys, "frozen", False)`; `ambiente` padrão `os.environ`. Se não congelado e `SF_GRUPOS_DEV` presente → itens separados por `;`, sem espaços, não vazios. Senão `leitor()`; qualquer `Exception` → `log.exception(...)` em `logging.getLogger("sistema_financeiro")` e `set()`.
- `permitidos`: normaliza cada grupo (parte depois do último `\`, `casefold()`); `SF-Admin` → todos; senão os de `grupo_ad.casefold()` no conjunto. Mantém a ordem recebida.
- `usuario_windows`: `f"{USERDOMAIN}\\{USERNAME}"`; sem `USERDOMAIN` → só `getpass.getuser()`.

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv\Scripts\python -m pytest -v` — Expected: todos PASS.

- [ ] **Step 6: Não commitar** (regra do Erik). Registrar no relatório os arquivos criados.

---

### Task 2: Descoberta dos módulos e janela da casca

**Files:**
- Create: `src/sistema_financeiro/descoberta.py`, `src/sistema_financeiro/app.py`, `main.py`
- Test: `tests/test_descoberta.py`, `tests/test_app.py`

**Interfaces:**
- Consumes: Task 1 (`grupos_do_usuario`, `permitidos`, `usuario_windows`); `tcm_ui.janela.JanelaPrincipal(modulos, *, nome_app, icone_app, usuario, modo, configuracoes, rodape, sem_modulos)`; `tcm_ui.registro.configurar_log(pasta, nome)`; `tcm_ui.atualizacao_ui.VerificadorAtualizacao(janela, repositorio, nome_exe, versao).iniciar()`; `tcm_ui.themes.tema.configurar/aplicar`; `tcm_ui.components.CartaoErro`, `EstadoVazio`.
- Produces:
  - `descoberta.GRUPO_ENTRY_POINT = "sistema_financeiro.modulos"`
  - `descoberta.ORDEM = ("robo_agregado", "mesclador", "enviador_pdf_xml", "renomeador_cte", "sistema_catraca")`
  - `descoberta.carregar_modulos(pontos: Iterable[EntryPoint] | None = None) -> list[Modulo]`
  - `app.NOME_APP = "Sistema Financeiro"`, `app.ICONE = "painel"`, `app.REPOSITORIO = "ErikDeFreitas/Sistema-Financeiro"`, `app.NOME_EXE = "SistemaFinanceiro.exe"`
  - `app.pasta_dados() -> Path` — `SISTEMA_FINANCEIRO_DADOS` ou `%LOCALAPPDATA%\TCM\SistemaFinanceiro`
  - `app.criar_janela(modulos: Sequence[Modulo], grupos: Iterable[str], usuario: str, configuracoes: QSettings) -> JanelaPrincipal`
  - `app.verificar_modulos() -> int` — 0 se todo módulo instalado abre todas as páginas sem `CartaoErro`, 1 senão (usado pelo build da Task 3)
  - `app.rodar(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_descoberta.py` (entry points falsos: objetos com `.name` e `.load()`):

```python
def test_ordem_fixa_e_desconhecidos_por_id_no_fim():
    ids = [m.id for m in carregar_modulos([ep("zeta"), ep("mesclador"), ep("alfa"), ep("robo_agregado")])]
    assert ids == ["robo_agregado", "mesclador", "alfa", "zeta"]

def test_modulo_que_nao_importa_nao_derruba_os_outros(caplog):
    ids = [m.id for m in carregar_modulos([ep_que_lanca("mesclador", ImportError("pandas")), ep("robo_agregado")])]
    assert ids == ["robo_agregado"] and "mesclador" in caplog.text

def test_objeto_que_nao_e_modulo_e_ignorado(caplog): ...   # load() devolve "texto" → fora + log

def test_id_repetido_fica_o_primeiro(caplog): ...

def test_robo_agregado_instalado_pelo_entry_point():
    assert "robo_agregado" in [m.id for m in carregar_modulos()]
```

`tests/test_app.py`:

```python
def test_sem_acesso_mostra_usuario(qtbot, configuracoes):
    jan = criar_janela([robo], {"Users"}, "TCMSP\\fulano", configuracoes); qtbot.addWidget(jan)
    vazio = jan.findChild(EstadoVazio)
    assert "Você não tem acesso a nenhum sistema." in textos(vazio) and "TCMSP\\fulano" in textos(vazio)

def test_rodape_tem_usuario_e_versao(qtbot, configuracoes): ...   # "TCMSP\\fulano", "Versão 1.0.0"

def test_ultima_pagina_de_sistema_perdido_abre_a_primeira_permitida(qtbot, configuracoes):
    configuracoes.setValue("navegacao/ultima", "b:p")
    jan = criar_janela([a, b], {"SF-A"}, "u", configuracoes)
    assert jan.pagina_atual == ("a", "p")

def test_robo_agregado_abre_na_casca(qtbot, configuracoes):
    jan = criar_janela(carregar_modulos(), {"SF-RoboAgregado"}, "u", configuracoes); qtbot.addWidget(jan)
    assert jan.pagina_atual == ("robo_agregado", "extrato") and not jan.findChildren(CartaoErro)

def test_modulo_com_erro_vira_cartao_e_o_resto_funciona(qtbot, configuracoes): ...  # criar() lança

def test_verificar_modulos_ok():
    assert verificar_modulos() == 0

def test_verificar_modulos_falha_se_algum_quebra(monkeypatch):   # carregar_modulos devolve um que lança
    assert verificar_modulos() == 1

def test_pasta_dados_respeita_variavel(monkeypatch, tmp_path): ...
```

- [ ] **Step 2: Rodar e ver falhar** — `.venv\Scripts\python -m pytest tests/test_descoberta.py tests/test_app.py -v` → FAIL (módulos não existem).

- [ ] **Step 3: Implementar**

- `carregar_modulos`: padrão `importlib.metadata.entry_points(group=GRUPO_ENTRY_POINT)`. Cada `load()` em `try/except Exception` → `log.exception("Não foi possível carregar o módulo %s", ep.name)`; não-`Modulo` → `log.error`, ignora; id repetido → `log.error`, fica o primeiro. Ordena por `(índice em ORDEM, id)` com desconhecidos depois de todos de `ORDEM`. Logger: `sistema_financeiro`.
- `criar_janela`: `JanelaPrincipal(permitidos(modulos, grupos), nome_app=NOME_APP, icone_app=ICONE, usuario=usuario, modo="casca", configuracoes=configuracoes, rodape=[usuario, f"Versão {__version__}"], sem_modulos=("Você não tem acesso a nenhum sistema.", f"Fale com a TI e informe o seu usuário: {usuario}"))`.
- `verificar_modulos`: `QApplication` (reaproveita a existente), monta `criar_janela(carregar_modulos(), {GRUPO_ADMIN}, "verificacao", QSettings(<arquivo .ini temporário>, IniFormat))`, abre cada `(modulo, pagina)` com `janela.abrir`, falha se a lista de módulos estiver vazia ou houver `CartaoErro`; loga o resultado; fecha a janela sem `closeEvent` interativo (`deleteLater`).
- `rodar`: `configurar_log(pasta_dados(), "sistema_financeiro")`; se `"--verificar"` em `argv` → `return verificar_modulos()`; `QApplication`, `setOrganizationName("TCM")`, `setApplicationName("SistemaFinanceiro")`; `tema.configurar("TCM", "SistemaFinanceiro")`; `tema.aplicar(app)`; usuário, grupos, módulos; log INFO com usuário, quantidade de grupos e ids permitidos (sem listar os grupos); `criar_janela(..., QSettings("TCM", "SistemaFinanceiro"))`; `VerificadorAtualizacao(janela, REPOSITORIO, NOME_EXE, __version__).iniciar()`; `show`; `exec`.
- `main.py`: `sys.exit(rodar())` com `from sistema_financeiro.app import rodar`.

- [ ] **Step 4: Rodar e ver passar** — `.venv\Scripts\python -m pytest -v` → todos PASS.

- [ ] **Step 5: Conferir rodando pelo Python** (sem tocar dados reais):

```powershell
$env:SISTEMA_FINANCEIRO_DADOS = (New-Item -ItemType Directory "$env:TEMP\sf_dev_$(Get-Random)").FullName
$env:ROBO_AGREGADO_DADOS = (New-Item -ItemType Directory "$env:TEMP\robo_dev_$(Get-Random)").FullName
$env:SF_GRUPOS_DEV = "SF-RoboAgregado"; .venv\Scripts\python main.py
```

Esperado: janela "Sistema Financeiro" com "Extrato de fretes" aberta; rodapé com usuário e `Versão 1.0.0`; log em `$env:SISTEMA_FINANCEIRO_DADOS\logs\sistema_financeiro.log`. Com `SF_GRUPOS_DEV="Nada"` → tela sem acesso. (O controlador faz esta conferência com captura de tela.)

- [ ] **Step 6: Não commitar.**

---

### Task 3: Build, Release e documentação

**Files:**
- Create: `requirements.txt`, `requirements-local.txt`, `build.ps1`, `ferramentas/args_pyinstaller.py`, `.github/workflows/release.yml`, `README.md`
- Test: `tests/test_args_pyinstaller.py`
- Modify: `CLAUDE.md` (seção "Onde paramos"), spec seção 5.7 se algum detalhe mudar

**Interfaces:**
- Consumes: `app.verificar_modulos` via `SistemaFinanceiro.exe --verificar`; `descoberta.GRUPO_ENTRY_POINT`.
- Produces: `ferramentas/args_pyinstaller.py` imprime um argumento por linha: `--collect-data tcm_ui`, e para cada entry point do grupo, `--collect-all <pacote do módulo>` e `--copy-metadata <distribuição>`.

- [ ] **Step 1: Teste que falha** (`tests/test_args_pyinstaller.py`): rodar o script com `subprocess` e o Python do venv; a saída contém `--collect-data`/`tcm_ui`, `--collect-all`/`robo_agregado`, `--copy-metadata`/`robo-agregado` (pares em linhas seguidas).

- [ ] **Step 2: Implementar `args_pyinstaller.py`** — pacote = `ep.value.split(":")[0].split(".")[0]`; distribuição = `ep.dist.name`. Só stdlib.

- [ ] **Step 3: Requisitos**

`requirements.txt` (Release):

```
tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.1.0
robo-agregado @ git+https://github.com/ErikDeFreitas/Send_Agregados@v2.0.0
```

`requirements-local.txt` (antes das tags existirem; caminhos relativos à raiz do repositório):

```
../Tcm-ui
../Send_Agregados
```

- [ ] **Step 4: `build.ps1`** — `param([string]$Python, [string]$Requisitos = "requirements.txt")`, `Set-Location $PSScriptRoot`.
  - Sem `-Python`: recria `build\venv` limpo, instala `-r $Requisitos`, `.`, `pytest pytest-qt pyinstaller`, roda `pytest -q` com `QT_QPA_PLATFORM=offscreen` (falhou → sai 1).
  - PyInstaller: `--noconfirm --onefile --windowed --name SistemaFinanceiro`, os argumentos de `args_pyinstaller.py`, mais as importações ocultas que os módulos precisam e o PyInstaller não enxerga (`--hidden-import openpyxl --hidden-import pythoncom --hidden-import win32com.client`, com comentário dizendo de qual módulo vem cada uma), os mesmos `--exclude-module` do RoboAgregado, `--workpath build --specpath build --distpath dist main.py`.
  - Mesma checagem de "nenhum arquivo novo" do `Send_Agregados\build.ps1`.
  - **Verificação do `.exe`**: com `SISTEMA_FINANCEIRO_DADOS`, `ROBO_AGREGADO_DADOS` em pastas temporárias, `SMTP_USUARIO`/`SMTP_SENHA` falsos e `QT_QPA_PLATFORM=offscreen`, `Start-Process dist\SistemaFinanceiro.exe --verificar -PassThru`, espera até 180 s; código ≠ 0 ou tempo esgotado → mata o processo, mostra o log da pasta temporária e sai 1.
  - Grava `dist\SistemaFinanceiro.exe.sha256` (`"<hash>  SistemaFinanceiro.exe\n"`), lê a versão de `src\sistema_financeiro\__init__.py`, mostra o resumo como no RoboAgregado.

- [ ] **Step 5: Gerar e conferir** — `powershell -File build.ps1 -Requisitos requirements-local.txt` → `dist\SistemaFinanceiro.exe` e `.sha256`, verificação OK. O controlador abre o `.exe` (pasta de dados temporária) e confere a tela "sem acesso" com o usuário (os grupos `SF-*` ainda não existem no AD).

- [ ] **Step 6: `release.yml`** — cópia do `Send_Agregados/.github/workflows/release.yml` com: `pip install -r requirements.txt . pytest pytest-qt pyinstaller`; conferência da tag com `sistema_financeiro.__version__`; `./build.ps1 -Python python`; artefatos `dist/SistemaFinanceiro.exe` e `.sha256`.

- [ ] **Step 7: README** — o que é; como pedir acesso (grupo `SF-*` por sistema, `SF-Admin` vê todos; vale só depois de sair e entrar de novo no Windows); onde fica o log; como desenvolver (`.venv`, `SF_GRUPOS_DEV` só fora do `.exe`); como adicionar um sistema (linha no `requirements.txt` + id em `descoberta.ORDEM` + importações ocultas no `build.ps1`, se houver); como lançar versão (subir `__version__`, tag `vX.Y.Z`); limite: é uma barreira organizacional, não proteção dos dados. Nada de nomes de admin ou detalhes da rede.

- [ ] **Step 8: Atualizar `CLAUDE.md`** ("Onde paramos": plano 3 implementado, não salvo; ordem do "Salvar versão": Tcm-ui `v1.1.0` → Send_Agregados `v2.0.0` → Sistema-Financeiro `v1.0.0`; a TI cria os grupos `SF-*` antes de distribuir).

- [ ] **Step 9: Não commitar.**
