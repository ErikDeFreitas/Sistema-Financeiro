# Plano 1 — Tcm-ui v1.0.0

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o pacote `tcm-ui` (repo `ErikDeFreitas/Tcm-ui`) com o design system do RoboAgregado, o atualizador por Release do GitHub, o contrato de módulo e a janela padrão (barra lateral + cabeçalho) usada tanto pela casca quanto pelos `.exe` avulsos.

**Architecture:** Pacote Python em layout `src/` instalável por pip a partir do GitHub. O design system é portado de `Projeto_Agregados/design_system/` quase sem mudança. A `JanelaPrincipal` recebe uma lista de `Modulo` e cuida de navegação, carregamento preguiçoso, isolamento de erro e fechamento; a casca (plano 3) e `rodar_avulso` só a configuram.

**Tech Stack:** Python 3.13, PySide6-Essentials ≥ 6.8 (instalado: 6.12.0), setuptools, pytest + pytest-qt (offscreen).

**Spec:** `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md` (seções 5.2, 5.3, 5.4, 5.6, 7)

**Série de planos** (um por subsistema, na ordem da seção 6 do spec):
1. **Tcm-ui** (este) · 2. RoboAgregado · 3. Casca Sistema-Financeiro (acesso AD, build, Release) ·
4. Mesclador · 5. Enviador PDF+XML · 6. Renomeador de CT-e · 7. Sistema Catraca.
Os planos 2–7 são escritos depois que o anterior terminar, usando a API real do `tcm-ui`.

## Global Constraints

- **Proibido commit, push, tag ou release.** Regra do Erik: só quando ele disser "Salvar versão". Nenhuma tarefa deste plano tem passo de commit; subagentes também não commitam.
- Repositório local: `C:\Users\erik.freitas\Projetos\Tcm-ui` (clone de `https://github.com/ErikDeFreitas/Tcm-ui.git`), fora do OneDrive. Venv em `.venv\` dentro dele (no `.gitignore`).
- Fonte do design system: `C:\Users\erik.freitas\TCM LOGISTICA e TRANSPORTES\FileServer - TI\15. Automações\Projetos_Financeiro\Projeto_Agregados\design_system\` e `...\Projeto_Agregados\atualizador.py`. **Só leitura**: nada no FileServer é alterado.
- Nome de distribuição pip: `tcm-ui`; pacote de import: `tcm_ui`; versão `1.0.0` (em `pyproject.toml` e em `tcm_ui.__version__`, iguais).
- API em português, no estilo do RoboAgregado (`Botao`, `Cartao`, `BarraLateral`, `tema`, `ESPACO`, `TAMANHOS`, `MARCA`).
- Só a janela (casca ou avulso) chama `tema.aplicar(app)`. Nenhum código de módulo chama `setStyleSheet` no `QApplication`.
- Testes rodam com `QT_QPA_PLATFORM=offscreen` (definido em `tests/conftest.py`).
- Comando de teste: `.venv\Scripts\python -m pytest -q` na raiz do repo.

## Review Focus

1. **Última página lembrada que não existe mais** (módulo removido ou sem permissão): a janela deve abrir na primeira página disponível, sem erro. → teste `test_ultima_pagina_invalida_cai_na_primeira` (Task 6).
2. **Uma página do módulo quebra e a outra não**: a página com erro mostra `CartaoErro`; a outra página do mesmo módulo abre normal. → `test_erro_em_uma_pagina_nao_afeta_outra` (Task 6).
3. **`pode_fechar()` lança exceção**: tratar como veto (pede confirmação), registrar no log, nunca travar o fechamento. → `test_pode_fechar_com_excecao_conta_como_veto` (Task 6).
4. **Nome de ícone desconhecido numa `Pagina`**: barra lateral desenha o ícone `info` em vez de quebrar. → `test_icone_desconhecido_usa_info` (Task 3).
5. **Lista de módulos vazia** (usuário sem acesso): janela mostra `EstadoVazio` com a mensagem recebida, sem barra de itens. → `test_sem_modulos_mostra_estado_vazio` (Task 6).

---

## Estrutura de arquivos

```
Tcm-ui/
├── pyproject.toml
├── README.md
├── .gitignore                       # .venv/, __pycache__/, build/, dist/, *.egg-info/
├── src/tcm_ui/
│   ├── __init__.py                  # __version__ + reexporta tema, ESPACO, TAMANHOS, MARCA
│   ├── themes.py                    # portado; + tema.configurar()
│   ├── icons.py                     # portado; fallback de ícone desconhecido
│   ├── components.py                # portado; + secao, limpar_acoes, CartaoErro, EstadoVazio
│   ├── styles.qss                   # portado; + QLabel[papel="secao"]
│   ├── atualizador.py               # portado e parametrizado (repositório, nome do .exe, versão)
│   ├── modulo.py                    # Pagina, Contexto, InstanciaModulo, Modulo
│   ├── janela.py                    # JanelaPrincipal
│   ├── atualizacao_ui.py            # VerificadorAtualizacao
│   ├── avulso.py                    # rodar_avulso()
│   └── demo.py                      # vitrine: python -m tcm_ui.demo
└── tests/
    ├── conftest.py                  # offscreen + fixtures (app, módulos falsos)
    ├── test_design_system.py
    ├── test_componentes.py
    ├── test_atualizador.py
    ├── test_modulo.py
    ├── test_janela.py
    └── test_avulso.py
