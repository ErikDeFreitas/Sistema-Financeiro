# Sistema Financeiro — design

Data: 19/11/2026 · Autor: Erik (TI TCM) com Claude · Status: rascunho para aprovação

## 1. Intenção

Hoje o financeiro da TCM usa 5 mini-sistemas desktop, cada um com seu `.exe`, seu atualizador
e sua cópia do layout. Eles não são conectados: o usuário instala e atualiza vários programas.

O **Sistema Financeiro** é um único programa desktop que reúne esses sistemas numa barra lateral.
Cada funcionário vê só os sistemas liberados para ele, conforme os grupos do Active Directory.

Cada sistema continua vivendo no **seu próprio repositório**. Atualizar um sistema = mexer só no
repositório dele, publicar uma tag e subir a versão na casca.

## 2. Objetivos, não-objetivos e anti-objetivos

**Objetivos**
- Um `.exe` (`SistemaFinanceiro.exe`) distribuído por Release no GitHub, com atualização automática.
- Barra lateral com os sistemas permitidos ao usuário logado no Windows.
- Controle de acesso por grupos do AD local (`TCMSP`), sem tela de login.
- Um único design system (`tcm-ui`), baseado no do RoboAgregado, usado pela casca e pelos 5 sistemas.
- Cada sistema continua gerando o seu `.exe` avulso (com seu próprio atualizador).

**Não-objetivos**
- Troca de dados entre sistemas. Cada sistema é independente; só compartilham o lugar, o visual e o acesso.
- Repositório único (monorepo). Os repositórios continuam separados.
- Carregar módulos baixados em tempo de execução (plugins). Os módulos entram no `.exe` no build.
- Tela de administração de permissões. A TI administra pelo AD (Usuários e Computadores do AD).

**Anti-objetivos** (falha mesmo que funcione)
- Um sistema quebrar o visual de outro (ex.: tema/QSS de um sobrescrevendo outro).
- Um sistema com erro derrubar o programa inteiro.
- Atualizar um sistema exigir mexer em outro repositório além dele e da linha de versão na casca.
- O `.exe` avulso de algum sistema deixar de funcionar por causa da migração.

## 3. Contexto atual

Pasta de origem: `FileServer - TI\15. Automações\Projetos_Financeiro`.

| Sistema | Repositório | Hoje | Páginas atuais |
|---|---|---|---|
| RoboAgregado | ErikDeFreitas/Send_Agregados | `app.py`, `design_system/` (API em português), `atualizador.py`, `versao.py` | Extrato de fretes |
| Mesclador de PDFs | ErikDeFreitas/pdf-merge | pacotes `core/` + `ui/` (API em inglês) | Mesclar PDFs |
| Enviador PDF + XML | ErikDeFreitas/pdf-xml-mailer | pacotes `core/` + `ui/`, MSAL (conta Microsoft) | Enviar |
| Renomeador de CT-e | ErikDeFreitas/Renomeador_CTE | arquivos soltos na raiz, `components.py` | Separar e renomear (+ página "Design System" de demonstração) |
| Sistema Catraca | ErikDeFreitas/Projeto_Catraca | arquivos soltos na raiz, `components.py`, `requests` | Relatório de acessos, Usuários |

Todos são PySide6 e todos aplicam o tema **no aplicativo inteiro** (`app.setStyleSheet(...)`).
Os nomes de módulo se repetem (`core`, `ui`, `components`, `themes`, `icons`, `version`, `updater`, `main`).
Os dois fatos impedem juntar os sistemas num processo só sem reestruturar.

Máquinas no domínio AD `TCMSP`. A TI gerencia os grupos do AD. Não há acesso admin ao
Microsoft 365/Entra.

## 4. Abordagens consideradas

| | Abordagem | Trade-off |
|---|---|---|
| **A (escolhida)** | Cada sistema vira um **pacote pip** instalado do GitHub por tag; todos migram para um design system único `tcm-ui` | Mais trabalho de migração por sistema; resultado: um programa, um visual, sem dívida |
| B | Pacotes pip, mas cada sistema mantém seus componentes e aplica o tema só na própria tela | Migração rápida; 3 bibliotecas visuais divergindo; tema claro/escuro precisa ser repassado a cada tela |
| C | Lançador: a casca checa o AD e abre os `.exe` avulsos | Quase sem mudança; continuam 5 janelas; bloqueio contornável abrindo o `.exe` direto |
| — | git submodules | Descartado: mesma reestruturação do A e gestão de submodules mais frágil |

Erik escolheu **A**, com o layout do **RoboAgregado** como padrão.

