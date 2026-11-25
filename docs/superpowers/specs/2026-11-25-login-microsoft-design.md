# Login Microsoft padronizado (Enviador + RoboAgregado)

Data: 25/11/2026. Status: rascunho para aprovação do Erik.

## Por quê

A Microsoft desliga o SMTP com autenticação básica (usuário e senha) por padrão no fim de dezembro de
2026, e a remoção definitiva vem depois. O RoboAgregado ainda envia assim: a senha da conta
compartilhada do financeiro fica gravada num `.env` em cada computador. O Enviador de PDF + XML já
usa o login Microsoft (OAuth), com o aplicativo registrado na Azure pelo Erik, e foi testado com a
conta real.

O objetivo é padronizar: um só login Microsoft, num lugar só, usado pelos dois sistemas. No
RoboAgregado, cada pessoa entra com a própria conta e envia **como** a caixa do financeiro.

## Objetivos

- O RoboAgregado envia por SMTP com OAuth (XOAUTH2), como o Enviador. Cada pessoa usa a própria
  conta Microsoft, e o remetente é a caixa compartilhada ("Enviar como").
- O código de login Microsoft fica no `Tcm-ui`, e Enviador e RoboAgregado usam esse mesmo código.
- O login é compartilhado: quem entrou em um dos sistemas já está logado no outro, na casca e nos
  `.exe` avulsos.
- Quem já está logado no Enviador continua logado depois da atualização.
- A senha gravada no `.env` do RoboAgregado é apagada, e o CCO salvo nele é mantido.

## Fora do escopo

- Microsoft Graph (envio pela API em vez de SMTP). Fica como plano B, caso a Microsoft restrinja
  também o SMTP com OAuth.
- Mudanças no envio do Enviador (ele continua enviando como a própria conta logada).
- Novas permissões no aplicativo da Azure: o escopo continua `SMTP.Send` (delegado).

## Não pode acontecer

- Nenhuma senha gravada em disco depois da migração.
- O RoboAgregado parar de enviar para quem usa o método Outlook (`metodo = outlook`).
- Um extrato ir com o remetente errado sem a pessoa perceber: o remetente aparece na confirmação de
  envio, como hoje.
- Exigir que quem já usa o Enviador entre de novo só por causa da atualização.

## Restrições

- O `Tcm-ui` e o `Send_Agregados` são públicos. O ID do aplicativo e o ID do locatário não são
  segredos (cliente público) e já estão no `pdf-xml-mailer`, também público. Nenhum e-mail real
  entra nos repositórios.
- A TI dá a permissão **"Enviar como"** (Send As) na caixa do financeiro a cada pessoa que envia.
  "Enviar em nome de" (Send on Behalf) não serve para este envio por SMTP. Também é a TI que mantém o
  SMTP autenticado habilitado na conta de cada pessoa, como já está para quem usa o Enviador.
- Para o `msal` não pesar em quem não envia e-mail, ele é dependência opcional do `Tcm-ui`
  (`tcm-ui[microsoft]`).
- O `config.ini` do RoboAgregado só é trocado quando chega uma versão mais nova (já é assim).

## Abordagens consideradas

1. **Login Microsoft + SMTP XOAUTH2, no `Tcm-ui` (escolhida pelo Erik).** Reaproveita o que já
   funciona no Enviador: o mesmo aplicativo, o mesmo escopo e o mesmo envio.
2. **Microsoft Graph `sendMail`.** Escapa de futuras regras sobre SMTP, mas exige uma permissão nova
   com aprovação do administrador e um envio diferente do do Enviador. Fica como plano B.
3. **Outlook instalado (`metodo = outlook` + `enviar_como`).** Já existe e não exige programar nada,
   mas depende do Outlook clássico aberto no computador e é mais lento. Continua disponível como
   opção no `config.ini`.

## Desenho

### `Tcm-ui` 1.6.0: `tcm_ui.microsoft`

- `CLIENT_ID`, `TENANT_ID` e `ESCOPOS` (`SMTP.Send`) num só lugar: são os do aplicativo do Enviador.
- `Conta`: o que hoje é `enviador_pdf_xml.conta.Conta` (`email`, `entrar`, `token`, `sair`), com
  `ContaNaoConfigurada` e `FalhaLogin`.
- O cache de tokens é criptografado com DPAPI em `%LOCALAPPDATA%\TCM\ContaMicrosoft\token_cache.bin`,
  compartilhado por todos os sistemas. Na primeira vez, se esse arquivo não existir e existir o
  cache antigo do Enviador (`%LOCALAPPDATA%\EnviadorEmails\token_cache.bin`), o antigo é copiado,
  para ninguém precisar entrar de novo. Uma variável de ambiente (`TCM_CONTA_MICROSOFT`) troca a
  pasta, para os testes e a verificação do `.exe`.