```

---

### Task 1: Repositório, pacote e design system portado

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `src/tcm_ui/__init__.py`, `src/tcm_ui/themes.py`, `src/tcm_ui/icons.py`, `src/tcm_ui/components.py`, `src/tcm_ui/styles.qss`, `tests/conftest.py`, `tests/test_design_system.py`

**Interfaces:**
- Produces: `tcm_ui.__version__ == "1.0.0"`; `tcm_ui.themes`: `tema` (instância de `GerenciadorTema`), `MARCA`, `TEMAS`, `TAMANHOS`, `ESPACO`, `FONTES`; `tcm_ui.icons`: `ICONES`, `svg()`, `pixmap()`, `icone()`, `arquivo()`; `tcm_ui.components`: todas as classes do `design_system/components.py` original com os mesmos nomes e assinaturas.

- [ ] **Step 1: Clonar e preparar o ambiente**

```powershell
cd C:\Users\erik.freitas\Projetos
git clone https://github.com/ErikDeFreitas/Tcm-ui.git
cd Tcm-ui
python -m venv .venv
```

- [ ] **Step 2: Criar `pyproject.toml`**

setuptools com layout `src/`; `name = "tcm-ui"`, `version = "1.0.0"`, `requires-python = ">=3.11"`, `dependencies = ["PySide6-Essentials>=6.8"]`, extra `dev = ["pytest", "pytest-qt"]`, `[tool.setuptools.package-data] tcm_ui = ["styles.qss"]`, `[tool.pytest.ini_options] testpaths = ["tests"]`.

- [ ] **Step 3: Copiar o design system**

Copiar `themes.py`, `icons.py`, `components.py`, `styles.qss` de `Projeto_Agregados\design_system\` para `src/tcm_ui/`. Ajustes, e só estes:
- `icons._PASTA_TEMP` → `Path(tempfile.gettempdir()) / "tcm_ui_icones"`.
- Docstrings que dizem "RoboAgregado" → "TCM".
- `GerenciadorTema.__init__` **não** abre `QSettings("TCM", "RoboAgregado")`; isso muda na Task 2. Por ora: `self._config = None`, tema inicial `"claro"`, e `definir()` só grava se `self._config` não for `None`.
- `__init__.py`: `__version__ = "1.0.0"` e `from .themes import ESPACO, MARCA, TAMANHOS, tema`.

- [ ] **Step 4: Instalar em modo editável**

Run: `.venv\Scripts\python -m pip install -e ".[dev]"`
Expected: termina com `Successfully installed ... tcm-ui-1.0.0`

- [ ] **Step 5: Escrever os testes de fumaça**

`tests/conftest.py`: `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")` antes de qualquer import do Qt (pytest-qt fornece a fixture `qapp`/`qtbot`).