## 5. Arquitetura

### 5.1 Repositórios

```
tcm-ui                 (NOVO)  design system + atualizador + utilidades comuns
Sistema-Financeiro     (NOVO)  casca: janela, barra lateral, acesso AD, build do .exe
Send_Agregados         módulo  robo_agregado
pdf-merge              módulo  mesclador
pdf-xml-mailer         módulo  enviador_pdf_xml
Renomeador_CTE         módulo  renomeador_cte
Projeto_Catraca        módulo  sistema_catraca
```

Dependências: casca → tcm-ui + 5 módulos; cada módulo → tcm-ui. Nenhum módulo depende de outro
nem da casca.

Instalação por `pip` a partir do GitHub, sempre com tag fixa:

```
# Sistema-Financeiro/requirements.txt
tcm-ui           @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.0.0
robo-agregado    @ git+https://github.com/ErikDeFreitas/Send_Agregados@v2.0.0
mesclador        @ git+https://github.com/ErikDeFreitas/pdf-merge@v3.0.0
enviador-pdf-xml @ git+https://github.com/ErikDeFreitas/pdf-xml-mailer@v2.0.0
renomeador-cte   @ git+https://github.com/ErikDeFreitas/Renomeador_CTE@v2.0.0
sistema-catraca  @ git+https://github.com/ErikDeFreitas/Projeto_Catraca@v2.0.0
```

(Os números de versão acima são ilustrativos. A migração de cada módulo é uma mudança grande e
justifica subir a versão maior.)

### 5.2 tcm-ui

Origem: `Projeto_Agregados/design_system/` (API em português: `Botao`, `Cartao`, `BarraLateral`,
`Cabecalho`, `Pagina`, `Modal`, `Tabela`, `GradeResponsiva`, `tema`, `ESPACO`, `TAMANHOS`, `MARCA`...).

Conteúdo:
- `tcm_ui.components`, `tcm_ui.themes`, `tcm_ui.icons`, `styles.qss` — vindos do RoboAgregado.
- Componentes que os outros sistemas usam e o RoboAgregado não tem são adicionados no estilo e
  com nomes em português (ex.: `CampoData`, `AreaSoltar` (drop zone), `EstadoVazio`,
  `Selo` em tabela). A lista exata sai do levantamento feito na migração de cada módulo.
- `tcm_ui.atualizador` — o atualizador do RoboAgregado (Release do GitHub + SHA-256 + hosts
  permitidos), parametrizado por repositório e nome do `.exe`. Usado pela casca e pelos `.exe` avulsos.
- `tcm_ui.modulo` — o contrato de módulo (seção 5.4). A pasta de dados é o campo
  `Modulo.pasta_dados` (seção 5.6); não existe `tcm_ui.dados`.
- `tcm_ui.janela` — `JanelaPrincipal` (barra lateral + cabeçalho + páginas), usada pela casca e
  pelo avulso. (Atualizado na implementação do plano 1.)
- `tcm_ui.avulso` — `rodar_avulso(MODULO)`; `tcm_ui.atualizacao_ui` — `VerificadorAtualizacao`.

Regra: **só a casca (ou a janela avulsa) chama `tema.aplicar(app)`**. Módulos nunca chamam
`setStyleSheet` no `QApplication`.

O gerenciador de tema guarda a preferência via `QSettings`; a organização/aplicação usada no
`QSettings` vem de quem inicia o app (casca ou janela avulsa), para o tema ser um só dentro da casca.

### 5.3 Casca (Sistema-Financeiro)

Layout = o do RoboAgregado: barra lateral à esquerda, cabeçalho no topo, área de conteúdo.

```
┌───────────────────────┬──────────────────────────────────────────────┐
│ ▣ Sistema Financeiro  │ Extrato de fretes             [ação] [☾]     │
│                       │ Envio dos extratos semanais aos agregados    │
│ ROBOAGREGADO          ├──────────────────────────────────────────────┤
│  ▸ Extrato de fretes  │                                              │
│ MESCLADOR             │         (tela da página selecionada)         │
│  ▸ Mesclar PDFs       │                                              │
│ CATRACA               │                                              │
│  ▸ Relatório          │                                              │
│  ▸ Usuários           │                                              │
│                       │                                              │
│ TCMSP\fulano          │                                              │
│ Versão 1.0.0          │                                              │
└───────────────────────┴──────────────────────────────────────────────┘
```

- A barra lateral agrupa por sistema: nome do sistema como título de seção, páginas do sistema
  como itens. (Proposta do Claude: sistemas com várias páginas, como a Catraca, não precisam de
  abas internas.)
