# Plano 2 — RoboAgregado como módulo do tcm-ui

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** O RoboAgregado (`ErikDeFreitas/Send_Agregados`) vira o pacote `robo_agregado`, usa o `tcm-ui`, expõe `MODULO` pelo entry point da casca e continua gerando o `RoboAgregado.exe` avulso com os mesmos dados e o mesmo comportamento.

**Architecture:** Primeiro o `tcm-ui` ganha o que o avulso do RoboAgregado precisa e o plano 1 deixou pendente (v1.1.0). Depois o `Send_Agregados` passa para o layout `src/robo_agregado/`: um módulo leve (`dados.py`, `modulo.py`, sem pandas) que a casca importa ao abrir, e a tela (`tela.py`, vinda do `app.py`) criada só em `criar`. A janela, o tema e o atualizador saem do RoboAgregado e passam a vir do `tcm-ui`.

**Tech Stack:** Python 3.13, PySide6 (via `tcm-ui`), pandas, openpyxl, pywin32, pytest + pytest-qt (offscreen), PyInstaller, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md` (seções 5.2, 5.4, 5.6, 5.7, 6, 7). Pendências herdadas: `.superpowers/sdd/2026-11-19-plano-1-tcm-ui/progress.md` (M3, M5, M6, M7).

**Repositórios** (ambos em `C:\Users\erik.freitas\Projetos\`):
- `Tcm-ui` — Task 1.
- `Send_Agregados` — Tasks 2 a 4.

## Global Constraints

- **Sem commit, push, tag ou release** em nenhuma task. Só quando o Erik disser "Salvar versão". Os passos "Commit" do template viram "Sem commit".
- Versões: `tcm-ui` **1.1.0**; `robo-agregado` **2.0.0** (`__version__` em `src/robo_agregado/__init__.py`, commitado igual à tag).
- Dependência no `pyproject.toml` do RoboAgregado: `tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.1.0`. Como a tag ainda não existe, o desenvolvimento usa o `Tcm-ui` local (ver "Ambiente" na Task 2).
- `MODULO`: `id="robo_agregado"`, `nome="RoboAgregado"`, `icone="caminhao"`, `grupo_ad="SF-RoboAgregado"`, `repositorio="ErikDeFreitas/Send_Agregados"`, `nome_exe="RoboAgregado.exe"`, `pasta_dados=%LOCALAPPDATA%\RoboAgregado`.
- Página única: `Pagina("extrato", "Extrato de fretes", "Envio dos extratos semanais aos agregados", "enviar")`.
- Entry point: `[project.entry-points."sistema_financeiro.modulos"] robo_agregado = "robo_agregado.modulo:MODULO"`.
- **Dados não mudam de lugar**: `config.ini`, `.env`, `log_envios.csv`, `preferencias.json` continuam em `%LOCALAPPDATA%\RoboAgregado\`.
- Tema no avulso continua em `QSettings("TCM", "RoboAgregado")` (= `MODULO.aplicacao_settings`); a preferência atual dos usuários é preservada.
- `robo_agregado.modulo` e `robo_agregado.dados` não importam pandas, PySide6 widgets do app, nem criam pastas/arquivos ao serem importados (a casca importa para todos os usuários).
- Módulo nunca chama `setStyleSheet` no `QApplication` nem `QSettings()` sem argumentos.
- Imports sempre absolutos (`from robo_agregado import ...`).
- Testes com `QT_QPA_PLATFORM=offscreen`; nunca escrevem no registro do Windows nem em `%LOCALAPPDATA%\RoboAgregado` real; nunca enviam e-mail.
- Os repositórios são públicos: nada de credenciais, e-mails reais ou dados de agregados em código, testes ou docs.

## Review Focus

1. **A casca importa `robo_agregado.modulo` para um usuário sem acesso** — esperado: nada de pandas carregado, nenhuma pasta criada. Teste na Task 3 (`test_modulo_e_leve`).
2. **Usuário fecha o programa (ou chega uma atualização) no meio de um envio** — esperado: `pode_fechar()` devolve False e a janela pede confirmação / adia a atualização. Teste na Task 3 (`test_pode_fechar_durante_envio`).
3. **Primeira execução numa máquina sem `%LOCALAPPDATA%\RoboAgregado`** — esperado: a pasta e o `config.ini` são criados a partir do pacote. Teste na Task 2 (`test_config_criado_na_primeira_execucao`).
4. **Usuário do `.exe` 1.3.3 atualiza para o 2.0.0** — esperado: mesmos dados; `config.ini` trocado pelo novo com cópia em `config.ini.bak` (mesma regra de hoje); `.env` e log intactos. Teste na Task 2 (`test_config_substituido_quando_versao_muda`).
5. **`[atualizacao] ativo = nao` no `config.ini`** — esperado: o avulso não procura atualização. Testes na Task 1 (`test_rodar_avulso_sem_atualizar`) e na Task 2 (`test_atualizacao_ativa`).

---

### Task 1: tcm-ui 1.1.0 — avulso configurável, log de erros e reinício seguro

Repositório: `C:\Users\erik.freitas\Projetos\Tcm-ui` (usar o `.venv` existente).

**Files:**
- Create: `src/tcm_ui/registro.py`
- Modify: `src/tcm_ui/avulso.py`, `src/tcm_ui/atualizacao_ui.py`, `src/tcm_ui/janela.py` (`closeEvent`), `src/tcm_ui/__init__.py`, `pyproject.toml`, `README.md`
- Test: `tests/test_registro.py`, `tests/test_avulso.py`, `tests/test_atualizador.py` (ou o arquivo que já testa `VerificadorAtualizacao`), `tests/test_janela.py`

**Interfaces:**
- Produces:
  - `tcm_ui.registro.configurar_log(pasta: Path, nome: str) -> Path` — cria `pasta/"logs"`, liga um `RotatingFileHandler` (`<nome>.log`, 1 MiB, 3 backups, UTF-8, formato `%(asctime)s %(levelname)s %(name)s: %(message)s`) no logger raiz em nível INFO, instala `sys.excepthook` e `threading.excepthook` que gravam a exceção com `logging.getLogger("tcm_ui").critical(..., exc_info=...)` (e chamam o hook anterior), e devolve o caminho do arquivo. Chamar duas vezes com o mesmo arquivo não duplica o handler. Se a pasta não puder ser criada (`OSError`), não lança: devolve o caminho e segue sem arquivo.
  - `tcm_ui.avulso.rodar_avulso(modulo: Modulo, argv: list[str] | None = None, *, atualizar: bool = True) -> int` — chama `configurar_log(modulo.pasta_dados, modulo.id)` antes de criar a janela; só cria/inicia o `VerificadorAtualizacao` se `atualizar`.
  - `JanelaPrincipal.closeEvent` aceito chama `self._configuracoes.sync()` (o `os._exit(0)` do atualizador não perde a última página/tema — pendência M3).
  - `VerificadorAtualizacao._ao_pronto`: se `aplicar_e_reiniciar` lançar `OSError` (o `Popen` do reinício falhou depois de a versão nova já estar no lugar — pendência M5), mostra `Modal.informar(janela, "Atualização", "A nova versão foi instalada, mas o programa não pôde ser reiniciado. Abra-o novamente.", "perigo")`, registra com `_log.exception` e segue para `close()` + `os._exit(0)`.
  - `__version__ = "1.1.0"` e `version = "1.1.0"` no `pyproject.toml`.

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_registro.py
def test_configurar_log_grava_em_arquivo(tmp_path):
    caminho = configurar_log(tmp_path, "teste_log")
    assert caminho == tmp_path / "logs" / "teste_log.log"
    logging.getLogger("x").warning("olá")
    for h in logging.getLogger().handlers: h.flush()
    assert "olá" in caminho.read_text(encoding="utf-8")

def test_configurar_log_nao_duplica_handler(tmp_path):
    configurar_log(tmp_path, "dup"); configurar_log(tmp_path, "dup")
    alvo = str(tmp_path / "logs" / "dup.log")
    assert sum(getattr(h, "baseFilename", None) == alvo for h in logging.getLogger().handlers) == 1

def test_excecao_nao_tratada_vai_para_o_log(tmp_path):
    caminho = configurar_log(tmp_path, "exc")
    try: raise RuntimeError("falha-x")
    except RuntimeError: sys.excepthook(*sys.exc_info())
    for h in logging.getLogger().handlers: h.flush()
    assert "falha-x" in caminho.read_text(encoding="utf-8")
```

