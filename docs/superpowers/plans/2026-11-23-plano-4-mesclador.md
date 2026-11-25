# Plano 4 — Mesclador de PDFs no Sistema Financeiro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar o Mesclador de PDFs (`ErikDeFreitas/pdf-merge`) para módulo `mesclador` com o visual do `tcm-ui`, mantendo o `MesclarPDFs.exe` avulso, e incluí-lo na casca.

**Architecture:** Mesmo caminho do RoboAgregado (plano 2): pacote `src/mesclador/` com `MODULO` no entry point `sistema_financeiro.modulos`, tela reescrita com os componentes do `tcm-ui`, `main.py` → `rodar_avulso`. O `tcm-ui` ganha o que o Mesclador usa e ainda não existe (tom "aviso", etiqueta clicável, ícones). As dependências entre pacotes passam a usar faixa de versão no `pyproject.toml` e o pino por tag só nos `requirements.txt`, para um módulo não travar a versão do `tcm-ui` dos outros dentro da casca.

**Tech Stack:** Python 3.13, PySide6, pypdf, Pillow, pytest + pytest-qt (offscreen), PyInstaller, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-19-sistema-financeiro-design.md` (seções 2, 5.2, 5.4, 5.6, 5.7, 6 passo 4, 7).

## Global Constraints

- **Sem commit, push, tag ou release** até o Erik dizer "Salvar versão". Nenhum passo commita.
- Repositórios públicos: nada de admin do domínio, detalhes de rede, credenciais ou dados reais (faturas, CT-es, CNPJ) em código, testes ou docs.
- Repositórios em `C:\Users\erik.freitas\Projetos\` (`Tcm-ui`, `Send_Agregados`, `pdf-merge`, `Sistema-Financeiro`).
- Versões: `tcm-ui` **1.2.0**, `robo-agregado` **2.0.1**, `mesclador` **3.0.0**, casca **1.1.0** (`__version__` commitado igual à tag; workflow falha se diferente).
- Dependência entre pacotes: no `pyproject.toml` só faixa de versão (`tcm-ui>=1.2.0`); o pino `@ git+https://github.com/ErikDeFreitas/Tcm-ui@vX.Y.Z` fica no `requirements.txt` de cada repositório.
- Módulos nunca chamam `setStyleSheet` no `QApplication`; `QSettings` sempre com organização/aplicação explícitas.
- `MODULO` do Mesclador: id `mesclador`, nome `Mesclador de PDFs`, ícone `camadas`, grupo `SF-Mesclador`, repositório `ErikDeFreitas/pdf-merge`, executável `MesclarPDFs.exe`, pasta de dados `%LOCALAPPDATA%\MesclarPDFs` (variável `MESCLADOR_DADOS` para testes), página `Pagina("mesclar", "Mesclar PDFs", "Junte fatura, CVA, CT-es e anexos em um único PDF por pasta.", "camadas")`.
- O `.exe` avulso continua `MesclarPDFs.exe`, com `MesclarPDFs.exe.sha256` no formato `"<hash>  MesclarPDFs.exe"` (o atualizador da 2.1.0 lê `split()[0]`): os usuários atuais atualizam sozinhos para a 3.0.0.
- Regras de mesclagem (`core/mesclagem.py`) não mudam: só mudam de lugar e de imports.
- Nada toca o registro do Windows nem pastas reais de dados nos testes e conferências.

## Review Focus

1. **Fechar o programa (casca ou avulso) no meio de uma mesclagem**: confirma, pede para parar depois da pasta atual e espera a thread terminar; nunca "QThread destroyed while running". Teste em `test_instancia.py`.
2. **Pasta com subpasta sem PDF principal / arquivo corrompido**: a fatura vira "Pulada"/"Erro" na tabela e as outras continuam. Teste em `test_mesclagem.py`.
3. **Casca com RoboAgregado 2.0.1 e Mesclador 3.0.0 juntos**: `pip install -r requirements.txt` resolve um único `tcm-ui` 1.2.0 sem conflito. Coberto pela Task 6 (build limpo).
4. **Usuário do `MesclarPDFs.exe` 2.1.0 recebe a 3.0.0**: nomes dos arquivos da Release e formato do `.sha256` iguais aos de hoje. Teste do build na Task 5.
5. **Clique no status da linha** abre os detalhes da fatura (etiqueta clicável dentro da tabela). Teste em `test_tela.py` e no `tcm-ui`.

