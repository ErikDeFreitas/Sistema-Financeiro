# Sistema Financeiro — ideias e análise inicial

> Rascunho de 19/11/2026. Ainda não é plano aprovado; é a base para o brainstorming.

## Objetivo

Um único programa desktop (um `.exe`) com uma aba/tela por sistema do financeiro da TCM.
Cada sistema continua no **seu próprio repositório**; o Sistema-Financeiro é só a "casca" que
junta os módulos. Atualizar um sistema = mexer só no repositório dele.

Requisito extra: **controle de acesso** — cada funcionário só abre os módulos liberados para ele.

## Inventário (pasta `FileServer - TI\15. Automações\Projetos_Financeiro`)

| Projeto | Repositório | Stack | Design system | Observação |
|---|---|---|---|---|
| mesclador | ErikDeFreitas/pdf-merge | PySide6 | Variante A (`ui/components.py`, nomes em inglês) | pacotes `core/` + `ui/` |
| pdf-xml-mailer | ErikDeFreitas/pdf-xml-mailer | PySide6 + MSAL | Variante A (idêntica ao mesclador) | já faz login Microsoft (MSAL) |
| Renomeador_CTE | ErikDeFreitas/Renomeador_CTE | PySide6 | Variante B (`components.py` na raiz) | arquivos soltos na raiz |
| Sistema_Catraca | ErikDeFreitas/Projeto_Catraca (commit 5699b43 já é a versão PySide6; a pasta do FileServer não tem `.git` e tem um `design_page.py` que não está no repo) | PySide6 + requests | Variante B (+ PasswordInput, DateInput, ThemeFade) | versão oficial; a Flask/Docker foi descartada |
| Projeto_Agregados | ErikDeFreitas/Send_Agregados | PySide6 + pandas + pywin32 | Variante C (`design_system/`, nomes em português) | `config.ini` / `preferencias.json` locais |

Atualizado em 19/11/2026: Enviador_de_Emails (Flask) foi removido; Projeto Catraca virou só `Sistema_Catraca`.
Total: **5 projetos**.

Todos têm atualizador próprio (`atualizacao.py` / `updater.py` / `atualizador.py`).

## Problemas para juntar tudo num processo só

1. **Colisão de nomes de módulo.** `core`, `ui`, `components`, `themes`, `icons`, `version`, `updater`,
   `main` se repetem entre projetos. No mesmo processo Python só um de cada é carregado.
   → Cada projeto precisa virar um pacote com nome único (`mesclador/`, `renomeador_cte/`, ...).
2. **Cada app só sabe criar uma `QMainWindow`.**
   → Cada projeto expõe uma função de entrada que devolve um `QWidget` (a "tela" do módulo).
   O `main.py` de cada repositório continua existindo e embrulha essa tela numa janela,
   então o `.exe` avulso segue funcionando enquanto for útil.
3. **Três design systems diferentes (A, B, C).** Cada um tem seu `theme_manager`; trocar o tema
   na casca não chegaria nas telas dos módulos.
   → Extrair um repositório único `tcm-ui` (componentes + tema + ícones + QSS) e migrar os módulos
   para ele aos poucos. Partir da variante B (Catraca), que é a mais completa.
4. **Atualizadores duplicados.** No sistema unificado só a casca se atualiza.
   Os módulos perdem o atualizador quando rodam dentro da casca.
5. **Configurações locais** (`config.ini`, `preferencias.json`) em caminhos relativos ao `.exe`.
   → Padronizar: cada módulo grava em `%APPDATA%\TCM\SistemaFinanceiro\<modulo>\`.

## Arquitetura proposta

```
Sistema-Financeiro (repo casca)
├── requirements.txt          # cada módulo fixado por tag do seu repositório
│     tcm-ui         @ git+https://github.com/ErikDeFreitas/Tcm-ui@v1.0.0
│     pdf-merge      @ git+https://github.com/ErikDeFreitas/pdf-merge@v2.3.0
│     pdf-xml-mailer @ git+https://github.com/ErikDeFreitas/pdf-xml-mailer@v1.4.0
│     ...
├── main.py                   # janela principal: sidebar com os módulos permitidos
├── acesso.py                 # login + permissões
└── atualizador.py            # único atualizador
```

Contrato que cada módulo implementa (exemplo):

```python
# mesclador/modulo.py
MODULO = {
    "id": "mesclador",
    "nome": "Mesclador de PDFs",
    "icone": "files",
    "versao": __version__,
}

def criar_tela(contexto) -> QWidget:
    """contexto traz usuário logado, conta Microsoft, pasta de config, etc."""