Uma fixture autouse no próprio arquivo remove os handlers adicionados e restaura `sys.excepthook`/`threading.excepthook` ao fim de cada teste.

```python
# tests/test_avulso.py (acrescentar; seguir o padrão de monkeypatch já usado no arquivo)
def test_rodar_avulso_sem_atualizar(...):  # VerificadorAtualizacao trocado por um falso que conta instâncias
    rodar_avulso(modulo, atualizar=False)   # com app.exec trocado como nos testes existentes
    assert falso.criados == 0

def test_rodar_avulso_configura_log(...):   # configurar_log trocado por um falso
    rodar_avulso(fazer_modulo(pasta_dados=tmp_path))
    assert chamadas == [(tmp_path, "falso")]
```

```python
# teste do VerificadorAtualizacao (arquivo onde ele já é testado)
def test_reinicio_falhou_avisa_e_fecha(...):
    # aplicar_e_reiniciar lança OSError; Modal.informar e os._exit trocados por falsos
    verificador._ao_pronto("9.9.9", str(tmp_path / "x.novo"))
    assert "não pôde ser reiniciado" in mensagens[0]
    assert saiu == [0]
```

```python
# tests/test_janela.py
def test_fechar_sincroniza_configuracoes(janela, fazer_modulo...):
    # configuracoes = objeto que registra chamadas de sync(); janela.close()
    assert sincronizou
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest -q`
Expected: os testes novos falham (`ModuleNotFoundError: tcm_ui.registro`, `TypeError: unexpected keyword 'atualizar'` etc.); os 75 antigos passam.