---

### Task 1: tcm-ui 1.2.0 — tom "aviso", etiqueta clicável e ícones

**Files (em `C:\Users\erik.freitas\Projetos\Tcm-ui`):** Modify `src/tcm_ui/themes.py`, `src/tcm_ui/styles.qss`, `src/tcm_ui/components.py`, `src/tcm_ui/icons.py`, `src/tcm_ui/__init__.py`, `pyproject.toml`, `README.md`, `src/tcm_ui/demo.py` (mostrar os novos), tests.

**Interfaces — Produces:**
- Tokens `aviso` (`#D97706` nos dois temas), `aviso_suave` (claro `#FFFBEB`, escuro `rgba(217, 119, 6, 0.18)`).
- Tom `"aviso"` aceito em `Etiqueta`, `CartaoIndicador` (`QLabel#IconeIndicador[tom="aviso"]`) e `Modal(..., tom="aviso")` (ícone `alerta` na cor `aviso`).
- `Etiqueta(texto, tom="neutro", clicavel=False, dica="")` com sinal `clicada = Signal()`; clicável → cursor de mão, emite `clicada` no clique esquerdo; `dica` vira tooltip.
- Ícones: `camadas`, `executar` (play), `borracha`, `link_externo`, `copiar`, `check_circulo`, `x_circulo`, `pastas` (SVGs no mesmo estilo de traço; podem vir de `..\pdf-merge\ui\icons.py`).
- `__version__ = "1.2.0"`.

- [ ] Step 1: testes que falham — `test_etiqueta_clicavel_emite` (qtbot.mouseClick → `clicada` emitido; não clicável não emite), `test_tom_aviso_tem_cor` (tokens nos dois temas; QSS gerado contém `[tom="aviso"]` para etiqueta e indicador), `test_icones_novos_renderizam` (cada nome gera pixmap não nulo), `test_modal_tom_aviso`.
- [ ] Step 2: rodar e ver falhar; Step 3: implementar; Step 4: suíte inteira passa (85 + novos).
- [ ] Step 5: não commitar.

---

### Task 2: robo-agregado 2.0.1 — dependência do tcm-ui por faixa

**Files (em `C:\Users\erik.freitas\Projetos\Send_Agregados`):** Modify `pyproject.toml`, `src/robo_agregado/__init__.py`, `.github/workflows/release.yml`, `build.ps1` (se instalar dependências), `README.md`; Create `requirements.txt`.

- `pyproject.toml`: `tcm-ui>=1.1.0` no lugar do `@ git+...@v1.1.0`. `__version__ = "2.0.1"`.
- `requirements.txt`: `tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.2.0` (usado pelo build e pelo workflow).
- Workflow: `pip install -r requirements.txt . pytest pytest-qt pyinstaller`.
- README: como instalar para desenvolver (`-r requirements.txt` ou `..\Tcm-ui` editável).
- [ ] Step 1: teste `test_pyproject_sem_pino_de_url` (lê o `pyproject.toml` com `tomllib`; nenhuma dependência contém `@`) — falha antes.
- [ ] Step 2: implementar; suíte inteira (22 + 1) passa num venv com `..\Tcm-ui` 1.2.0 editável.
- [ ] Step 3: não commitar.

---

### Task 3: pacote `mesclador` — núcleo e testes

**Files (em `C:\Users\erik.freitas\Projetos\pdf-merge`):**
- Move (git mv): `core/mesclagem.py` → `src/mesclador/mesclagem.py`; `core/worker.py` → `src/mesclador/worker.py`; `core/__main__.py` → `src/mesclador/__main__.py`.
- Create: `pyproject.toml`, `src/mesclador/__init__.py`, `src/mesclador/dados.py`, `tests/conftest.py`, `tests/test_mesclagem.py`.
- Delete: `core/__init__.py`, `core/atualizacao.py`, `version.py`, `requirements.txt` (recriado na Task 5 só com o pino do `tcm-ui`).

