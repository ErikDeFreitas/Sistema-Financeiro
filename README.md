# Sistema Financeiro

Programa desktop único (PySide6) que reúne os sistemas do financeiro da TCM numa barra
lateral. Cada sistema vive no seu próprio repositório e é descoberto por entry point
(grupo `sistema_financeiro.modulos`); esta "casca" só mostra os que o usuário pode usar.

## Como pedir acesso

O acesso é por grupo do Windows (AD): um grupo `SF-*` por sistema, e `SF-Admin` enxerga
todos. Peça ao TI para entrar no grupo do sistema que precisa:

- `SF-RoboAgregado`
- `SF-Mesclador`
- `SF-EnviadorPDFXML`
- `SF-RenomeadorCTE` (Renomeador de CT-e e Renomeador de XML)
- `SF-Catraca`
- `SF-Admin` (vê todos os sistemas)

A mudança só vale depois de **sair e entrar de novo no Windows** (bloquear a tela ou reiniciar o
programa não basta). Sem nenhum grupo, o programa mostra a tela "sem acesso".

Se a pessoa entrou no grupo e continua sem acesso depois de sair e entrar, espere alguns minutos
(a mudança precisa chegar a todos os controladores de domínio) e repita. Para conferir os grupos da
sessão: `whoami /groups | findstr /i "SF-"`.

Isto é uma barreira organizacional (esconde o que o usuário não deve usar), não uma proteção
dos dados: quem tem acesso às pastas de rede continua tendo.

## Onde fica o log

`%LOCALAPPDATA%\TCM\SistemaFinanceiro\logs\sistema_financeiro.log`

## Desenvolver

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e . pytest pytest-qt
python -m pytest -q
python main.py
```

- Fora do `.exe`, a variável `SF_GRUPOS_DEV` (grupos separados por ponto e vírgula) substitui a
  leitura dos grupos do Windows, para testar o filtro. No `.exe` ela é ignorada.
- `SISTEMA_FINANCEIRO_DADOS` troca a pasta de dados (use uma pasta temporária nos testes).
- `python main.py --verificar` carrega todos os sistemas instalados e abre cada página;
  devolve 0 se estiver tudo certo. O `build.ps1` roda isso no `.exe` gerado.

## Adicionar um sistema

1. Acrescente a linha dele em `requirements.txt` (repositório + tag).
2. Coloque o id dele em `descoberta.ORDEM` (`src/sistema_financeiro/descoberta.py`).
3. Se ele usa bibliotecas que o PyInstaller não enxerga, acrescente as importações ocultas
   em `build.ps1` (com um comentário dizendo de qual sistema vêm).

## Gerar o executável e lançar uma versão

```powershell
powershell -File build.ps1
```

Cria um venv limpo em `build\venv`, instala `requirements.txt`, roda os testes, gera
`dist\SistemaFinanceiro.exe` e o `.sha256`, e confere o `.exe` com `--verificar`.

**Modo local (`-Local`)**: `powershell -File build.ps1 -Local` instala `..\Tcm-ui`,
`..\Send_Agregados`, `..\pdf-merge`, `..\pdf-xml-mailer`, `..\Renomeador_CTE` e `..\Projeto_Catraca` das pastas vizinhas (`requirements-local.txt`), para testar
antes de criar as tags dos repositórios dos sistemas.

Para lançar: suba `__version__` em `src/sistema_financeiro/__init__.py`, crie a tag
`vX.Y.Z` igual à versão e envie (`git push origin vX.Y.Z`). O workflow `Release` gera o
`.exe` e o `.sha256` e os anexa à Release; ele falha se a tag for diferente de `__version__`.