- Só aparecem os sistemas permitidos. Ordem: a ordem de registro na casca.
- Ao abrir, seleciona a primeira página permitida. (Proposta: lembrar a última página aberta
  pelo usuário, via `QSettings`.)
- Cabeçalho: título/subtítulo da página + ações da página (ex.: "Credenciais" do RoboAgregado)
  + botão de tema.
- Rodapé da barra: usuário do Windows e versão da casca.
- Usuário sem nenhum sistema permitido: tela única "Você não tem acesso a nenhum sistema.
  Fale com a TI." com o nome do usuário (para a TI saber quem liberar).
- **Carregamento preguiçoso**: a tela de um módulo só é criada na primeira vez que o usuário
  abre uma página dele. Abrir o programa não executa código de módulos não usados.
- **Isolamento de erro**: se `criar_paginas()` ou a criação de uma página lançar exceção, aquela
  área mostra um cartão de erro ("Não foi possível abrir o <sistema>. Detalhes: ...") e grava o
  traceback no log; o resto do programa continua.
- **Fechar o programa**: a casca pergunta a cada módulo já carregado se pode fechar
  (`pode_fechar()`); se algum tiver tarefa em andamento (ex.: envio de e-mails), mostra um Modal
  de confirmação.
- **Atualização**: `tcm_ui.atualizador` apontando para `ErikDeFreitas/Sistema-Financeiro`,
  `SistemaFinanceiro.exe`. Verifica ao abrir (mesmo comportamento do RoboAgregado hoje).
  Dentro da casca os atualizadores dos módulos não rodam.

### 5.4 Contrato de módulo

Cada repositório de sistema passa a ter:

```
<repo>/
├── pyproject.toml              # nome do pacote, dependências (inclui tcm-ui), entry point
├── src/<pacote>/               # ex.: src/robo_agregado/
│   ├── __init__.py             # __version__
│   ├── modulo.py               # MODULO (abaixo)
│   └── ...                     # lógica e telas do sistema, imports sempre absolutos (<pacote>.x)
├── main.py                     # .exe avulso: tcm_ui.avulso.rodar_avulso(MODULO)
└── <Sistema>.spec              # build do .exe avulso
```

Entry point (no `pyproject.toml`):

```toml
[project.entry-points."sistema_financeiro.modulos"]
robo_agregado = "robo_agregado.modulo:MODULO"
```

Contrato (definido em `tcm_ui.modulo`):

```python
@dataclass
class Pagina:
    chave: str                     # única dentro do módulo, ex.: "relatorio"
    titulo: str                    # vai na barra lateral e no cabeçalho
    subtitulo: str
    icone: str                     # nome de ícone do tcm_ui.icons

@dataclass
class Modulo:
    id: str                        # ex.: "robo_agregado"; também nome da pasta de dados
    nome: str                      # ex.: "RoboAgregado"
    icone: str
    versao: str
    grupo_ad: str                  # ex.: "SF-RoboAgregado"
    repositorio: str               # ex.: "ErikDeFreitas/Send_Agregados" (atualizador avulso)
    nome_exe: str                  # ex.: "RoboAgregado.exe" (atualizador avulso)
    paginas: list[Pagina]
    criar: Callable[[Contexto], "InstanciaModulo"]

class InstanciaModulo(Protocol):
    def widget(self, chave_pagina: str) -> QWidget: ...          # tela da página
    def acoes_cabecalho(self, chave_pagina: str) -> list[QWidget]: ...  # botões no cabeçalho
    def pode_fechar(self) -> bool: ...                            # False = tarefa em andamento

@dataclass
class Contexto:
    usuario: str                   # "TCMSP\\fulano"
    pasta_dados: Path              # seção 5.6
    modo: Literal["casca", "avulso"]
    log: logging.Logger
    janela: QWidget                # pai para Modals e diálogos de arquivo
```

A lista de páginas é estática (declarada no `MODULO`), então a casca monta a barra lateral sem
executar código do módulo. `criar` só roda no primeiro acesso.

`rodar_avulso(MODULO)` cria a mesma janela (barra lateral + cabeçalho) só com aquele módulo,
aplica o tema, liga o atualizador do próprio módulo e não consulta o AD. Assim o `.exe` avulso
continua funcionando para qualquer pessoa que o tenha.

### 5.5 Controle de acesso

- Grupos no AD, um por sistema:
  `SF-RoboAgregado`, `SF-Mesclador`, `SF-EnviadorPDFXML`, `SF-RenomeadorCTE`, `SF-Catraca`,
  e `SF-Admin` (vê todos).