**Interfaces — Produces:** `mesclador.__version__ = "3.0.0"`; `mesclador.dados.PASTA: Path` (`MESCLADOR_DADOS` ou `%LOCALAPPDATA%\MesclarPDFs`, sem criar nada no import); `mesclador.mesclagem` com a mesma API de hoje; `mesclador.worker.MesclarWorker` (sem o `BaixarAtualizacaoWorker`, que vai embora com o atualizador próprio); `python -m mesclador "C:\Pasta"` como hoje `python -m core`.

- `pyproject.toml` no modelo do `Send_Agregados`: `name = "mesclador"`, versão dinâmica, `dependencies = ["tcm-ui>=1.2.0", "pypdf>=6.16", "pillow>=12.3"]`, extra `dev`, entry point `mesclador = "mesclador.modulo:MODULO"` (o `modulo.py` chega na Task 4), `testpaths`.
- [ ] Step 1: testes que falham (`tests/test_mesclagem.py`, PDFs gerados na hora com `pypdf.PdfWriter.add_blank_page` e imagens com Pillow, em `tmp_path`): `test_listar_subpastas_ignora_arquivos`, `test_subpasta_sem_principal_e_pulada_e_as_outras_seguem`, `test_pdf_corrompido_vira_erro_ou_pulada_sem_derrubar`, `test_imagem_jfif_entra_como_pagina`, `test_cancelado_para_depois_da_pasta_atual`, `test_cli_devolve_codigo`. Ler `mesclagem.py` antes para usar os nomes de arquivo reais (`2`, `3`, `4`, `7`, principal).
- [ ] Step 2: rodar e ver falhar; Step 3: mover e ajustar imports (absolutos `mesclador.x`); Step 4: passar.
- [ ] Step 5: não commitar.

---

### Task 4: tela, instância e `MODULO`

**Files:** Create `src/mesclador/tela.py`, `src/mesclador/instancia.py`, `src/mesclador/modulo.py`, `tests/test_tela.py`, `tests/test_instancia.py`, `tests/test_modulo.py`.

**Interfaces:**
- Consumes: Task 1 (`Etiqueta(..., clicavel=True)`, tom `aviso`, ícones), `tcm_ui.components` (`Pagina`, `Cartao`, `CartaoIndicador`, `GradeResponsiva`, `Campo`, `CampoTexto`, `CampoPesquisa`, `Selecao`, `Botao`, `BarraProgresso`, `Tabela`, `Modal`, `Texto`), `tcm_ui.modulo`.
- Produces: `tela.TelaMesclar(contexto, pasta_inicial="")` (subclasse de `tcm_ui.components.Pagina`), propriedade `rodando`, métodos `parar()`, `aguardar()`; `tela.DialogoDetalhes(resultado, versao, parent)`; `instancia.Mesclador` (`widget("mesclar")` cria uma vez, outra chave → `KeyError`; `acoes_cabecalho` → `[]`; `pode_fechar` → `not tela.rodando`); `instancia.PASTA_INICIAL: str = ""` (o `main.py` avulso preenche com a pasta passada na linha de comando); `modulo.MODULO` com os valores dos Global Constraints, importando a instância só dentro de `criar`.

- Tela: mesma tela de hoje (`main.py:MesclarPage` + `DetalhesModal`) com os componentes do `tcm-ui`: cartão "Origem" (campo da pasta + Procurar + Mesclar tudo/Cancelar/Limpar + progresso), 4 indicadores (Faturas `primaria`, Geradas `sucesso`, Com aviso `aviso`, Não geradas `perigo`), cartão "Resultado" (pesquisa + filtro de status + tabela; ação "Abrir pasta"). Status na tabela = `Etiqueta(..., clicavel=True)` que abre `DialogoDetalhes`; duplo clique abre o PDF gerado. Guardar o `Resultado` de cada linha no item (`Qt.UserRole + 1`). Diálogos de arquivo e Modais com `contexto.janela` como pai.
- Ao sair: `tela` liga `QApplication.aboutToQuit` → `parar()` + `aguardar()`, para a thread terminar antes de o processo acabar (a confirmação já vem do `pode_fechar` na `JanelaPrincipal`).
- [ ] Step 1: testes que falham — `test_modulo.py` (valores do `MODULO`, entry point carrega, `import mesclador.modulo` não importa `pypdf` nem PySide widgets pesados — conferir `sys.modules`), `test_instancia.py` (widget único, `KeyError`, `pode_fechar` falso enquanto `rodando`, `aboutToQuit` para e espera a thread), `test_tela.py` (pasta inexistente → erro no campo; mesclar uma pasta gerada em `tmp_path` preenche tabela e indicadores; clicar na etiqueta de status abre o diálogo — trocar `DialogoDetalhes.exec` por um falso; filtro por status esconde linhas).
- [ ] Step 2: falhar; Step 3: implementar; Step 4: passar (suíte inteira).
- [ ] Step 5: não commitar.

