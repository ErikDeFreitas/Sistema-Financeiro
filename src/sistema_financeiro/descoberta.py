"""Descoberta dos módulos instalados, via entry points do grupo `sistema_financeiro.modulos`."""
from __future__ import annotations

import logging
from collections.abc import Iterable
from importlib.metadata import EntryPoint, entry_points

from tcm_ui.modulo import Modulo

GRUPO_ENTRY_POINT = "sistema_financeiro.modulos"
ORDEM = ("robo_agregado", "mesclador", "enviador_pdf_xml", "renomeador_cte", "sistema_catraca")

log = logging.getLogger("sistema_financeiro")


def carregar_modulos(pontos: Iterable[EntryPoint] | None = None) -> list[Modulo]:
    """Carrega os módulos; um que falha é registrado no log e não derruba os demais."""
    if pontos is None:
        pontos = entry_points(group=GRUPO_ENTRY_POINT)
    achados: dict[str, Modulo] = {}
    for ponto in pontos:
        try:
            modulo = ponto.load()
        except Exception:
            log.exception("Não foi possível carregar o módulo %s", ponto.name)
            continue
        if not isinstance(modulo, Modulo):
            log.error("O ponto de entrada %s não é um Modulo (%s)", ponto.name, type(modulo).__name__)
            continue
        if modulo.id in achados:
            log.error("Módulo %s repetido (ponto de entrada %s); fica o primeiro", modulo.id, ponto.name)
            continue
        achados[modulo.id] = modulo

    def chave(modulo: Modulo) -> tuple[int, str]:
        indice = ORDEM.index(modulo.id) if modulo.id in ORDEM else len(ORDEM)
        return indice, modulo.id

    return sorted(achados.values(), key=chave)