- A casca lê os grupos do **token do Windows** do processo (`win32security.GetTokenInformation`
  com `TokenGroups` + `LookupAccountSid`; pywin32). Inclui grupos aninhados, porque o token já
  vem expandido pelo controlador de domínio. Não consulta o AD pela rede.
- Comparação pelo nome do grupo sem o domínio, sem diferenciar maiúsculas/minúsculas.
- Funciona offline (logon em cache).
- Mudança de grupo só vale depois de logoff/logon do usuário. Documentar no README.
- Modo desenvolvimento: variável `SF_GRUPOS_DEV="SF-Mesclador;SF-Catraca"` substitui a leitura
  do token, **só quando a casca roda pelo Python** (não no `.exe` congelado).
- Limite assumido: é uma barreira organizacional. Quem tem um `.exe` avulso abre o sistema sem
  passar pela casca; quem descompila consegue pular a checagem. Proteção real dos dados fica nos
  recursos (permissões NTFS das pastas do FileServer com os mesmos grupos `SF-*`, conta Microsoft
  do próprio usuário no envio de e-mails). Proposta, fora deste projeto: a TI aplicar os grupos
  `SF-*` nas pastas do FileServer usadas por cada sistema.

### 5.6 Dados e configurações

**Decisão do Claude: cada sistema mantém exatamente onde guarda dados hoje.** Nada é movido.
Assim não há migração, não há risco de perder configuração, credencial ou histórico, e o `.exe`
avulso e a casca enxergam os mesmos dados.

Locais atuais (levantados no código, 19/11/2026):

