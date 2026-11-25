# Plano 8 — Login Microsoft padronizado (Enviador + RoboAgregado)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (Erik pediu execução direta, sem subagentes). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** O RoboAgregado envia com o login Microsoft da própria pessoa, "Enviar como" a caixa do financeiro, usando o mesmo código de login que o Enviador, agora no `Tcm-ui`.

**Architecture:** `tcm_ui.microsoft` reúne o que hoje está no `enviador_pdf_xml` (Conta MSAL com cache DPAPI, `LoginWorker`, `abrir_smtp` XOAUTH2, IDs do aplicativo) e ganha um cache compartilhado e a criação da conta em segundo plano. `tcm_ui.microsoft_ui.CartaoContaMicrosoft` é o bloco "Conta de envio" usado pelos dois diálogos. O Enviador só troca as importações; o RoboAgregado troca o método `smtp` com senha pelo método `microsoft`.

**Tech Stack:** Python 3.13, PySide6, msal 1.39.0, msal-extensions 1.3.1, smtplib (XOAUTH2), pytest + pytest-qt.

**Spec:** `docs/superpowers/specs/2026-11-25-login-microsoft-design.md`

## Global Constraints

- **Sem commit, push, tag ou release** até o Erik dizer "Salvar versão". Onde um passo diria "commit", não faça nada.
- Repositórios em `C:\Users\erik.freitas\Projetos\`: `Tcm-ui`, `pdf-xml-mailer`, `Send_Agregados`, `Sistema-Financeiro`. Testes: `.venv\Scripts\python -m pytest -q` em cada um (com `QT_QPA_PLATFORM=offscreen`).
- Versões: `Tcm-ui` 1.6.0, `pdf-xml-mailer` 2.1.0, `Send_Agregados` 2.1.0, `Sistema-Financeiro` 1.5.0.
- Escopo OAuth: `["https://outlook.office.com/SMTP.Send"]`; servidor `smtp.office365.com:587`, STARTTLS com certificado verificado.
- `msal`/`msal-extensions` só pelo extra `tcm-ui[microsoft]` (`msal>=1.39,<2`, `msal-extensions>=1.3.1,<2`). Os IDs vêm de `enviador_pdf_xml/modelo.py` sem alteração.
- Cache: `%LOCALAPPDATA%\TCM\ContaMicrosoft\token_cache.bin`; a variável `TCM_CONTA_MICROSOFT` troca a pasta.
- Repositórios públicos: nenhum e-mail real em código, testes ou docs (use `@tcm.com`/`example.com` fictícios).
- `import msal` só dentro de funções (o `modulo.py` dos sistemas continua leve).
- Textos fixados pelo spec:
  - `SendAsDenied`: `Sua conta não tem permissão para enviar como '<endereço>'. Peça à TI a permissão 'Enviar como' nessa caixa.`
  - Botão do cabeçalho: `Conta de envio...`

## Review Focus

1. **`.env` antigo com aspas, BOM ou linhas vazias** → a migração lê como o `carregar_env` lia (aspas e BOM removidos) e apaga o arquivo mesmo se faltar `EMAIL_CCO`. Teste na Task 4.
2. **Sessão expirada no meio de um lote longo do RoboAgregado** → `FalhaLogin` vira `ErroFatal` com "Entre com a Microsoft em 'Conta de envio...'", o lote para e nada é marcado como enviado. Teste na Task 4.
3. **Primeira abertura sem internet** → a tela do RoboAgregado abre, o diálogo mostra o motivo e "Entrar" fica desligado; nada trava a interface. Teste na Task 5.
4. **"Enviar como" com e-mail inválido ou com espaços** → o diálogo recusa com mensagem no campo; espaços nas pontas são removidos. Teste na Task 5.
5. **Cache antigo do Enviador presente e o novo também** → o novo não é sobrescrito. Teste na Task 1.

---

### Task 1: `tcm_ui.microsoft` (conta, cache, SMTP, criação em segundo plano)

**Files:**
- Create: `Tcm-ui/src/tcm_ui/microsoft.py`
- Modify: `Tcm-ui/pyproject.toml` (versão `1.6.0`, extra `microsoft`), `Tcm-ui/src/tcm_ui/__init__.py` (`__version__ = "1.6.0"`)
- Test: `Tcm-ui/tests/test_microsoft.py`

**Interfaces:**
- Produces:
  - `CLIENT_ID: str`, `TENANT_ID: str`, `ESCOPOS: list[str]`, `SMTP_HOST = "smtp.office365.com"`, `SMTP_PORTA = 587`, `TIMEOUT_SMTP = 30`
  - `class ContaNaoConfigurada(Exception)`, `class FalhaLogin(Exception)`
  - `pasta_cache() -> Path` (`TCM_CONTA_MICROSOFT` ou `%LOCALAPPDATA%\TCM\ContaMicrosoft`)
  - `migrar_cache(antigo: Path) -> bool` — copia `antigo` para `pasta_cache()/token_cache.bin` só se o novo não existe e o antigo existe; True se copiou; nunca levanta `OSError`
  - `class Conta: __init__(app=None)`, `email() -> str | None`, `entrar() -> str`, `token() -> str`, `sair() -> None` (mesmo comportamento de `enviador_pdf_xml.conta.Conta`)
  - `xoauth2(email: str, token: str) -> str`, `abrir_smtp(email: str, token: str, fabrica=smtplib.SMTP) -> smtplib.SMTP`
  - `class LoginWorker(QObject)`: sinais `concluido(str)`, `falhou(str)`, slot `run()` (o do Enviador)
  - `AVISO_SEM_REDE = "Não foi possível conectar ao login Microsoft (verifique a internet). Detalhes no log."`
  - `criar_conta(log: logging.Logger, fabrica: Callable[[], Conta] = Conta) -> tuple[Conta | None, str]` — `ContaNaoConfigurada` → `(None, str(e))`; outra exceção → loga e `(None, AVISO_SEM_REDE)`
  - `criar_conta_em_segundo_plano(pai: QObject, log, ao_pronto: Callable[[Conta | None, str], None], fabrica=Conta) -> None` — thread daemon + fila esvaziada por `QTimer` (30 ms) filho de `pai`; se `pai` for destruído antes, o resultado é descartado (é o `_EntregaDeConta` do Enviador generalizado)

- [ ] **Step 1: Testes que falham** em `tests/test_microsoft.py`. Porte os testes de `pdf-xml-mailer/tests/test_conta.py`, `test_lote.py::test_xoauth2_formato`, `test_lote.py::test_abrir_smtp_usa_xoauth2` e `test_worker.py` (LoginWorker) trocando o módulo, e acrescente:

```python
def test_pasta_cache_variavel(tmp_path, monkeypatch):
    monkeypatch.setenv("TCM_CONTA_MICROSOFT", str(tmp_path))
    assert microsoft.pasta_cache() == tmp_path

