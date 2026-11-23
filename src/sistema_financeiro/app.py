"""Casca do Sistema Financeiro: monta a janela com os módulos permitidos ao usuário."""
from __future__ import annotations

import logging
import os
import sys
import tempfile
from collections.abc import Iterable, Sequence
from importlib.metadata import entry_points
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from tcm_ui.atualizacao_ui import VerificadorAtualizacao
from tcm_ui.components import CartaoErro
from tcm_ui.janela import JanelaPrincipal
from tcm_ui.modulo import Modulo
from tcm_ui.registro import configurar_log
from tcm_ui.themes import tema

from . import __version__
from .acesso import GRUPO_ADMIN, grupos_do_usuario, permitidos, usuario_windows
from .descoberta import GRUPO_ENTRY_POINT, carregar_modulos

NOME_APP = "Sistema Financeiro"
ICONE = "painel"
REPOSITORIO = "ErikDeFreitas/Sistema-Financeiro"
NOME_EXE = "SistemaFinanceiro.exe"

log = logging.getLogger("sistema_financeiro")


def pasta_dados() -> Path:
    base = os.environ.get("SISTEMA_FINANCEIRO_DADOS")
    if base:
        return Path(base)
    return Path(os.environ["LOCALAPPDATA"]) / "TCM" / "SistemaFinanceiro"


def criar_janela(modulos: Sequence[Modulo], grupos: Iterable[str], usuario: str,
                 configuracoes: QSettings) -> JanelaPrincipal:
    return JanelaPrincipal(
        permitidos(modulos, grupos),
        nome_app=NOME_APP,
        icone_app=ICONE,
        usuario=usuario,
        modo="casca",
        configuracoes=configuracoes,
        rodape=[usuario, f"Versão {__version__}"],
        sem_modulos=("Você não tem acesso a nenhum sistema.",
                     f"Fale com a TI e informe o seu usuário: {usuario}"),
    )


def verificar_modulos() -> int:
    """0 se todo módulo instalado abre todas as suas páginas sem erro; 1 caso contrário."""
    _app = QApplication.instance() or QApplication(sys.argv[:1])  # noqa: F841
    try:
        tema.aplicar(_app)
    except Exception:
        log.exception("Verificação: falha ao aplicar o tema (styles.qss)")
        return 1
    pontos = list(entry_points(group=GRUPO_ENTRY_POINT))
    modulos = carregar_modulos(pontos)
    if len(modulos) < len(pontos):
        log.error("Verificação: %d ponto(s) de entrada não viraram módulo (instalados: %s; carregados: %s)",
                  len(pontos) - len(modulos), ", ".join(p.name for p in pontos), ", ".join(m.id for m in modulos))
        return 1
    if not modulos:
        log.error("Verificação: nenhum módulo instalado")
        return 1
    with tempfile.TemporaryDirectory(prefix="sf_verificacao_") as pasta:
        configuracoes = QSettings(str(Path(pasta) / "verificacao.ini"), QSettings.IniFormat)
        janela = criar_janela(modulos, {GRUPO_ADMIN}, "verificacao", configuracoes)
        falha = None
        for modulo in modulos:
            for pagina in modulo.paginas:
                janela.abrir(modulo.id, pagina.chave)
                if falha is None and janela.findChildren(CartaoErro):
                    falha = f"{modulo.id}:{pagina.chave}"  # CartaoErro só cresce: a primeira vez é a culpada
        janela.deleteLater()
        del janela
        configuracoes.sync()
    if falha:
        log.error("Verificação falhou em: %s", falha)
        return 1
    log.info("Verificação ok: %s", ", ".join(m.id for m in modulos))
    return 0


def rodar(argv: list[str] | None = None) -> int:
    configurar_log(pasta_dados(), "sistema_financeiro")
    if "--verificar" in (argv if argv is not None else sys.argv):
        return verificar_modulos()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setOrganizationName("TCM")
    app.setApplicationName("SistemaFinanceiro")
    tema.configurar("TCM", "SistemaFinanceiro")
    tema.aplicar(app)
    usuario, grupos, modulos = usuario_windows(), grupos_do_usuario(), carregar_modulos()
    log.info("Usuário %s com %d grupos (SF-*: %s); módulos permitidos: %s", usuario, len(grupos),
             sorted(g for g in grupos if g.rsplit("\\", 1)[-1].casefold().startswith("sf-")),
             [m.id for m in permitidos(modulos, grupos)])
    janela = criar_janela(modulos, grupos, usuario, QSettings("TCM", "SistemaFinanceiro"))
    VerificadorAtualizacao(janela, REPOSITORIO, NOME_EXE, __version__).iniciar()
    janela.show()
    return app.exec()