- [ ] **Step 3: Implementar** `registro.py` e as mudanças de `avulso.py`, `atualizacao_ui.py`, `janela.py`, versão 1.1.0.

- [ ] **Step 4: README** — documentar `atualizar=False`, o log em `<pasta_dados>\logs\<id>.log` e incluir na seção de exemplo `main.py` a forma com `atualizar=`.

- [ ] **Step 5: Rodar tudo**

Run: `.venv\Scripts\python -m pytest -q`
Expected: todos passam (75 + novos), sem warnings novos.

- [ ] **Step 6: Sem commit** (regra do Erik). A tag `v1.1.0` sai no "Salvar versão", **antes** da do RoboAgregado.

---

### Task 2: Pacote `robo_agregado` — layout `src/`, pasta de dados e `config.ini` embutido

Repositório: `C:\Users\erik.freitas\Projetos\Send_Agregados`.

**Ambiente** (uma vez, no início da task):
```
python -m venv .venv
.venv\Scripts\python -m pip install -e ..\Tcm-ui
.venv\Scripts\python -m pip install -e . --no-deps
.venv\Scripts\python -m pip install pandas openpyxl pywin32 pytest pytest-qt pyinstaller
```
(`--no-deps` porque a tag `v1.1.0` do `tcm-ui` ainda não existe no GitHub.) Confirmar que `.venv/` está no `.gitignore`.

**Files:**
- Create: `pyproject.toml`, `src/robo_agregado/__init__.py`, `src/robo_agregado/dados.py`, `tests/conftest.py`, `tests/test_dados.py`
- Move (`git mv`): `enviar_fretes.py` → `src/robo_agregado/enviar_fretes.py`; `config.ini` → `src/robo_agregado/config.ini`
- Delete: `versao.py`, `requirements.txt`
- Modify: `src/robo_agregado/enviar_fretes.py` (só o topo de pasta/config e o `from versao import VERSAO`), `src/robo_agregado/config.ini` (seção `[atualizacao]`)

**Interfaces:**
- Produces (`robo_agregado.dados`, só stdlib):
  - `NOME_PASTA = "RoboAgregado"`
  - `pasta_dados() -> Path` — `Path(os.environ["ROBO_AGREGADO_DADOS"])` se a variável existir; senão `Path(os.environ.get("LOCALAPPDATA") or Path.home()) / NOME_PASTA`. Vale para `.exe` e para `python` (mudança: antes, rodando pelo Python, os dados ficavam na pasta do código).
  - `PASTA: Path = pasta_dados()` — calculado no import, sem criar nada.
  - `preparar_pasta() -> Path` — cria `PASTA`; se `getattr(sys, "frozen", False)` **e** `Path(sys.executable).name.lower() == "roboagregado.exe"`, move `.env`, `log_envios.csv`, `preferencias.json` de ao lado do `.exe` para `PASTA` quando ainda não existirem lá (lógica de hoje, `enviar_fretes.py:34-44`, ignorando `OSError`). Dentro da casca nada é movido.
  - `CONFIG_EMBUTIDO` = `importlib.resources.files("robo_agregado") / "config.ini"` (substitui `sys._MEIPASS / "config.ini"`).
  - `atualizar_config_embutido(caminho: Path, versao: str) -> None` — mesma regra de `enviar_fretes.atualizar_config_embutido` de hoje (marca `config.versao`; se não existe ou a versão mudou, copia o atual para `config.ini.bak` e grava o embutido; `OSError` ignorado), agora com a versão como parâmetro e rodando também fora do `.exe`.
  - `garantir_config() -> Path` — `preparar_pasta()` + `atualizar_config_embutido(PASTA / "config.ini", __version__)`; devolve o caminho.
  - `atualizacao_ativa() -> bool` — `garantir_config()`, lê `[atualizacao] ativo` com `configparser` (`interpolation=None`, UTF-8); True se ausente ou em `("sim", "s", "true", "1")` sem diferenciar maiúsculas.