```python
# tests/test_design_system.py
import re
from importlib.metadata import version
import tcm_ui
from tcm_ui.themes import tema, TEMAS

def test_versao_do_pacote_igual_a_do_codigo():
    assert version("tcm-ui") == tcm_ui.__version__ == "1.0.0"

def test_qss_sem_token_nao_resolvido(qapp):
    for nome in TEMAS:
        tema._nome = nome
        qss = tema._qss(tema.tokens())
        assert not re.search(r"@[a-z]", qss), f"token sem valor no tema {nome}"

def test_aplicar_tema_define_stylesheet_e_fusion(qapp):
    tema.aplicar(qapp)
    assert qapp.styleSheet()
    assert qapp.style().name().lower() == "fusion"

def test_alternar_emite_mudou(qtbot):
    tema._nome = "claro"
    with qtbot.waitSignal(tema.mudou) as sinal:
        tema.alternar()
    assert sinal.args == ["escuro"] and tema.escuro
```

- [ ] **Step 6: Rodar os testes**

Run: `.venv\Scripts\python -m pytest -q tests/test_design_system.py`
Expected: `4 passed`

---

### Task 2: Preferência de tema por organização/aplicação

**Files:**
- Modify: `src/tcm_ui/themes.py` (classe `GerenciadorTema`)
- Test: `tests/test_design_system.py`

**Interfaces:**
- Consumes: `GerenciadorTema` da Task 1.
- Produces: `tema.configurar(organizacao: str, aplicacao: str) -> None` — lê `aparencia/tema` de `QSettings(organizacao, aplicacao)` (valor inválido ou ausente → `"claro"`), passa a gravar ali em `definir()`, **não** aplica nem emite `mudou`.

- [ ] **Step 1: Escrever os testes**

```python
from PySide6.QtCore import QSettings

def test_configurar_le_preferencia_salva(qapp):
    QSettings("TCM-teste", "AppA").setValue("aparencia/tema", "escuro")
    tema.configurar("TCM-teste", "AppA")
    assert tema.nome == "escuro"

def test_definir_grava_na_aplicacao_configurada(qapp):
    tema.configurar("TCM-teste", "AppB")
    tema.definir("escuro")
    assert QSettings("TCM-teste", "AppB").value("aparencia/tema") == "escuro"

def test_valor_invalido_vira_claro(qapp):
    QSettings("TCM-teste", "AppC").setValue("aparencia/tema", "roxo")
    tema.configurar("TCM-teste", "AppC")
    assert tema.nome == "claro"
```

Fixture `autouse` em `conftest.py` que, ao final de cada teste, apaga as chaves de `QSettings("TCM-teste", *)` usadas (`clear()` em AppA, AppB, AppC e nas usadas nas tasks seguintes).

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest -q tests/test_design_system.py -k "configurar or definir_grava or invalido"`
Expected: FAIL com `AttributeError: 'GerenciadorTema' object has no attribute 'configurar'`

- [ ] **Step 3: Implementar `configurar`**

- [ ] **Step 4: Rodar todos os testes**

Run: `.venv\Scripts\python -m pytest -q`
Expected: todos passam

---

### Task 3: Componentes novos para a janela

**Files:**
- Modify: `src/tcm_ui/components.py`, `src/tcm_ui/icons.py`, `src/tcm_ui/styles.qss`
- Test: `tests/test_componentes.py`

**Interfaces:**
- Produces:
  - `BarraLateral.adicionar_secao(titulo: str) -> None` — insere `Texto(titulo.upper(), "secao")` na lista de itens, na ordem de chamada.
  - `BarraLateral.chaves() -> list[str]` — chaves dos itens na ordem de inserção.
  - `BarraLateral.selecionar(chave)` já existe (emite `navegou`); manter.
  - `Cabecalho.limpar_acoes() -> None` — tira do layout da direita e esconde todos os widgets adicionados com `adicionar()`. **Não destrói** (os botões pertencem ao módulo e são reaproveitados).
  - `CartaoErro(titulo: str, detalhes: str, parent=None)` — subclasse de `Cartao`; ícone `alerta` na cor `perigo`, `Texto(titulo, "subtitulo")` e `AreaLog` somente leitura com `detalhes`. Atributos públicos `titulo: str`, `detalhes: str`.
  - `EstadoVazio(titulo: str, descricao: str = "", icone: str = "info", parent=None)` — ícone grande centralizado + título + descrição. Atributos `titulo`, `descricao`.
  - `icons.svg/pixmap/icone/arquivo` com nome desconhecido usam `ICONES["info"]` (sem `KeyError`).
  - QSS: `QLabel[papel="secao"] { font-size: @fonte_rotulo; font-weight: 600; color: @texto_suave; padding-top: 12px; }`.

- [ ] **Step 1: Escrever os testes**

```python
from tcm_ui.components import BarraLateral, Cabecalho, Botao, CartaoErro, EstadoVazio, Texto
from tcm_ui import icons

