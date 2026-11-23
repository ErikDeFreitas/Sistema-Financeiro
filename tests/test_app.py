from pathlib import Path

import pytest
from tcm_ui.components import CartaoErro, EstadoVazio, Texto

from sistema_financeiro import app
from sistema_financeiro.app import criar_janela, pasta_dados, verificar_modulos
from sistema_financeiro.descoberta import carregar_modulos


USUARIO = "TCMSP" + chr(92) + "fulano"
assert "\\" in USUARIO


def textos(widget):
    return [t.text() for t in widget.findChildren(Texto)]


def test_sem_acesso_mostra_usuario(qtbot, configuracoes, modulos_abc):
    jan = criar_janela(modulos_abc, {"Users"}, USUARIO, configuracoes)
    qtbot.addWidget(jan)
    vazio = jan.findChild(EstadoVazio)
    juntos = " | ".join(textos(vazio))
    assert "Você não tem acesso a nenhum sistema." in juntos and USUARIO in juntos


def test_rodape_tem_usuario_e_versao(qtbot, configuracoes, modulos_abc):
    jan = criar_janela(modulos_abc, {"SF-A"}, USUARIO, configuracoes)
    qtbot.addWidget(jan)
    todos = textos(jan)
    assert USUARIO in todos and "Versão 1.0.0" in todos


def test_ultima_pagina_de_sistema_perdido_abre_a_primeira_permitida(qtbot, configuracoes, modulos_abc):
    configuracoes.setValue("navegacao/ultima", "b:p")
    a, b, _ = modulos_abc
    jan = criar_janela([a, b], {"SF-A"}, "u", configuracoes)
    qtbot.addWidget(jan)
    assert jan.pagina_atual == ("a", "p")


def test_robo_agregado_abre_na_casca(qtbot, configuracoes):
    jan = criar_janela(carregar_modulos(), {"SF-RoboAgregado"}, "u", configuracoes)
    qtbot.addWidget(jan)
    assert jan.pagina_atual == ("robo_agregado", "extrato") and not jan.findChildren(CartaoErro)


def test_modulo_com_erro_vira_cartao_e_o_resto_funciona(qtbot, configuracoes, criar_modulo_falso):
    def quebra(contexto):
        raise RuntimeError("boom")

    ruim = criar_modulo_falso("ruim", criar=quebra)
    bom = criar_modulo_falso("bom", criar=lambda contexto: _Instancia())
    configuracoes.setValue("navegacao/ultima", "ruim:p")
    jan = criar_janela([ruim, bom], {"SF-Admin"}, "u", configuracoes)
    qtbot.addWidget(jan)
    assert len(jan.findChildren(CartaoErro)) == 1
    jan.abrir("bom", "p")
    assert jan.pagina_atual == ("bom", "p")


class _Instancia:
    def widget(self, chave):
        from PySide6.QtWidgets import QLabel
        return QLabel("ok")

    def acoes_cabecalho(self, chave):
        return []

    def pode_fechar(self):
        return True


def test_verificar_modulos_ok():
    assert verificar_modulos() == 0


def test_verificar_modulos_falha_se_algum_quebra(monkeypatch, criar_modulo_falso):
    def quebra(contexto):
        raise RuntimeError("boom")

    monkeypatch.setattr(app, "carregar_modulos", lambda pontos=None: [criar_modulo_falso("ruim", criar=quebra)])
    assert verificar_modulos() == 1


def test_verificar_modulos_falha_sem_modulos(monkeypatch):
    monkeypatch.setattr(app, "carregar_modulos", lambda pontos=None: [])
    assert verificar_modulos() == 1


def test_pasta_dados_respeita_variavel(monkeypatch, tmp_path):
    monkeypatch.setenv("SISTEMA_FINANCEIRO_DADOS", str(tmp_path))
    assert pasta_dados() == Path(tmp_path)


def test_pasta_dados_padrao(monkeypatch):
    monkeypatch.delenv("SISTEMA_FINANCEIRO_DADOS")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\X")
    assert pasta_dados() == Path(r"C:\X") / "TCM" / "SistemaFinanceiro"


def test_verificar_modulos_falha_se_ponto_de_entrada_nao_carrega(monkeypatch):
    class Quebrado:
        name = "quebrado"

        def load(self):
            raise ImportError("dependência ausente")

    monkeypatch.setattr(app, "entry_points", lambda group: [Quebrado()])
    assert verificar_modulos() == 1


def test_verificar_modulos_falha_se_tema_nao_aplica(monkeypatch, tmp_path):
    monkeypatch.setattr("tcm_ui.themes._ARQUIVO_QSS", tmp_path / "nao_existe.qss")
    assert verificar_modulos() == 1


def test_constantes_do_atualizador_batem_com_o_build():
    assert app.NOME_EXE == "SistemaFinanceiro.exe"
    assert app.REPOSITORIO == "ErikDeFreitas/Sistema-Financeiro"
    build = (Path(__file__).resolve().parent.parent / "build.ps1").read_text(encoding="utf-8")
    assert '$nome = "' + app.NOME_EXE.removesuffix(".exe") + '"' in build


def test_rodar_registra_grupos_sf(monkeypatch, caplog, qtbot):
    barra = chr(92)
    monkeypatch.setattr(app, "configurar_log", lambda *a, **k: None)
    monkeypatch.setattr(app, "grupos_do_usuario", lambda: {f"TCMSP{barra}sf-Mesclador", "Users", "SF-Admin"})
    monkeypatch.setattr(app, "carregar_modulos", lambda pontos=None: [])
    monkeypatch.setattr(app, "VerificadorAtualizacao", lambda *a, **k: type("V", (), {"iniciar": lambda s: None})())
    monkeypatch.setattr(app.JanelaPrincipal, "show", lambda self: None)
    monkeypatch.setattr(app.QApplication, "exec", lambda self: 0)
    with caplog.at_level("INFO", logger="sistema_financeiro"):
        assert app.rodar([]) == 0
    assert "sf-Mesclador" in caplog.text and "SF-Admin" in caplog.text
    assert "'Users'" not in caplog.text