---

### Task 5: `.exe` avulso, build e Release do Mesclador

**Files:** Modify `main.py` (reescrito), `README.md`, `.gitignore`, `.github/workflows/release.yml`; Create `build.ps1`, `requirements.txt`; Delete `ui/`, `MesclarPDFs.spec`; mantém `assets/MesclarPDFs.ico`.

- `main.py`: se `sys.argv[1]` for uma pasta existente → `instancia.PASTA_INICIAL`; `sys.exit(rodar_avulso(MODULO))`.
- `requirements.txt`: `tcm-ui @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.2.0`.
- `build.ps1` no modelo do `Send_Agregados\build.ps1` (`-Python`), com `--icon assets\MesclarPDFs.ico`, `--collect-data tcm_ui --collect-data mesclador`, os `--exclude-module` do `.spec` atual que ainda fazem sentido, e `dist\MesclarPDFs.exe.sha256` = `"<hash>  MesclarPDFs.exe\n"`.
- `release.yml` no modelo do `Send_Agregados` (2.0.1): instala `-r requirements.txt . pytest pytest-qt pyinstaller`, confere tag = `mesclador.__version__`, roda testes, `./build.ps1 -Python python`, publica `MesclarPDFs.exe` + `.sha256`.
- README: o que faz, uso (janela, pasta na linha de comando, `python -m mesclador`), desenvolver, lançar versão, módulo da casca (grupo `SF-Mesclador`).
- [ ] Step 1: teste `test_build_usa_nome_do_exe` (o `build.ps1` e o `MODULO.nome_exe` usam `MesclarPDFs.exe`; o `.sha256` gerado tem o formato acima).
- [ ] Step 2: `powershell -File build.ps1` (venv do repositório com `..\Tcm-ui` editável) gera `dist\MesclarPDFs.exe`; rodar com `MESCLADOR_DADOS` temporário e `QT_QPA_PLATFORM=offscreen` por alguns segundos e fechar (sem erro no log). O controlador confere a janela real (capturas pelo Python, nunca da tela).
- [ ] Step 3: não commitar.

---

### Task 6: casca 1.1.0 com o Mesclador

**Files (em `C:\Users\erik.freitas\Projetos\Sistema-Financeiro`):** Modify `requirements.txt`, `requirements-local.txt`, `build.ps1`, `pyproject.toml`, `src/sistema_financeiro/__init__.py`, `README.md`, `CLAUDE.md`; tests.

- `requirements.txt`: `tcm-ui@v1.2.0`, `robo-agregado@v2.0.1`, `mesclador@v3.0.0`. `pyproject.toml`: `tcm-ui>=1.2.0`. `__version__ = "1.1.0"`.
- `-Local`: agora que ninguém fixa URL no `pyproject.toml`, instala `../Tcm-ui ../Send_Agregados ../pdf-merge .` direto (sem `--no-deps`); `requirements-local.txt` lista esses caminhos.
- Teste: `verificar_modulos()` com os dois módulos instalados → 0; ordem na barra: RoboAgregado, Mesclador de PDFs (agora aparecem os títulos de seção).
- [ ] Step 1: venv da casca com os quatro repositórios locais editáveis; suíte passa.
- [ ] Step 2: `powershell -File build.ps1 -Local` → `dist\SistemaFinanceiro.exe`, `--verificar` OK com os dois módulos. O controlador confere a janela (capturas pelo Python com `SF_GRUPOS_DEV`).
- [ ] Step 3: README (grupo `SF-Mesclador`), `CLAUDE.md` ("Onde paramos"; ordem do "Salvar versão": Tcm-ui v1.2.0 → Send_Agregados v2.0.1 → pdf-merge v3.0.0 → Sistema-Financeiro v1.1.0; a TI cria `SF-Mesclador`).
- [ ] Step 4: não commitar.