def test_secao_e_itens_em_ordem(qtbot):
    barra = BarraLateral("X"); qtbot.addWidget(barra)
    barra.adicionar_secao("Catraca")
    barra.adicionar_item("catraca:relatorio", "Relatório", "arquivo")
    barra.adicionar_item("catraca:usuarios", "Usuários", "usuarios")
    assert barra.chaves() == ["catraca:relatorio", "catraca:usuarios"]
    textos = [w.text() for w in barra.findChildren(Texto) if w.property("papel") == "secao"]
    assert textos == ["CATRACA"]

def test_limpar_acoes_esconde_sem_destruir(qtbot):
    cab = Cabecalho("T"); qtbot.addWidget(cab)
    botao = Botao("A"); cab.adicionar(botao)
    cab.limpar_acoes()
    assert not botao.isVisible() and botao.parent() is not None

def test_cartao_erro_guarda_detalhes(qtbot):
    c = CartaoErro("Não foi possível abrir o Catraca", "Traceback ...")
    qtbot.addWidget(c)
    assert c.titulo.startswith("Não foi possível") and "Traceback" in c.detalhes

def test_icone_desconhecido_usa_info(qapp):
    assert icons.svg("nao_existe", "#000") == icons.svg("info", "#000")
    assert not icons.pixmap("nao_existe", "#000").isNull()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest -q tests/test_componentes.py`
Expected: FAIL com `ImportError: cannot import name 'CartaoErro'`

- [ ] **Step 3: Implementar os componentes, o fallback de ícone e a regra de QSS**

- [ ] **Step 4: Rodar todos os testes**

Run: `.venv\Scripts\python -m pytest -q`
Expected: todos passam

---

### Task 4: Atualizador parametrizado

**Files:**
- Create: `src/tcm_ui/atualizador.py` (portado de `Projeto_Agregados\atualizador.py`)
- Test: `tests/test_atualizador.py`

**Interfaces:**
- Produces (mesmo comportamento do original; mudam só os parâmetros):
  - `class ErroAtualizacao(Exception)`
  - `versao_tupla(texto: str) -> tuple[int, int, int]`
  - `buscar_atualizacao(repositorio: str, nome_exe: str, versao_atual: str) -> dict | None` → `{"versao", "url_exe", "url_sha"}`
  - `baixar_e_verificar(info: dict, destino: Path) -> None`
  - `aplicar_e_reiniciar(novo: Path, atual: Path | None = None, reiniciar: bool = True) -> None`
  - `limpar_temporarios(atual: Path | None = None) -> None`
  - Constantes iguais ao original: `API`, `HOSTS_PERMITIDOS`, `TAMANHO_MIN = 5 MiB`, `TAMANHO_MAX = 300 MiB`.
- Mensagem de repositório inválido passa a ser `"Repositório de atualização inválido."` (sem citar `config.ini`).

- [ ] **Step 1: Escrever os testes**

Os testes de rede substituem `atualizador._abrir` por um falso (`monkeypatch`) que devolve objetos com `read()`/context manager, sem acessar a internet.

```python
def test_versao_tupla():
    assert versao_tupla("v1.2") == (1, 2, 0)
    assert versao_tupla("1.10.3") > versao_tupla("1.9.9")

def test_repositorio_invalido():
    with pytest.raises(ErroAtualizacao, match="inválido"):
        buscar_atualizacao("sem-barra", "X.exe", "1.0.0")