- `enviar_fretes`: `PASTA`, `ARQUIVO_*`, `PASTA_PREVIA` passam a vir de `dados.PASTA`; o bloco `if frozen` do topo sai; `carregar_config(caminho=None)` chama `dados.garantir_config()` quando `caminho` é o padrão (com `caminho` explícito, só lê). `atualizar_config_embutido` sai de `enviar_fretes`. `main()` (linha de comando) continua: `python -m robo_agregado.enviar_fretes --planilha ... --listar`.
- `config.ini`: em `[atualizacao]` fica só `ativo = sim`; remover `repositorio` (o repositório agora é `MODULO.repositorio`) e ajustar o comentário.
- `pyproject.toml`: `name = "robo-agregado"`, `dynamic = ["version"]` lido de `robo_agregado.__version__`, `requires-python = ">=3.11"`, dependências `tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.1.0`, `pandas`, `openpyxl`, `pywin32; sys_platform == 'win32'`; extra `dev = ["pytest", "pytest-qt"]`; entry point da Global Constraints; `package-data` `robo_agregado = ["config.ini"]`; `[tool.pytest.ini_options] testpaths = ["tests"]`.
- `tests/conftest.py` (antes de qualquer import do pacote): `QT_QPA_PLATFORM=offscreen`; `ROBO_AGREGADO_DADOS` apontando para uma pasta temporária da sessão (`tempfile.mkdtemp()`); `SMTP_USUARIO`/`SMTP_SENHA` com valores fictícios (senão a tela abre o diálogo de credenciais na criação e trava o teste); mesmo `_QSettingsIni` do conftest do `Tcm-ui` (QSettings em `.ini` temporário, nunca o registro).

- [ ] **Step 1: Ambiente, `git mv` dos arquivos, `pyproject.toml` e `__init__.py` (`__version__ = "2.0.0"`)**

- [ ] **Step 2: Escrever os testes que falham** (`tests/test_dados.py`)

```python
def test_pasta_padrao_em_localappdata(monkeypatch, tmp_path):
    monkeypatch.delenv("ROBO_AGREGADO_DADOS", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert dados.pasta_dados() == tmp_path / "RoboAgregado"

def test_pasta_pela_variavel(monkeypatch, tmp_path):
    monkeypatch.setenv("ROBO_AGREGADO_DADOS", str(tmp_path / "x"))
    assert dados.pasta_dados() == tmp_path / "x"

def test_config_criado_na_primeira_execucao(tmp_path):
    cfg = tmp_path / "nova" / "config.ini"; cfg.parent.mkdir()
    dados.atualizar_config_embutido(cfg, "2.0.0")
    assert "[email]" in cfg.read_text(encoding="utf-8")
    assert (tmp_path / "nova" / "config.versao").read_text(encoding="utf-8").strip() == "2.0.0"

def test_config_da_mesma_versao_nao_e_trocado(tmp_path):
    # cria com 2.0.0, edita o arquivo, chama de novo com 2.0.0 -> edição mantida

def test_config_substituido_quando_versao_muda(tmp_path):
    # config.ini com "editado" + config.versao "1.3.3"; chama com "2.0.0"
    # -> config.ini.bak contém "editado"; config.ini é o embutido; config.versao == "2.0.0"

def test_atualizacao_ativa(monkeypatch, tmp_path):
    # PASTA trocada para tmp_path; config.ini com [atualizacao] ativo = nao -> False
    # versão igual gravada em config.versao para o arquivo não ser trocado; sem a seção -> True

def test_migra_arquivos_de_ao_lado_do_exe(monkeypatch, tmp_path):
    # sys.frozen=True, sys.executable=tmp_path/"exe"/"RoboAgregado.exe", PASTA=tmp_path/"dados"
    # .env ao lado do exe -> preparar_pasta() -> está em dados/.env
    # repetir com executable "SistemaFinanceiro.exe" -> não move

def test_carregar_config_padrao_usa_pasta_de_dados():
    cfg = enviar_fretes.carregar_config()
    assert cfg["smtp"].get("servidor")
    assert (dados.PASTA / "config.ini").exists()  # PASTA = pasta temporária do conftest
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest -q`
Expected: FAIL (`robo_agregado.dados` não existe).