| Sistema | Onde guarda |
|---|---|
| RoboAgregado | `%LOCALAPPDATA%\RoboAgregado\` (`config.ini`, `preferencias.json`, `log_envios.csv`, `.env` com credenciais) — ver `enviar_fretes.py` |
| Enviador PDF+XML | `%APPDATA%\EnviadorEmails\config.json`; cache MSAL em `%LOCALAPPDATA%\EnviadorEmails\token_cache.bin` (DPAPI) |
| Sistema Catraca | `QSettings("TCM", "SistemaCatraca")` (IP da catraca, usuário etc.) |
| Renomeador de CT-e | `QSettings("TCM", "RenomeadorCTE")` |
| Mesclador | `QSettings` só para o tema |

Regras:
- `Contexto.pasta_dados` aponta para a pasta atual do sistema (cada `MODULO` declara a sua).
- Módulos que usam `QSettings` passam a criar o objeto **com organização/aplicação explícitas**
  (`QSettings("TCM", "SistemaCatraca")`), nunca com o construtor vazio, porque dentro da casca a
  organização/aplicação globais são as da casca.
- Preferência de tema: uma só, da casca (`QSettings("TCM", "SistemaFinanceiro")`) quando dentro
  dela; no avulso, a do próprio sistema. As chaves de tema antigas de cada sistema são ignoradas
  dentro da casca.
- Log da casca: `%LOCALAPPDATA%\TCM\SistemaFinanceiro\logs\` (rotativo); cada módulo usa um
  logger filho (`sistema_financeiro.<id>`).

### 5.7 Build e release

- Casca: `build.ps1` cria venv limpo **fora do OneDrive**, `pip install -r requirements.txt`,
  roda os testes, roda PyInstaller (`--onefile`, sem console), gera `SistemaFinanceiro.exe` e
  `SistemaFinanceiro.exe.sha256`.
- PyInstaller precisa incluir os pacotes descobertos por entry point (`--collect-all` / `copy_metadata`
  para cada módulo e para `tcm-ui`, inclusive os `.qss` e ícones como dados do pacote).
- Release no GitHub `ErikDeFreitas/Sistema-Financeiro` com o `.exe` e o `.sha256` (formato que o
  atualizador já espera).
- Repositórios públicos: o atualizador não usa token, então as Releases precisam ser públicas
  (como já são hoje).
- Commits/tags/releases só quando o Erik disser "Salvar versão" (regra do usuário).

**Módulos — uma tag serve aos dois modos (decisão do Claude).**
`pdf-merge`, `pdf-xml-mailer`, `Renomeador_CTE` e `Projeto_Catraca` têm
`.github/workflows/release.yml`: tag `v*` gera o `.exe` avulso e publica a Release, e os `.exe`
avulsos se atualizam por ela. Isso continua assim. A mesma tag fixa a versão na casca. Como
consequência, **uma tag só é criada quando o `.exe` avulso daquela versão está testado**, porque
ela chega a todos os usuários do avulso.
- Na migração de cada módulo, o `release.yml` é ajustado para o layout `src/` e para instalar
  `tcm-ui` do GitHub.
- `__version__` passa a ser **commitado** igual à tag (o pip lê o que está no repositório).
  O workflow falha se a tag e o `__version__` forem diferentes, em vez de reescrever a versão.
- O RoboAgregado (sem workflow, com `build.ps1` local) ganha o mesmo `release.yml`.

### 5.8 Onde trabalhar

- Todos os repositórios são clonados de novo em `C:\Users\erik.freitas\Projetos\<repo>`, fora do
  OneDrive, ao lado da casca. Venvs e builds ficam lá.
- Verificado em 19/11/2026: as cópias do FileServer de RoboAgregado, Mesclador, Enviador e
  Renomeador não têm alterações pendentes (só arquivos do graphify no Enviador).
- Catraca: o repositório `ErikDeFreitas/Projeto_Catraca` é a fonte. A pasta do FileServer é igual
  a ele (só difere em fim de linha) mais `design_page.py`, que é a vitrine de demonstração dos
  componentes e não entra no projeto.
- As pastas do FileServer não são alteradas.

## 6. Migração

Ordem (cada passo termina com o `.exe` avulso do módulo funcionando):

1. **tcm-ui v1.0.0** a partir do `design_system/` do RoboAgregado + atualizador + contrato de módulo
   + `rodar_avulso`. Repositório novo `ErikDeFreitas/Tcm-ui` (criado pelo Erik em 19/11/2026).
2. **RoboAgregado** primeiro (já usa esse design system; serve de prova do contrato).
3. **Casca** com leitura de grupos AD, barra lateral agrupada, carregamento preguiçoso, isolamento
   de erro, atualizador. Primeira Release só com o RoboAgregado.
4. **Mesclador**, **Enviador PDF+XML**, **Renomeador de CT-e**, **Catraca** — um por vez:
   mover para `src/<pacote>/`, imports absolutos, trocar componentes pelos do `tcm-ui`, remover
   `app.setStyleSheet` próprio, expor `MODULO`, adaptar `main.py` para `rodar_avulso`, rodar os
   testes existentes. Depois subir a tag na casca e gerar nova Release.
5. Página "Design System" de demonstração do Renomeador não vai para a casca (vira demo do `tcm-ui`).

## 7. Testes

- Casca: leitura de grupos (com token simulado), filtro de módulos por grupo, `SF-Admin`,
  usuário sem acesso, módulo que lança exceção não derruba a janela, `pode_fechar` com veto.
- tcm-ui: aplicação de tema claro/escuro, atualizador (comparação de versão, hosts permitidos,
  SHA-256) — reaproveitar o que já existe.
- Módulos: os testes que cada repositório já tem continuam passando; mais um teste de fumaça que
  importa o `MODULO` pelo entry point e cria cada página com `pytest-qt` (offscreen).

## 8. Decisões tomadas

Pelo Erik:
- Abordagem A (pacotes pip por tag + design system único).
- Layout padrão = RoboAgregado.
- Navegação por barra lateral.
- `.exe` avulsos continuam existindo.
- Distribuição por Release no GitHub; repositório `ErikDeFreitas/Sistema-Financeiro`.
- Acesso por grupos do AD local `TCMSP`, administrado só pela TI.
- Sistemas não trocam dados entre si.
- Projeto em pasta local, fora do OneDrive: `C:\Users\erik.freitas\Projetos\Sistema-Financeiro`.

Pelo Claude (podem ser corrigidas):
- Nomes dos grupos `SF-*` e do pacote de cada módulo.
- Barra lateral agrupada por sistema, sem abas internas.
- Lembrar a última página aberta.
- Cada sistema mantém onde guarda dados hoje (sem migração); `QSettings` com nome explícito.
- Uma tag de módulo serve à casca e à Release do avulso; tag só com o avulso testado;
  `__version__` commitado igual à tag.
- Trabalhar em clones novos em `C:\Users\erik.freitas\Projetos\`; FileServer intocado.
- Carregamento preguiçoso e isolamento de erro por módulo.
- Atualizador do RoboAgregado vira o atualizador padrão do `tcm-ui`.

## 9. Fica a cargo de quem implementar

- Lista exata de componentes que faltam no `tcm-ui` (sai da migração de cada módulo).
- Formato do cartão de erro e da tela "sem acesso", dentro do visual do `tcm-ui`.
- Detalhes do `build.ps1` e do `.spec` do PyInstaller.
- Ícone da casca.