def test_release_mais_nova_retorna_urls(monkeypatch): ...
    # release {"tag_name": "v1.1.0", assets: X.exe e X.exe.sha256}, atual 1.0.0
    # → {"versao": "1.1.0", "url_exe": ..., "url_sha": ...}

def test_release_igual_ou_antiga_retorna_none(monkeypatch): ...
def test_release_sem_sha256_levanta_erro(monkeypatch): ...      # match="não contém"
def test_404_retorna_none(monkeypatch): ...                     # _abrir levanta ErroAtualizacao("HTTP 404")
def test_sha_divergente_apaga_arquivo(monkeypatch, tmp_path): ...  # destino não existe depois
def test_arquivo_sem_MZ_rejeitado(monkeypatch, tmp_path): ...       # conteúdo ≥ TAMANHO_MIN sem "MZ"
def test_aplicar_troca_e_mantem_antigo(tmp_path):
    atual = tmp_path / "App.exe"; atual.write_bytes(b"MZvelho")
    novo = tmp_path / "App.exe.novo"; novo.write_bytes(b"MZnovo")
    aplicar_e_reiniciar(novo, atual, reiniciar=False)
    assert atual.read_bytes() == b"MZnovo"
    assert (tmp_path / "App.exe.antigo").read_bytes() == b"MZvelho"
def test_limpar_temporarios_remove_antigo_e_novo(tmp_path): ...
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest -q tests/test_atualizador.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'tcm_ui.atualizador'`

- [ ] **Step 3: Portar e parametrizar** (remover `from versao import VERSAO` e `NOME_EXE`; usar os parâmetros)

- [ ] **Step 4: Rodar todos os testes**

Run: `.venv\Scripts\python -m pytest -q`
Expected: todos passam

---

### Task 5: Contrato de módulo

**Files:**
- Create: `src/tcm_ui/modulo.py`
- Test: `tests/test_modulo.py`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class Pagina:
    chave: str
    titulo: str
    subtitulo: str
    icone: str

@dataclass(frozen=True)
class Contexto:
    usuario: str                          # "TCMSP\\fulano" (casca) ou login do Windows (avulso)
    pasta_dados: Path                     # = Modulo.pasta_dados
    modo: Literal["casca", "avulso"]
    log: logging.Logger
    janela: QWidget                       # pai para Modal e QFileDialog

class InstanciaModulo(Protocol):
    def widget(self, chave_pagina: str) -> QWidget: ...
    def acoes_cabecalho(self, chave_pagina: str) -> list[QWidget]: ...
    def pode_fechar(self) -> bool: ...

@dataclass(frozen=True)
class Modulo:
    id: str                               # regex ^[a-z][a-z0-9_]*$
    nome: str
    icone: str
    versao: str
    grupo_ad: str                         # ex.: "SF-RoboAgregado"
    repositorio: str                      # "Dono/Repo"
    nome_exe: str                         # termina em ".exe"
    pasta_dados: Path                     # onde o sistema já guarda dados hoje (spec 5.6)
    paginas: tuple[Pagina, ...]           # não vazia, chaves únicas
    criar: Callable[[Contexto], InstanciaModulo]

    @property
    def aplicacao_settings(self) -> str:  # Path(nome_exe).stem, ex.: "RoboAgregado"
```

`Modulo.__post_init__` levanta `ValueError` com mensagem que cita o campo: id fora do padrão, `paginas` vazia, chave de página repetida, `nome_exe` sem `.exe`, `repositorio` sem `/`.

- [ ] **Step 1: Escrever os testes**

`tests/conftest.py` ganha `fazer_modulo(**trocas) -> Modulo` (valores válidos padrão: `id="falso"`, 2 páginas `"a"` e `"b"`, `criar` devolvendo uma instância falsa com `QLabel` por página, `pode_fechar() -> True`, `acoes_cabecalho() -> []`).

```python
def test_modulo_valido(): assert fazer_modulo().aplicacao_settings == "Falso"   # nome_exe="Falso.exe"
@pytest.mark.parametrize("troca, campo", [
    ({"id": "Falso-1"}, "id"), ({"paginas": ()}, "paginas"),
    ({"paginas": (Pagina("a","A","",""), Pagina("a","B","",""))}, "chave"),
    ({"nome_exe": "Falso"}, "nome_exe"), ({"repositorio": "semdono"}, "repositorio"),
])
def test_modulo_invalido(troca, campo):
    with pytest.raises(ValueError, match=campo): fazer_modulo(**troca)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest -q tests/test_modulo.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'tcm_ui.modulo'`