- [ ] **Step 4: Implementar `dados.py` e ajustar `enviar_fretes.py` e `config.ini`**

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv\Scripts\python -m pytest -q` → todos passam.
Run: `.venv\Scripts\python -m robo_agregado.enviar_fretes --help` → mostra a ajuda sem erro.

- [ ] **Step 6: Sem commit.**

---

### Task 3: Tela, instância e `MODULO`

**Files:**
- Create: `src/robo_agregado/tela.py`, `src/robo_agregado/instancia.py`, `src/robo_agregado/modulo.py`, `tests/test_modulo.py`, `tests/test_instancia.py`
- Delete: `app.py` (conteúdo vai para `tela.py`), `atualizador.py`, `design_system/` (pasta inteira)

**Interfaces:**
- Consumes: `robo_agregado.dados` (Task 2); `tcm_ui.modulo.{Modulo, Pagina, Contexto}`, `tcm_ui.components`, `tcm_ui.themes.{ESPACO, MARCA, TAMANHOS}`, `tcm_ui.icons`, `tcm_ui.janela.JanelaPrincipal` (Tcm-ui 1.1.0).
- Produces:
  - `robo_agregado.tela.DialogoCredenciais` — igual ao de `app.py`, imports trocados para `tcm_ui`.
  - `robo_agregado.tela.TelaExtrato(tcm_ui.components.Pagina)` — `__init__(self, contexto: Contexto)`; é o `App` de hoje sem janela: monta no `self.conteudo` os mesmos 4 blocos (indicadores, configuração, agregados com stretch 1, registro), na mesma ordem e com os mesmos textos. Saem: título/ícone/tamanho da janela, `BarraLateral`, `Cabecalho`, `BotaoTema`, `verificar_atualizacao`, `_atualizar_thread`, `_aplicar_atualizacao`, o ramo `"atualizar"` de `processar_fila`, o bloco `if __name__ == "__main__"`. Ficam: `enviando: bool`, `metodo: str`, `pedir_credenciais() -> bool`, o timer da fila e o pedido de credenciais na primeira execução (`QTimer.singleShot(300, ...)` se `metodo == "smtp"` e sem credenciais). `ARQUIVO_PREFS = dados.PASTA / "preferencias.json"`. Modais e `QFileDialog` com `self` como pai.
  - `robo_agregado.instancia.RoboAgregado` — `__init__(self, contexto: Contexto)`; `widget(chave_pagina) -> QWidget`: para `"extrato"` cria a `TelaExtrato` na primeira chamada e devolve a mesma depois; outra chave → `KeyError`. `acoes_cabecalho(chave_pagina) -> list[QWidget]`: `Botao("Credenciais...", "secundario", icone="chave")` ligado a `tela.pedir_credenciais` (só se a tela existe e `tela.metodo == "smtp"`) e `Botao("Pasta de dados", "secundario", icone="pasta")` que faz `dados.preparar_pasta()` + `os.startfile(dados.PASTA)`, nessa ordem. `pode_fechar() -> bool`: `True` se a tela não existe, senão `not tela.enviando`.
  - `robo_agregado.modulo.MODULO` (valores da Global Constraints; `versao=__version__`, `pasta_dados=dados.PASTA`) e `criar(contexto) -> RoboAgregado` com o import de `robo_agregado.instancia` **dentro** da função.

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_modulo.py
def test_entry_point_expoe_modulo():
    eps = {ep.name: ep for ep in entry_points(group="sistema_financeiro.modulos")}
    modulo = eps["robo_agregado"].load()
    assert (modulo.id, modulo.grupo_ad, modulo.nome_exe) == ("robo_agregado", "SF-RoboAgregado", "RoboAgregado.exe")
    assert modulo.versao == robo_agregado.__version__ == "2.0.0"
    assert [p.chave for p in modulo.paginas] == ["extrato"]
    assert modulo.aplicacao_settings == "RoboAgregado"

def test_modulo_e_leve(tmp_path):
    codigo = ("import sys, robo_agregado.modulo; "
              "print('pandas' in sys.modules, 'robo_agregado.tela' in sys.modules)")
    env = {**os.environ, "ROBO_AGREGADO_DADOS": str(tmp_path / "nao_criar")}
    saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, env=env, check=True)
    assert saida.stdout.split() == ["False", "False"]
    assert not (tmp_path / "nao_criar").exists()

def test_abre_na_janela_da_casca(qtbot):
    jan = JanelaPrincipal([MODULO], nome_app="Teste", icone_app="painel", usuario="TCMSP\\teste",
                          modo="casca", configuracoes=QSettings("TCM-teste", "Robo"))
    qtbot.addWidget(jan)
    assert jan.pagina_atual == ("robo_agregado", "extrato")
    assert jan.findChildren(TelaExtrato) and not jan.findChildren(CartaoErro)
```

