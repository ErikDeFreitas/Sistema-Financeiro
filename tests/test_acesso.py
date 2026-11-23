import sys
import types

import pytest

from sistema_financeiro.acesso import (
    GRUPO_ADMIN,
    grupos_do_token,
    grupos_do_usuario,
    permitidos,
    usuario_windows,
)


def test_grupo_admin():
    assert GRUPO_ADMIN == "SF-Admin"


def test_dev_substitui_token_quando_nao_congelado():
    g = grupos_do_usuario(
        congelado=False,
        ambiente={"SF_GRUPOS_DEV": " SF-Mesclador ; SF-Catraca;"},
        leitor=lambda: pytest.fail("não deve ler o token"),
    )
    assert g == {"SF-Mesclador", "SF-Catraca"}


def test_dev_ignorado_quando_congelado():
    g = grupos_do_usuario(congelado=True, ambiente={"SF_GRUPOS_DEV": "SF-Admin"}, leitor=lambda: {"Users"})
    assert g == {"Users"}


def test_falha_na_leitura_do_token_vira_conjunto_vazio(caplog):
    def quebra():
        raise OSError("sem token")

    assert grupos_do_usuario(congelado=True, ambiente={}, leitor=quebra) == set()
    assert "sem token" in caplog.text


def test_permitidos_por_grupo_sem_caixa_e_sem_dominio(modulos_abc):
    assert [m.id for m in permitidos(modulos_abc, {"TCMSP\\sf-b", "sf-c"})] == ["b", "c"]


def test_admin_ve_todos_na_ordem(modulos_abc):
    assert [m.id for m in permitidos(modulos_abc, {"sf-admin"})] == ["a", "b", "c"]


def test_sem_grupo_nenhum_modulo(modulos_abc):
    assert permitidos(modulos_abc, {"Users"}) == []


class _ErroWin(Exception):
    pass


def _falsificar_win32(monkeypatch, grupos, nomes, deny_only=0x10):
    """grupos: lista de (sid, atributos); nomes: sid -> (nome, dominio, tipo) ou None (não resolve)."""
    seguranca = types.ModuleType("win32security")
    seguranca.TOKEN_QUERY = 8
    seguranca.TokenGroups = 2
    seguranca.SE_GROUP_USE_FOR_DENY_ONLY = deny_only
    seguranca.OpenProcessToken = lambda processo, acesso: "token"
    seguranca.GetTokenInformation = lambda token, classe: grupos

    def procurar(sistema, sid):
        if nomes[sid] is None:
            raise _ErroWin("não resolve")
        return nomes[sid]

    seguranca.LookupAccountSid = procurar
    api = types.ModuleType("win32api")
    api.GetCurrentProcess = lambda: "processo"
    tipos = types.ModuleType("pywintypes")
    tipos.error = _ErroWin
    for nome, mod in (("win32security", seguranca), ("win32api", api), ("pywintypes", tipos)):
        monkeypatch.setitem(sys.modules, nome, mod)


def test_sid_que_nao_resolve_e_ignorado(monkeypatch):
    _falsificar_win32(
        monkeypatch,
        [("s1", 4), ("s2", 4), ("s3", 4)],
        {"s1": ("SF-A", "TCMSP", 2), "s2": None, "s3": ("Users", "BUILTIN", 4)},
    )
    assert grupos_do_token() == {"SF-A", "Users"}


def test_grupo_so_para_negacao_e_ignorado(monkeypatch):
    _falsificar_win32(
        monkeypatch,
        [("s1", 4), ("s2", 4 | 0x10)],
        {"s1": ("SF-A", "TCMSP", 2), "s2": ("SF-B", "TCMSP", 2)},
    )
    assert grupos_do_token() == {"SF-A"}


@pytest.mark.skipif(sys.platform != "win32", reason="token só no Windows")
def test_token_real_devolve_nomes():
    g = grupos_do_token()
    assert g and all(isinstance(n, str) and "\\" not in n for n in g)


def test_usuario_windows_com_dominio():
    assert usuario_windows({"USERDOMAIN": "TCMSP", "USERNAME": "fulano"}) == "TCMSP\\fulano"


def test_usuario_windows_sem_dominio(monkeypatch):
    monkeypatch.setattr("getpass.getuser", lambda: "fulano")
    assert usuario_windows({}) == "fulano"


def test_sid_sem_nome_gera_aviso_com_contagem(monkeypatch, caplog):
    _falsificar_win32(
        monkeypatch,
        [("s1", 4), ("s2", 4), ("s3", 4)],
        {"s1": ("SF-A", "TCMSP", 2), "s2": None, "s3": None},
    )
    with caplog.at_level("WARNING", logger="sistema_financeiro"):
        assert grupos_do_token() == {"SF-A"}
    assert "2 grupo(s) do token sem nome (fora da rede?)" in caplog.text


def test_sem_sid_irresolvel_nao_gera_aviso(monkeypatch, caplog):
    _falsificar_win32(monkeypatch, [("s1", 4)], {"s1": ("SF-A", "TCMSP", 2)})
    with caplog.at_level("WARNING", logger="sistema_financeiro"):
        grupos_do_token()
    assert "sem nome" not in caplog.text