- [ ] **Step 3: Implementar `modulo.py`**

- [ ] **Step 4: Rodar todos os testes**

Run: `.venv\Scripts\python -m pytest -q`
Expected: todos passam

---

### Task 6: JanelaPrincipal

**Files:**
- Create: `src/tcm_ui/janela.py`
- Test: `tests/test_janela.py`

**Interfaces:**
- Consumes: `Modulo`, `Pagina`, `Contexto`, `InstanciaModulo` (Task 5); `BarraLateral.adicionar_secao/chaves/selecionar`, `Cabecalho.definir_titulo/adicionar/limpar_acoes`, `CartaoErro`, `EstadoVazio`, `BotaoTema`, `Modal.confirmar` (Tasks 1 e 3).
- Produces:

```python
class JanelaPrincipal(QMainWindow):
    def __init__(self, modulos: Sequence[Modulo], *, nome_app: str, icone_app: str, usuario: str,
                 modo: Literal["casca", "avulso"], configuracoes: QSettings,
                 rodape: Sequence[str] = (),
                 sem_modulos: tuple[str, str] = ("Nenhum sistema disponível", "")): ...
    def abrir(self, id_modulo: str, chave: str) -> None
    @property
    def pagina_atual(self) -> tuple[str, str] | None          # (id_modulo, chave)
    @property
    def instancias(self) -> dict[str, InstanciaModulo]        # só as já criadas
    def modulos_com_tarefa(self) -> list[str]                  # nomes dos que vetaram o fechamento
```

Comportamento (spec 5.3):
- `id` repetido em `modulos` → `ValueError`.
- Barra lateral: marca = `nome_app`/`icone_app`; para cada módulo, `adicionar_secao(modulo.nome)` **só se houver mais de um módulo**; itens com chave `f"{id}:{pagina.chave}"`; rodapé = um `Texto(linha, "dica")` por item de `rodape`.
- Cabeçalho: título/subtítulo da página + ações da página (`acoes_cabecalho`) + `BotaoTema` sempre por último. Ao trocar de página, `limpar_acoes()` antes.
- Preguiçoso: `modulo.criar(contexto)` só no primeiro `abrir` de uma página do módulo; `widget(chave)` só no primeiro `abrir` daquela página; ambos guardados para os próximos.
- Contexto: `usuario`, `pasta_dados=modulo.pasta_dados`, `modo`, `log=logging.getLogger(f"sistema_financeiro.{id}")` no modo casca e `logging.getLogger(id)` no avulso, `janela=self`.
- Erro em `criar` → `CartaoErro(f"Não foi possível abrir o {modulo.nome}", traceback)` em todas as páginas daquele módulo (sem nova tentativa até reabrir o programa). Erro em `widget(chave)` → `CartaoErro` só naquela página. Erro em `acoes_cabecalho` → sem ações, só log. Tudo registrado com `log.exception`.
- Última página: grava `navegacao/ultima = "id:chave"` em `configuracoes` a cada troca; ao abrir a janela, usa esse valor se ainda existir na barra, senão a primeira chave.
- Sem módulos: área central = `EstadoVazio(*sem_modulos, icone="alerta")`, barra lateral sem itens (só marca e rodapé).
- Fechar (`closeEvent`): `modulos_com_tarefa()` chama `pode_fechar()` das instâncias criadas; exceção conta como veto (com `log.exception`). Se houver veto: `Modal.confirmar(self, "Fechar o programa?", f"Há uma tarefa em andamento em: {', '.join(nomes)}. Se fechar agora, ela será interrompida.", "Fechar mesmo assim")`; recusou → `event.ignore()`.
- Título da janela = `nome_app`; ícone = `icons.icone(icone_app, MARCA["primaria"], 32)`.

- [ ] **Step 1: Escrever os testes**