```python
# tests/test_instancia.py  (contexto = Contexto("TCMSP\\teste", dados.PASTA, "avulso", logging.getLogger("t"), QWidget()))
def test_widget_e_criado_uma_vez(qtbot): assert inst.widget("extrato") is inst.widget("extrato")
def test_pagina_desconhecida(qtbot): with pytest.raises(KeyError): inst.widget("outra")
def test_acoes_smtp(qtbot):          # config padrão tem metodo = smtp
    inst.widget("extrato")
    assert [b.text() for b in inst.acoes_cabecalho("extrato")] == ["Credenciais...", "Pasta de dados"]
def test_acoes_outlook(qtbot, monkeypatch):  # tela.metodo = "outlook" antes de pedir as ações
    assert [b.text() for b in inst.acoes_cabecalho("extrato")] == ["Pasta de dados"]
def test_pode_fechar_durante_envio(qtbot):
    assert inst.pode_fechar()                  # antes de abrir a tela
    inst.widget("extrato").enviando = True
    assert not inst.pode_fechar()
def test_pasta_de_dados_abre_a_pasta(qtbot, monkeypatch):  # os.startfile trocado por falso
    acoes[-1].click(); assert abertos == [dados.PASTA]
```

Ajustar os textos dos botões ao que o `Botao` expõe em `text()` (pode incluir espaços por causa do ícone; nesse caso comparar com `.strip()`).

- [ ] **Step 2: Rodar e ver falhar** — `.venv\Scripts\python -m pytest -q` → FAIL (`robo_agregado.modulo` não existe).

- [ ] **Step 3: Implementar** `tela.py` (a partir de `app.py`), `instancia.py`, `modulo.py`; apagar `app.py`, `atualizador.py`, `design_system/`. Buscar resto de imports antigos: `rg -n "design_system|import atualizador|from versao|import enviar_fretes" src tests` → nada.

- [ ] **Step 4: Rodar e ver passar** — `.venv\Scripts\python -m pytest -q` → todos passam.

- [ ] **Step 5: Sem commit.**

---

### Task 4: `.exe` avulso — `main.py`, build, Release e README

**Files:**
- Create: `main.py`, `.github/workflows/release.yml`
- Modify: `build.ps1`, `Readme.md`, `.gitignore`, `gerar_planilha_exemplo.py` (só se ainda rodar; ver Step 5)