- `LoginWorker`: login no navegador numa thread daemon, com sinais `concluido` e `falhou` (o do
  Enviador).
- `abrir_smtp(email_login, token)`: STARTTLS e XOAUTH2 em `smtp.office365.com:587` (o do Enviador).
- `CartaoContaMicrosoft`: o bloco "Conta de envio" do diálogo do Enviador (e-mail logado, "Entrar
  com a Microsoft", "Sair da conta", aviso e login abandonado ao fechar). Os dois diálogos passam a
  usá-lo. Os campos Para/Cco do Enviador continuam no Enviador.
- `pip install tcm-ui[microsoft]` instala `msal` e `msal-extensions`.

### `pdf-xml-mailer` 2.1.0

- `conta.py`, `LoginWorker`, `abrir_smtp` e os IDs saem do pacote e passam a vir de `tcm_ui.microsoft`.
  O comportamento visível não muda.
- A dependência passa a `tcm-ui[microsoft]>=1.6.0`.

### `Send_Agregados` 2.1.0

- Novo método `metodo = microsoft`, padrão no `config.ini` embutido. `outlook` continua como está.
  O método `smtp` com senha deixa de existir: um `config.ini` antigo com `metodo = smtp` é tratado
  como `microsoft`.
- O botão "Credenciais..." vira **"Conta de envio..."**. O diálogo tem o `CartaoContaMicrosoft` e o
  campo **Enviar como** (opcional; vazio envia como a própria conta). O CCO continua no campo da tela
  principal, que já é salvo por método (`cco_<metodo>`). Enviar como e CCO ficam nas preferências da
  pessoa (`salvar_prefs`), não no `config.ini`, que é trocado nas atualizações.
- Na primeira abertura, quem ainda não entrou vê o diálogo, como hoje acontece com as credenciais.
- Envio: um token por lote (o `acquire_token_silent` renova sozinho). Login como a conta da pessoa;
  `From` e envelope com o remetente "Enviar como" (ou a própria conta). Uma reconexão no meio do
  lote pega um token novo.
- Erros: `SendAsDenied` vira `ErroFatal` com "Sua conta não tem permissão para enviar como
  '<endereço>'. Peça à TI a permissão 'Enviar como' nessa caixa." Uma sessão expirada para o lote e
  pede para entrar de novo.
- Migração: se existir o `.env`, o `EMAIL_CCO` vai para as preferências (quando ainda não houver
  CCO salvo lá) e o `.env` é apagado. O `SMTP_USUARIO` vira a sugestão inicial do campo "Enviar como"
  (era a conta compartilhada). Assim acaba também a senha no `os.environ` do processo da casca.
- `build.ps1` ganha `--hidden-import msal --hidden-import msal_extensions`, e a verificação do `.exe`
  usa proxy morto, como na casca.

### Casca `Sistema-Financeiro` 1.5.0

- Pins: `tcm-ui@v1.6.0`, `robo-agregado@v2.1.0`, `enviador-pdf-xml@v2.1.0`. As versões continuam em
  `versoes.txt`, sem bibliotecas novas.
- A verificação do `.exe` ganha `TCM_CONTA_MICROSOFT` temporário. Os dois módulos dividem o mesmo
  arquivo de cache no mesmo processo (o `msal-extensions` trava o arquivo).

### Ordem de lançamento

`Tcm-ui` v1.6.0 → `pdf-xml-mailer` v2.1.0 → `Send_Agregados` v2.1.0 → `Sistema-Financeiro` v1.5.0.
Antes da tag do `Send_Agregados`, o Erik testa um envio real como a caixa do financeiro, depois que a
TI der o "Enviar como".

## Decisões minhas (para o Erik conferir)

- Os IDs do aplicativo vão para o `Tcm-ui` (um lugar só), e não ficam repetidos em cada sistema.
- O endereço da caixa compartilhada **não** vem preenchido no `config.ini` (repositório público): a
  sugestão vem do `.env` antigo e, para quem não tiver, a pessoa digita uma vez.
- O método `smtp` com senha é removido, e não mantido como opção.
- O `CartaoContaMicrosoft` vai para o `Tcm-ui`, para os dois diálogos ficarem iguais.

## Fica com quem implementar

Nomes internos, textos de ajuda dos campos, organização dos testes (TDD em cada repositório) e como
dividir os commits locais (não há commits até o "Salvar versão").