Fixture `janela(modulos, **kw)` em `conftest.py` cria `JanelaPrincipal` com `configuracoes=QSettings("TCM-teste", "Janela")`, `usuario="TCMSP\\teste"`, `modo="casca"`, `nome_app="Teste"`, `icone_app="painel"`.

```python
def test_ids_repetidos_rejeitados(qtbot): ...            # ValueError
def test_secoes_so_com_mais_de_um_modulo(qtbot): ...     # 1 módulo → 0 seções; 2 → 2
def test_abre_na_primeira_pagina(qtbot): ...             # pagina_atual == ("m1", "a")
def test_criar_so_no_primeiro_acesso(qtbot): ...         # contador em criar: 0 após init de m2; 1 após abrir m2 duas vezes
def test_contexto_recebe_dados_do_modulo(qtbot): ...     # usuario, modo, pasta_dados, log.name == "sistema_financeiro.m1"
def test_erro_em_criar_mostra_cartao_e_resto_funciona(qtbot): ...
def test_erro_em_uma_pagina_nao_afeta_outra(qtbot): ...  # widget("a") levanta; "b" abre QLabel
def test_acoes_trocam_com_a_pagina(qtbot): ...           # botão da página "a" escondido ao ir para "b"; BotaoTema sempre visível
def test_lembra_ultima_pagina(qtbot): ...                # abrir("m1","b"); nova janela abre em ("m1","b")
def test_ultima_pagina_invalida_cai_na_primeira(qtbot): ...  # navegacao/ultima = "sumiu:x"
def test_sem_modulos_mostra_estado_vazio(qtbot): ...     # findChild(EstadoVazio).titulo == mensagem recebida
def test_fechar_com_tarefa_pede_confirmacao(qtbot, monkeypatch): ...  # Modal.confirmar → False ⇒ janela continua aberta
def test_pode_fechar_com_excecao_conta_como_veto(qtbot): ...  # modulos_com_tarefa() == ["M1"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest -q tests/test_janela.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'tcm_ui.janela'`

- [ ] **Step 3: Implementar `JanelaPrincipal`**

Layout igual ao `App` do RoboAgregado (`app.py` linhas 141–175): `BarraLateral` à esquerda; à direita `Cabecalho` em cima e um `QStackedWidget` com as páginas. Cada página entra no stack dentro de uma `Pagina` (rolável) só se o widget do módulo não for ele mesmo um `QScrollArea`.

- [ ] **Step 4: Rodar todos os testes**

Run: `.venv\Scripts\python -m pytest -q`
Expected: todos passam

---

### Task 7: Verificador de atualização e modo avulso

**Files:**
- Create: `src/tcm_ui/atualizacao_ui.py`, `src/tcm_ui/avulso.py`
- Test: `tests/test_avulso.py`

**Interfaces:**
- Consumes: `atualizador.*` (Task 4), `JanelaPrincipal.modulos_com_tarefa()` (Task 6), `Modulo.aplicacao_settings` (Task 5), `tema.configurar/aplicar` (Task 2).
- Produces:

```python
class VerificadorAtualizacao(QObject):
    pronto = Signal(str, str)        # versao, caminho do .novo
    def __init__(self, janela: JanelaPrincipal, repositorio: str, nome_exe: str, versao_atual: str,
                 congelado: bool | None = None)   # None → getattr(sys, "frozen", False)
    def iniciar(self) -> None
```

- `iniciar()`: se não congelado, não faz nada. Senão `limpar_temporarios()`, e numa thread daemon: `buscar_atualizacao` → `baixar_e_verificar` para `sys.executable + ".novo"` → emite `pronto` (o sinal leva o resultado para a thread da GUI). Falhas só vão para `logging.getLogger("tcm_ui.atualizacao")`.
- Ao receber `pronto`: se `janela.modulos_com_tarefa()` não estiver vazio, apaga o `.novo` e registra "Atualização adiada: tarefa em andamento"; senão `Modal.informar(janela, "Atualização", f"Nova versão {versao} instalada.\nO programa será reiniciado agora.", "sucesso")`, `aplicar_e_reiniciar(novo)`, `janela.close()`, `os._exit(0)`. Em `ErroAtualizacao`: apaga o `.novo` e `Modal.informar(..., f"{erro}\nO programa continuará na versão atual.", "perigo")`.
- `rodar_avulso(modulo: Modulo, argv: list[str] | None = None) -> int` em `avulso.py`: cria `QApplication`, `tema.configurar("TCM", modulo.aplicacao_settings)`, `tema.aplicar(app)`, `JanelaPrincipal([modulo], nome_app=modulo.nome, icone_app=modulo.icone, usuario=getpass.getuser(), modo="avulso", configuracoes=QSettings("TCM", modulo.aplicacao_settings), rodape=[f"Versão {modulo.versao}"])`, `VerificadorAtualizacao(janela, modulo.repositorio, modulo.nome_exe, modulo.versao).iniciar()`, `janela.show()`, devolve `app.exec()`. Não consulta grupos do AD.