```

A casca descobre os módulos por *entry points* do pip (grupo `sistema_financeiro.modulos`),
então incluir um módulo novo = adicionar uma linha no `requirements.txt`.

Fluxo de atualização de um módulo:
1. Altera e testa no repositório do módulo; cria tag nova (ex. `v2.4.0`).
2. Na casca, troca a tag no `requirements.txt`.
3. Gera o `.exe` da casca e publica a Release; o atualizador da casca distribui.

Descartado: carregar módulos baixados em tempo de execução (plugins). Com PyInstaller é frágil
(dependências, antivírus, versão do Python) e o ganho é pequeno.

## Controle de acesso

Possível, sim. Quem administra os acessos: **só a TI (Erik)**.

### 0. Grupos do Active Directory local (domínio `TCMSP`) — ESCOLHIDA
Descoberto em 19/11/2026: as máquinas estão no domínio AD local `TCMSP`, e a TI gerencia os
grupos do AD. Isso dispensa acesso admin ao Microsoft 365/Entra.

- Criar no AD um grupo por módulo: `SF-Mesclador`, `SF-MailerPDFXML`, `SF-RenomeadorCTE`,
  `SF-Catraca`, `SF-Agregados` (e opcionalmente `SF-Admin` = vê tudo).
- A casca lê os grupos do **token do Windows** do usuário logado (SSO: sem tela de login, sem senha).
  Em Python: `win32security.GetTokenInformation(token, TokenGroups)` + `LookupAccountSid`
  (pywin32 já é dependência do Agregados), ou `whoami /groups /fo csv` como fallback.
- Funciona offline (notebook fora da rede): o token vem do logon em cache.
- Desligamento: desativar a conta no AD bloqueia o Windows e o sistema juntos.
- Atenção: grupo adicionado/removido só vale **após o usuário fazer logoff/logon** (o token é
  montado no logon). Documentar isso para quem pedir acesso.
- Os mesmos grupos `SF-*` podem proteger as pastas do FileServer usadas por cada módulo (NTFS),
  dando segurança real além da "porta" do app.
- Para testes: variável/flag de desenvolvimento que simula grupos, só ativa em modo dev.

Opções abaixo ficam como alternativa, caso um dia o AD local saia (migração 100% nuvem):

### 1. Login Microsoft (Entra ID / Azure AD) + grupos
- O usuário entra com a conta corporativa (MSAL — o pdf-xml-mailer já usa).
- Permissões = grupos do Entra: `SF-Mesclador`, `SF-Agregados`, `SF-Catraca`...
  O token traz os grupos do usuário; a casca mostra só os módulos dos grupos dele.
- Gestão no portal da Microsoft/AD, sem cadastro próprio nem senha nova.
- Funcionário desligado: conta desativada → perde acesso a tudo automaticamente.
- Precisa: um *app registration* no Entra com a claim `groups` (ou consulta ao Graph `memberOf`).
- Sem internet: dá para guardar o último resultado em cache por algumas horas.

### 2. Usuário do Windows + arquivo de permissões no FileServer
- Casca lê o usuário logado no Windows e um `permissoes.json` numa pasta onde só a TI escreve
  (permissão NTFS de leitura para os demais).
- Simples, sem Entra. Mas depende do FileServer estar acessível e da permissão NTFS bem feita.

### 3. Login/senha próprios
- Não recomendado: mais uma senha, cadastro manual, risco de guardar senha errado.

### Limite importante
O bloqueio dentro do `.exe` é uma **porta organizacional**, não segurança forte: alguém com
conhecimento técnico consegue descompilar um executável PyInstaller e pular a checagem.
A proteção real vem dos recursos que o módulo usa:
- e-mails saem pela conta Microsoft do próprio usuário (permissões do Exchange);
- planilhas/pastas no FileServer/SharePoint com permissão por grupo (os mesmos grupos `SF-*`).
Com a opção 1, os mesmos grupos servem para o app **e** para esses recursos — fica coerente.

## Ordem sugerida

1. Criar `tcm-ui` a partir da variante B e publicar `v1.0.0`.
2. Criar no AD os grupos `SF-*`. Criar a casca com sidebar e leitura dos grupos do token do
   Windows (com um módulo "fake").
3. Migrar o módulo mais simples primeiro (Renomeador_CTE ou mesclador): pacote com nome único
   + `criar_tela()` + `tcm-ui`.
4. Migrar os demais, um por vez. Cada migração mantém o `.exe` avulso funcionando até a casca
   estar estável.
5. Desligar os `.exe` avulsos e os atualizadores individuais.

## Perguntas em aberto

Respondidas em 19/11/2026:
- Enviador_de_Emails: removido.
- Catraca: oficial é a desktop `Sistema_Catraca`.
- Permissões: administradas só pela TI.
- Acesso: grupos do AD local `TCMSP` (opção 0). Entra ID fica de reserva.

- Navegação: **sidebar**.
- `.exe` avulsos: **continuam existindo** (cada repo segue gerando seu executável isolado, com seu
  atualizador). Ou seja: o módulo precisa rodar nos dois modos — dentro da casca e sozinho.
- Distribuição da casca: **Release no GitHub** (mesmo esquema dos apps atuais).
- Catraca: repo `ErikDeFreitas/Projeto_Catraca`.

Próximo passo: brainstorming formal → spec → plano de implementação.