def test_pasta_cache_padrao(tmp_path, monkeypatch):
    monkeypatch.delenv("TCM_CONTA_MICROSOFT", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert microsoft.pasta_cache() == tmp_path / "TCM" / "ContaMicrosoft"

def test_migrar_cache_copia_so_se_novo_nao_existe(tmp_path, monkeypatch):
    monkeypatch.setenv("TCM_CONTA_MICROSOFT", str(tmp_path / "novo"))
    antigo = tmp_path / "antigo.bin"; antigo.write_bytes(b"A")
    assert microsoft.migrar_cache(antigo) is True
    assert (tmp_path / "novo" / "token_cache.bin").read_bytes() == b"A"
    antigo.write_bytes(b"B")
    assert microsoft.migrar_cache(antigo) is False
    assert (tmp_path / "novo" / "token_cache.bin").read_bytes() == b"A"

def test_migrar_cache_sem_antigo(tmp_path, monkeypatch):
    monkeypatch.setenv("TCM_CONTA_MICROSOFT", str(tmp_path))
    assert microsoft.migrar_cache(tmp_path / "nao_existe.bin") is False

def test_criar_conta_sem_rede_devolve_aviso():
    def falha(): raise OSError("rede")
    assert microsoft.criar_conta(logging.getLogger("t"), falha) == (None, microsoft.AVISO_SEM_REDE)

def test_criar_conta_em_segundo_plano_entrega_na_thread_da_interface(qtbot):
    pai = QObject(); recebido = []
    conta = object()
    microsoft.criar_conta_em_segundo_plano(pai, logging.getLogger("t"),
                                           lambda c, a: recebido.append((c, a, threading.current_thread())),
                                           fabrica=lambda: conta)
    qtbot.waitUntil(lambda: recebido, timeout=3000)
    assert recebido[0][:2] == (conta, "") and recebido[0][2] is threading.main_thread()
```

- [ ] **Step 2:** `.venv\Scripts\python -m pip install "msal==1.39.0" "msal-extensions==1.3.1"` e rode `pytest tests/test_microsoft.py -q`. Esperado: FAIL (`No module named tcm_ui.microsoft`).
- [ ] **Step 3: Implemente `tcm_ui/microsoft.py`** movendo o código do Enviador (`conta.py`, `envio.xoauth2/abrir_smtp`, `worker.LoginWorker`, `instancia.criar_conta/_EntregaDeConta`) e copiando os IDs de `modelo.py`. `pyproject.toml`: `version = "1.6.0"` e `[project.optional-dependencies] microsoft = ["msal>=1.39,<2", "msal-extensions>=1.3.1,<2"]` (manter `dev`).
- [ ] **Step 4:** `pytest -q` (suíte inteira do Tcm-ui). Esperado: todos passam (161 + os novos).

### Task 2: `tcm_ui.microsoft_ui.CartaoContaMicrosoft`

**Files:**
- Create: `Tcm-ui/src/tcm_ui/microsoft_ui.py`
- Test: `Tcm-ui/tests/test_microsoft_ui.py`

**Interfaces:**
- Consumes: `Conta`, `LoginWorker`, `FalhaLogin` (Task 1).
- Produces: `class CartaoContaMicrosoft(QWidget)`:
  - `__init__(conta: Conta | None, *, aviso_sem_conta: str = "", sessao_expirada: bool = False, parent=None)`
  - sinal `mudou = Signal()` (emitido ao logar, sair ou falhar o login, para o diálogo reajustar a altura)
  - `email() -> str | None` (None se sem conta ou sessão expirada)
  - `abandonar_login() -> None` (chamado pelo `done()` do diálogo)
  - widgets públicos: `rotulo_conta`, `botao_entrar` ("Entrar com a Microsoft"), `botao_sair` ("Sair da conta"), `aviso`
  - Comportamento e textos idênticos aos do bloco "Conta de envio" de `enviador_pdf_xml.dialogos.DialogoConta` (linhas 52–62 e 83–147 hoje), sem Para/Cco e sem o botão Salvar.

- [ ] **Step 1: Testes que falham.** Porte de `pdf-xml-mailer/tests/test_ui_conta.py` os casos de login/sair/sessão expirada/login travado/falha/sem conta para o cartão (`FakeConta` vai junto para `tests/test_microsoft_ui.py`), mais:

```python
def test_mudou_ao_sair(qtbot):
    conta = FakeConta("eu@tcm.com"); cartao = CartaoContaMicrosoft(conta); qtbot.addWidget(cartao)
    with qtbot.waitSignal(cartao.mudou):
        cartao.botao_sair.click()
    assert cartao.email() is None and conta.saiu
```

- [ ] **Step 2:** `pytest tests/test_microsoft_ui.py -q` → FAIL (módulo não existe).
- [ ] **Step 3:** Implemente `CartaoContaMicrosoft` extraindo o bloco do `DialogoConta`.
- [ ] **Step 4:** `pytest -q` no Tcm-ui → tudo passa. Instale o Tcm-ui local nos venvs dos outros três repositórios (`pip install -e ../Tcm-ui[microsoft]`).

### Task 3: Enviador 2.1.0 usa `tcm_ui.microsoft`

**Files:**
- Delete: `pdf-xml-mailer/src/enviador_pdf_xml/conta.py`, `tests/test_conta.py` (portado na Task 1)
- Modify: `modelo.py` (remover `CLIENT_ID`, `TENANT_ID`, `ESCOPOS`, `pendencias_release`, `SMTP_HOST`, `SMTP_PORTA`), `envio.py` (remover `xoauth2`/`abrir_smtp`; usar `tcm_ui.microsoft.abrir_smtp`), `worker.py` (remover `LoginWorker`), `dialogos.py` (`DialogoConta` usa `CartaoContaMicrosoft`; mantém aliases `rotulo_conta`, `botao_entrar`, `botao_sair`, `aviso` apontando para os do cartão), `instancia.py` (`FABRICA_CONTA` = `tcm_ui.microsoft.Conta`; usar `criar_conta`/`criar_conta_em_segundo_plano`; chamar `migrar_cache(dados.pasta_local() / "token_cache.bin")` antes de criar a conta), `cli.py`, `tela.py` (`AVISO_NAO_CONFIGURADA` passa a ser `str(ContaNaoConfigurada)` vindo do Tcm-ui), `.github/workflows/release.yml` (remover o passo de `pendencias_release`), `tests/test_avulso.py:49`, `__init__.py` (`2.1.0`), `pyproject.toml` (`tcm-ui[microsoft]>=1.6.0`, remover `msal*` diretos), `requirements.txt` (`tcm-ui[microsoft] @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.6.0`)
- Test: `tests/test_instancia.py`, `test_lote.py`, `test_worker.py`, `test_cli.py`, `test_ui_conta.py`, `test_dados.py` — trocar `enviador_pdf_xml.envio.abrir_smtp`/`conta` pelos de `tcm_ui.microsoft`

- [ ] **Step 1: Teste novo que falha** em `tests/test_instancia.py`:

```python
def test_migra_o_cache_antigo_ao_abrir(qtbot, monkeypatch, tmp_path):
    monkeypatch.setenv("TCM_CONTA_MICROSOFT", str(tmp_path / "novo"))
    antigo = dados.pasta_local() / "token_cache.bin"; antigo.parent.mkdir(parents=True, exist_ok=True)
    antigo.write_bytes(b"C")
    ... abrir a página "enviar" com FABRICA_CONTA falsa ...
    assert (tmp_path / "novo" / "token_cache.bin").read_bytes() == b"C"
```

- [ ] **Step 2:** `pytest tests/test_instancia.py -q` → o novo falha.
- [ ] **Step 3:** Faça as trocas listadas em **Files**. `grep -rn "enviador_pdf_xml.conta\|CLIENT_ID\|LoginWorker\|xoauth2" src tests` não deve achar nada fora dos aliases.
- [ ] **Step 4:** `pytest -q` → todos passam (138 ± os movidos para o Tcm-ui). `powershell -File build.ps1` gera o `EnviadorEmails.exe`.

### Task 4: RoboAgregado — envio com a conta Microsoft (núcleo)

**Files:**
- Modify: `Send_Agregados/src/robo_agregado/enviar_fretes.py`, `config.ini`
- Test: Create `Send_Agregados/tests/test_envio_microsoft.py`

**Interfaces:**
- Consumes: `tcm_ui.microsoft.Conta`, `FalhaLogin`, `ContaNaoConfigurada`, `abrir_smtp` (Task 1).
- Produces (em `enviar_fretes`):
  - `metodo_envio(cfg) -> str` — `"outlook"` se o `config.ini` diz `outlook`; qualquer outro valor (inclusive `smtp`) → `"microsoft"`
  - `migrar_env(prefs: dict, caminho: Path | None = None) -> bool` — lê o `.env` (`ARQUIVO_ENV`), põe `EMAIL_CCO` em `prefs["cco_microsoft"]` e `SMTP_USUARIO` em `prefs["enviar_como"]` só se as chaves não existem, apaga o `.env`; True se havia `.env`. Não mexe em `os.environ`.
  - `class Enviador: __init__(cfg, conta: Conta | None = None)`; no método `microsoft`, `_conectar()` usa `abrir_smtp(conta.email(), conta.token())`; `enviar(envio, remetente="", cco="")` usa `remetente or conta.email()`
  - `MSG_SEM_CONTA = "Entre com a Microsoft em 'Conta de envio...'."`
- Remove: `carregar_env`, `credenciais_ok`, `salvar_env`, `conectar_smtp`, `testar_login`, `remetente_padrao`; `cco_padrao(cfg)` passa a ler só o `config.ini`.
- `config.ini`: `metodo = microsoft` com o comentário dos dois métodos (`microsoft` = login da própria pessoa, "Enviar como" na tela; `outlook` = Outlook instalado); `[smtp]` fica só com `nome_remetente`.

- [ ] **Step 1: Testes que falham** (`SMTP` falso que guarda `send_message` e pode levantar):

```python
def test_metodo_smtp_antigo_vira_microsoft(): assert ef.metodo_envio(cfg("smtp")) == "microsoft"
def test_metodo_outlook_continua(): assert ef.metodo_envio(cfg("outlook")) == "outlook"

def test_migrar_env(tmp_path):
    env = tmp_path / ".env"
    env.write_text('\ufeffSMTP_USUARIO="financeiro@example.com"\nSMTP_SENHA="x"\n\nEMAIL_CCO=\'cco@example.com\'\n', encoding="utf-8")
    prefs = {}
    assert ef.migrar_env(prefs, env) is True
    assert prefs == {"enviar_como": "financeiro@example.com", "cco_microsoft": "cco@example.com"}
    assert not env.exists()

def test_migrar_env_nao_sobrescreve_prefs(tmp_path): ...  # prefs já com "enviar_como" fica igual
def test_migrar_env_sem_arquivo(tmp_path): assert ef.migrar_env({}, tmp_path / ".env") is False

def test_envia_como_remetente_logando_com_a_propria_conta(monkeypatch):
    conta = ContaFalsa("eu@tcm.com", token="T"); smtp = SMTPFalso()
    monkeypatch.setattr(ef, "abrir_smtp", lambda email, token: (smtp.logou(email, token), smtp)[1])
    ef.Enviador(cfg("microsoft"), conta).enviar(envio("a@example.com"), "financeiro@example.com", "c@example.com")
    assert smtp.login == ("eu@tcm.com", "T")
    assert smtp.from_addr == "financeiro@example.com" and smtp.msg["From"] == "financeiro@example.com"
    assert smtp.to_addrs == ["a@example.com", "c@example.com"] and "Bcc" not in smtp.msg

def test_sem_remetente_usa_a_propria_conta(...): smtp.from_addr == "eu@tcm.com"

def test_send_as_negado_e_fatal_com_texto_do_spec(...):
    # SMTPSenderRefused com b"SendAsDenied"
    with pytest.raises(ef.ErroFatal, match="Peça à TI a permissão 'Enviar como' nessa caixa"): ...

def test_sessao_expirada_e_fatal(...):
    # conta.token() levanta FalhaLogin
    with pytest.raises(ef.ErroFatal, match="Conta de envio"): ...

def test_sem_conta_e_fatal(): with pytest.raises(ef.ErroFatal, match="Conta de envio"): ef.Enviador(cfg("microsoft"), None).enviar(...)
```

- [ ] **Step 2:** `pytest tests/test_envio_microsoft.py -q` → FAIL.
- [ ] **Step 3:** Implemente. `FalhaLogin`/`ContaNaoConfigurada` em `_conectar` viram `ErroFatal(f"{e} {MSG_SEM_CONTA}")`. A reconexão após `SMTPServerDisconnected` pede um token novo. No `main()` (linha de comando): `migrar_env` com as prefs do arquivo, `Conta()` quando o método é `microsoft`, remetente = `enviar_como` do `config.ini` ou da conta.
- [ ] **Step 4:** `pytest -q` → tudo passa; ajuste `tests/test_dados.py:95` e `tests/test_instancia.py:34` para o novo método.

### Task 5: RoboAgregado — tela, diálogo e versão 2.1.0

**Files:**
- Modify: `Send_Agregados/src/robo_agregado/tela.py`, `instancia.py`, `__init__.py` (`2.1.0`), `pyproject.toml` (`tcm-ui[microsoft]>=1.6.0`), `requirements.txt` (`tcm-ui[microsoft] @ ...@v1.6.0`), `build.ps1` (`--hidden-import msal --hidden-import msal_extensions`), `README.md` (seções de credenciais/.env → "Conta de envio", "Enviar como" e o pedido de permissão à TI)
- Test: `Send_Agregados/tests/test_tela_conta.py`

**Interfaces:**
- Consumes: `CartaoContaMicrosoft` (Task 2), `criar_conta_em_segundo_plano` (Task 1), `metodo_envio`, `migrar_env`, `Enviador(cfg, conta)` (Task 4).
- Produces:
  - `class DialogoContaEnvio(Modal)`: `__init__(pai, conta, enviar_como: str, *, aviso_sem_conta="", sessao_expirada=False)`; atributos `cartao`, `campo_enviar_como`, `resultado: str | None` (o "Enviar como" salvo, `""` = própria conta); Salvar só habilita com conta logada; e-mail inválido mostra erro no campo.
  - `TelaExtrato`: `conta` (None até chegar), `pedir_conta() -> bool` (substitui `pedir_credenciais`), `remetente() -> str` (`prefs["enviar_como"]` ou e-mail da conta)
  - `instancia.RoboAgregado.acoes_cabecalho`: botão `Conta de envio...` (ícone `email`) quando `tela.metodo == "microsoft"`

- [ ] **Step 1: Testes que falham** (conta falsa via `monkeypatch` de `tcm_ui.microsoft.Conta` ou fábrica injetável na tela):

```python
def test_primeira_abertura_sem_conta_abre_o_dialogo(qtbot, ...): ...  # depois que a conta chega e email() é None
def test_sem_internet_abre_e_mostra_o_motivo(qtbot, ...):
    # fábrica levanta OSError → diálogo com cartao.aviso == AVISO_SEM_REDE e botao_entrar desligado
def test_enviar_como_invalido_recusa(qtbot):
    d = DialogoContaEnvio(None, FakeConta("eu@tcm.com"), ""); d.campo_enviar_como.setText(" errado ")
    d.botao_salvar.click()
    assert d.resultado is None and "inválido" in d.campo_enviar_como_field.erro()  # Campo.definir_erro
def test_enviar_como_salvo_sem_espacos(qtbot):
    ... setText("  financeiro@example.com  "); salvar → resultado == "financeiro@example.com"
def test_tela_migra_o_env_ao_abrir(qtbot, tmp_path, ...): # .env vira prefs e some
def test_confirmacao_mostra_o_remetente(qtbot, ...): # texto do Modal.confirmar contém "financeiro@example.com"
def test_acao_conta_de_envio(inst): ...  # rótulo "Conta de envio..."
```

- [ ] **Step 2:** `pytest tests/test_tela_conta.py -q` → FAIL.
- [ ] **Step 3:** Implemente: `DialogoCredenciais` sai; a tela chama `migrar_env(self.prefs)` + `salvar_prefs` no `__init__`, cria a conta com `criar_conta_em_segundo_plano(self, contexto.log, self._conta_pronta)` só no método `microsoft`, e o primeiro acesso abre o diálogo quando a conta chega sem e-mail; envio exige `self.conta` com e-mail (senão `pedir_conta()`), passa `self.conta` ao `Enviador`; a confirmação mostra `self.remetente()`. `FalhaLogin` durante o lote termina o envio e reabre o diálogo com `sessao_expirada=True`.
- [ ] **Step 4:** `pytest -q` → tudo passa. `powershell -File build.ps1` gera o `RoboAgregado.exe`. Confira o diálogo nos dois temas com `widget.grab()` em `QT_QPA_PLATFORM=offscreen` (mostrar com `show()`, nunca `exec()`).

### Task 6: Casca 1.5.0

**Files:**
- Modify: `Sistema-Financeiro/requirements.txt` (`tcm-ui[microsoft] @ ...@v1.6.0`, `robo-agregado @ ...@v2.1.0`, `enviador-pdf-xml @ ...@v2.1.0`), `requirements-local.txt` (`../Tcm-ui[microsoft]`), `src/sistema_financeiro/__init__.py` (`1.5.0`), `build.ps1` (`TCM_CONTA_MICROSOFT` temporário nas variáveis da verificação; remover `SMTP_USUARIO`/`SMTP_SENHA`), `CLAUDE.md` (plano 8, ordem de lançamento)

- [ ] **Step 1:** `pytest -q` → 51 passam.
- [ ] **Step 2:** `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 -Local` → "Verificacao do .exe: OK" e `pip freeze` igual a `versoes.txt` (mesmo `diff` usado em 25/11).
- [ ] **Step 3:** Captura da casca com o RoboAgregado aberto (método do `medir.py` de 25/11, diálogos suprimidos) mostrando o botão "Conta de envio...".

### Task 7: Teste do Erik e lançamento (só com "Salvar versão")

- [ ] O Erik testa o `RoboAgregado.exe` novo: login com a própria conta, "Enviar como" a caixa do financeiro, um extrato real para um endereço de teste; e o `EnviadorEmails.exe` sem precisar entrar de novo.
- [ ] Ordem: `Tcm-ui` v1.6.0 (tag) → `pdf-xml-mailer` v2.1.0 → `Send_Agregados` v2.1.0 → `Sistema-Financeiro` v1.5.0, cada Release conferida com o `lancar.sh` antes da próxima.