- [ ] **Step 1: Escrever os testes**

```python
def test_nao_congelado_nao_busca(qtbot, monkeypatch): ...      # buscar_atualizacao nunca chamado
def test_adiar_quando_ha_tarefa(qtbot, monkeypatch, tmp_path): ...
    # janela.modulos_com_tarefa → ["M1"]; emitir pronto("1.1.0", novo) ⇒ novo apagado, aplicar_e_reiniciar não chamado
def test_erro_ao_aplicar_apaga_novo_e_avisa(qtbot, monkeypatch, tmp_path): ...
def test_rodar_avulso_configura_tema_e_janela(qtbot, monkeypatch): ...
    # app.exec trocado por lambda: 0; tema.configurar chamado com ("TCM", "Falso");
    # janela tem 1 módulo e nenhuma seção
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python -m pytest -q tests/test_avulso.py`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar `atualizacao_ui.py` e `avulso.py`**

- [ ] **Step 4: Rodar todos os testes**

Run: `.venv\Scripts\python -m pytest -q`
Expected: todos passam

---

### Task 8: Vitrine, README e instalação pelo GitHub

**Files:**
- Create: `src/tcm_ui/demo.py`, `README.md`

**Interfaces:**
- Consumes: tudo acima.

- [ ] **Step 1: Portar a vitrine**

Portar `Projeto_Agregados\design_system\main.py` como um `Modulo` falso (`id="vitrine"`, páginas "Painel", "Componentes", "Configurações", mesmos dados fictícios) executado por `rodar_avulso`. `python -m tcm_ui.demo` abre a janela. Atualizador desligado na vitrine (não congelada).

- [ ] **Step 2: Conferir a vitrine na tela**

Run: `.venv\Scripts\python -m tcm_ui.demo`
Expected: janela abre com barra lateral, 3 páginas navegáveis e botão de tema funcionando nos dois temas. Fechar a janela.

- [ ] **Step 3: Escrever o README**

Seções: o que é; instalação (`pip install "tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.0.0"`); como criar um módulo (exemplo mínimo de `MODULO` + `main.py` com `rodar_avulso`); regra "só a janela aplica o tema"; regra `QSettings` com organização/aplicação explícitas (spec 5.6); como rodar testes e a vitrine.

- [ ] **Step 4: Testar a instalação limpa a partir da pasta (simula o pip da casca)**

```powershell
python -m venv $env:TEMP\tcmui-check
& $env:TEMP\tcmui-check\Scripts\python -m pip install C:\Users\erik.freitas\Projetos\Tcm-ui
& $env:TEMP\tcmui-check\Scripts\python -c "import tcm_ui, tcm_ui.janela, pathlib; from tcm_ui import themes; assert (pathlib.Path(themes.__file__).with_name('styles.qss')).exists(); print(tcm_ui.__version__)"
```

Expected: imprime `1.0.0` (o `.qss` foi empacotado). Depois apagar `$env:TEMP\tcmui-check`.

- [ ] **Step 5: Rodar a suíte completa**

Run: `.venv\Scripts\python -m pytest -q`
Expected: todos passam, sem avisos de erro do Qt

- [ ] **Step 6: Avisar o Erik**

O pacote está pronto para "Salvar versão" (commit + tag `v1.0.0` no `ErikDeFreitas/Tcm-ui`). Só ele decide quando. O plano 2 (RoboAgregado) instala `tcm-ui` dessa tag.