**Interfaces:**
- Consumes: `MODULO` (Task 3), `dados.atualizacao_ativa()` (Task 2), `rodar_avulso(..., atualizar=)` (Task 1).
- Produces:
  - `main.py`: `sys.exit(rodar_avulso(MODULO, atualizar=dados.atualizacao_ativa()))` dentro de `if __name__ == "__main__":`.
  - `build.ps1` com `param([string]$Python)`: sem parâmetro usa `.venv\Scripts\python.exe` se existir, senão `python`. Mesmo PyInstaller de hoje (`--onefile --windowed --name RoboAgregado`, `--hidden-import openpyxl pythoncom win32com.client`, os mesmos `--exclude-module`), trocando `--add-data config.ini/styles.qss` por `--collect-data tcm_ui --collect-data robo_agregado`, entrada `main.py`. Versão lida de `src/robo_agregado/__init__.py` (`__version__ = "(.+)"`). Mantém a checagem de "nenhum arquivo novo gerado" e grava `dist\RoboAgregado.exe.sha256` no formato atual (`<hash>  RoboAgregado.exe`).
  - `release.yml` igual ao do `pdf-merge` (gatilho `v*` + `workflow_dispatch`, `windows-latest`, Python 3.13, `upload-artifact`, `softprops/action-gh-release@v2` com o `.exe` e o `.sha256`), com estas diferenças: instala com `python -m pip install . pytest pytest-qt pyinstaller`; o passo de versão **não reescreve** nada — falha se `github.ref_name` sem o `v` for diferente de `robo_agregado.__version__`; o passo "Verificar se a janela abre" vira `python -m pytest -q` (com `QT_QPA_PLATFORM=offscreen`); o build chama `./build.ps1 -Python python`.
  - `Readme.md`: estrutura nova; como rodar (`python main.py`); que, pelo Python, os dados ficam em `%LOCALAPPDATA%\RoboAgregado` como no `.exe` (ou em `ROBO_AGREGADO_DADOS`); log de erros em `%LOCALAPPDATA%\RoboAgregado\logs\robo_agregado.log`; testes; publicar versão = subir `__version__`, tag igual, o workflow gera a Release; `[atualizacao] ativo = nao` desliga; linha de comando `python -m robo_agregado.enviar_fretes ...`; o módulo também roda dentro do Sistema Financeiro (grupo `SF-RoboAgregado`).
  - `.gitignore`: acrescentar `.venv/`, `*.egg-info/`, `.pytest_cache/`; manter as regras de credenciais e dados.

- [ ] **Step 1: Escrever `main.py`, `build.ps1`, `release.yml`, README e `.gitignore`**

- [ ] **Step 2: Rodar pelo Python**

Run: `.venv\Scripts\python main.py`
Expected: abre a janela "RoboAgregado" com a barra lateral (item "Extrato de fretes", rodapé "Versão 2.0.0"), cabeçalho com "Credenciais...", "Pasta de dados" e o botão de tema; a tela igual à de hoje. Fechar.

- [ ] **Step 3: Gerar o executável**

Run: `powershell -File build.ps1`
Expected: `Pronto: versao 2.0.0 | SHA-256 ...`; `dist\RoboAgregado.exe` e `dist\RoboAgregado.exe.sha256` criados.

- [ ] **Step 4: Conferir o `.exe` com a plataforma Windows real**

Abrir `dist\RoboAgregado.exe`, capturar a janela nos temas claro e escuro (mesmo método do `capturar_real.py` do plano 1) e comparar com o `RoboAgregado.exe` 1.3.3: mesmo conteúdo da página, sem barra de rolagem horizontal, `styles.qss` aplicado. Conferir que `%LOCALAPPDATA%\RoboAgregado\config.versao` virou `2.0.0` e que existe `config.ini.bak`. Nenhum e-mail é enviado nesta verificação.

- [ ] **Step 5: `gerar_planilha_exemplo.py`** — rodar; se os cabeçalhos não baterem com o `config.ini` (hoje gera `CNPJ/CPF`, o config espera `CNPJ / CPF` e aba `Emails`), ajustar para gerar uma planilha que o programa carrega, com dados fictícios; senão deixar como está.

- [ ] **Step 6: Rodar todos os testes dos dois repositórios**

Run: `.venv\Scripts\python -m pytest -q` em `Send_Agregados` e em `Tcm-ui`
Expected: tudo passa.

- [ ] **Step 7: Sem commit.** No "Salvar versão": tag `v1.1.0` no `Tcm-ui` primeiro; depois commit + tag `v2.0.0` no `Send_Agregados` (o workflow gera a Release). Teste final pelo Erik: um envio real pequeno com o `.exe` 2.0.0 antes da tag.

---

## Depois deste plano

- Atualizar o `CLAUDE.md` deste repositório ("Onde paramos") e o spec onde mudou: `Contexto`/`rodar_avulso(atualizar=)`, `tcm_ui.registro`, versão do `tcm-ui` no `requirements.txt` da casca (`v1.1.0`).
- Plano 3: a casca (grupos do AD, entry points, log em `%LOCALAPPDATA%\TCM\SistemaFinanceiro\logs\` via `configurar_log`, build, primeira Release só com o RoboAgregado).
