"""Controle de acesso da casca: grupos do Windows (AD) do usuário e módulos permitidos."""
from __future__ import annotations

import getpass
import logging
import os
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence

from tcm_ui.modulo import Modulo

GRUPO_ADMIN = "SF-Admin"

log = logging.getLogger("sistema_financeiro")


def grupos_do_token() -> set[str]:
    """Nomes (sem domínio) dos grupos do token do processo atual. Só funciona no Windows."""
    import pywintypes
    import win32api
    import win32security

    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
    nomes: set[str] = set()
    sem_nome = 0
    for sid, atributos in win32security.GetTokenInformation(token, win32security.TokenGroups):
        if atributos & win32security.SE_GROUP_USE_FOR_DENY_ONLY:
            continue
        try:
            nomes.add(win32security.LookupAccountSid(None, sid)[0])
        except pywintypes.error:
            sem_nome += 1
    if sem_nome:
        log.warning("%d grupo(s) do token sem nome (fora da rede?)", sem_nome)
    return nomes


def grupos_do_usuario(
    *,
    congelado: bool | None = None,
    ambiente: Mapping[str, str] | None = None,
    leitor: Callable[[], set[str]] = grupos_do_token,
) -> set[str]:
    """Grupos do usuário. Fora do executável (não congelado), SF_GRUPOS_DEV substitui o token."""
    if congelado is None:
        congelado = getattr(sys, "frozen", False)
    if ambiente is None:
        ambiente = os.environ
    if not congelado and "SF_GRUPOS_DEV" in ambiente:
        return {g.strip() for g in ambiente["SF_GRUPOS_DEV"].split(";") if g.strip()}
    try:
        return leitor()
    except Exception:
        log.exception("Falha ao ler os grupos do token do Windows")
        return set()


def _normalizar(grupo: str) -> str:
    return grupo.rsplit("\\", 1)[-1].casefold()


def permitidos(modulos: Sequence[Modulo], grupos: Iterable[str]) -> list[Modulo]:
    """Módulos que o usuário pode ver, na ordem recebida. SF-Admin vê todos."""
    normalizados = {_normalizar(g) for g in grupos}
    if GRUPO_ADMIN.casefold() in normalizados:
        return list(modulos)
    return [m for m in modulos if m.grupo_ad.casefold() in normalizados]


def usuario_windows(ambiente: Mapping[str, str] | None = None) -> str:
    """'DOMINIO\\usuario'; sem domínio, só o login."""
    if ambiente is None:
        ambiente = os.environ
    dominio = ambiente.get("USERDOMAIN")
    usuario = ambiente.get("USERNAME") or getpass.getuser()
    return f"{dominio}\\{usuario}" if dominio else usuario
