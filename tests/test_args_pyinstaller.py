import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "ferramentas" / "args_pyinstaller.py"


def _linhas():
    saida = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, check=True
    ).stdout
    return saida.splitlines()


def _tem_par(linhas, opcao, valor):
    return any(a == opcao and b == valor for a, b in zip(linhas, linhas[1:]))


def test_inclui_dados_do_tcm_ui():
    assert _tem_par(_linhas(), "--collect-data", "tcm_ui")


def test_inclui_pacote_e_metadados_do_robo_agregado():
    linhas = _linhas()
    assert _tem_par(linhas, "--collect-all", "robo_agregado")
    assert _tem_par(linhas, "--copy-metadata", "robo-agregado")
