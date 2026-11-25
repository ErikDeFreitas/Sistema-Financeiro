import os
import tempfile
from pathlib import Path

# Antes de qualquer import do pacote: nenhum teste pode tocar as pastas reais em %LOCALAPPDATA%
# (robo_agregado.dados calcula a pasta na importação).
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["ROBO_AGREGADO_DADOS"] = tempfile.mkdtemp(prefix="robo_agregado_dados_")
os.environ["SISTEMA_FINANCEIRO_DADOS"] = tempfile.mkdtemp(prefix="sistema_financeiro_dados_")
os.environ["MESCLADOR_DADOS"] = tempfile.mkdtemp(prefix="mesclador_dados_")
os.environ["ENVIADOR_DADOS"] = tempfile.mkdtemp(prefix="enviador_dados_")
os.environ["RENOMEADOR_DADOS"] = tempfile.mkdtemp(prefix="renomeador_dados_")
os.environ["CATRACA_DADOS"] = tempfile.mkdtemp(prefix="catraca_dados_")
os.environ["TCM_CONTA_MICROSOFT"] = tempfile.mkdtemp(prefix="conta_microsoft_")

import pytest  # noqa: E402
from PySide6 import QtCore  # noqa: E402


class _QSettingsIni(QtCore.QSettings):
    """QSettings(org, app) em arquivo .ini (pasta temporária), nunca no registro do Windows.

    No Qt 6, QSettings(org, app) ignora setDefaultFormat() e usa sempre o registro; por isso a classe é
    trocada em PySide6.QtCore antes de qualquer `from PySide6.QtCore import QSettings`.
    """

    def __init__(self, *args, **kwargs):
        if 1 <= len(args) <= 2 and not kwargs and all(isinstance(a, str) for a in args):
            super().__init__(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, *args)
        else:
            super().__init__(*args, **kwargs)


QtCore.QSettings = _QSettingsIni
from PySide6.QtCore import QSettings  # noqa: E402
from tcm_ui.modulo import Modulo, Pagina  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def _qsettings_fora_do_registro(tmp_path_factory):
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path_factory.mktemp("qsettings")))


@pytest.fixture(autouse=True)
def _sem_grupos_dev(monkeypatch):
    monkeypatch.delenv("SF_GRUPOS_DEV", raising=False)


@pytest.fixture(autouse=True)
def tentativas_de_rede(monkeypatch):
    """Nenhum teste da casca alcanca a rede: connect/connect_ex para fora do loopback levantam erro.

    Devolve a lista de enderecos externos tentados (para os testes conferirem que ficou vazia).
    """
    import ipaddress
    import socket

    tentativas = []
    connect, connect_ex = socket.socket.connect, socket.socket.connect_ex

    def externo(endereco):
        if not isinstance(endereco, tuple):  # AF_UNIX / pipes: nao e rede
            return False
        try:
            return not ipaddress.ip_address(endereco[0]).is_loopback
        except ValueError:  # nome de host: so "localhost" e permitido
            return endereco[0] != "localhost"

    def barrado(self, endereco):
        if externo(endereco):
            tentativas.append(endereco)
            raise OSError(f"rede bloqueada nos testes: {endereco}")
        return connect(self, endereco)

    def barrado_ex(self, endereco):
        if externo(endereco):
            tentativas.append(endereco)
            return 111  # ECONNREFUSED
        return connect_ex(self, endereco)

    monkeypatch.setattr(socket.socket, "connect", barrado)
    monkeypatch.setattr(socket.socket, "connect_ex", barrado_ex)
    return tentativas


@pytest.fixture(autouse=True)
def _conta_microsoft_sem_rede(monkeypatch):
    """A Conta Microsoft (Enviador e RoboAgregado) faz um GET sem login ao ser criada; sem rede as paginas
    abrem com aviso, sem nenhum dialogo modal."""
    from enviador_pdf_xml import instancia
    from robo_agregado import tela

    def sem_rede():
        raise OSError("sem rede nos testes")

    monkeypatch.setattr(instancia, "FABRICA_CONTA", sem_rede)
    monkeypatch.setattr(tela, "FABRICA_CONTA", sem_rede)


@pytest.fixture
def criar_modulo_falso(tmp_path):
    """Fábrica de Modulo falso: criar_modulo_falso("a", grupo_ad="SF-A", criar=...)."""

    def fabrica(id, *, grupo_ad=None, criar=None, chaves=("p",)):
        return Modulo(
            id=id,
            nome=f"Módulo {id}",
            icone="x",
            versao="1.0.0",
            grupo_ad=grupo_ad or f"SF-{id.upper()}",
            repositorio="Dono/Repo",
            nome_exe=f"{id}.exe",
            pasta_dados=Path(tmp_path) / id,
            paginas=tuple(Pagina(c, c.upper(), f"Página {c}", "x") for c in chaves),
            criar=criar or (lambda contexto: None),
        )

    return fabrica


@pytest.fixture
def modulos_abc(criar_modulo_falso):
    return [criar_modulo_falso(i) for i in ("a", "b", "c")]


@pytest.fixture
def configuracoes(tmp_path):
    return QSettings(str(tmp_path / "config.ini"), QSettings.IniFormat)
