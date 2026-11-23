"""Imprime, um por linha, os argumentos do PyInstaller para os sistemas instalados.

Cada entry point do grupo `sistema_financeiro.modulos` vira `--collect-all <pacote>` e
`--copy-metadata <distribuicao>`, para o .exe enxergar os modulos (o PyInstaller nao
segue entry points sozinho). Usa so a biblioteca padrao.
"""
from importlib.metadata import entry_points

GRUPO_ENTRY_POINT = "sistema_financeiro.modulos"


def argumentos() -> list[str]:
    args = ["--collect-data", "tcm_ui"]
    for ep in entry_points(group=GRUPO_ENTRY_POINT):
        pacote = ep.value.split(":")[0].split(".")[0]
        args += ["--collect-all", pacote, "--copy-metadata", ep.dist.name]
    return args


if __name__ == "__main__":
    print("\n".join(argumentos()))
