import logging

from sistema_financeiro.descoberta import carregar_modulos


class _Ponto:
    def __init__(self, nome, valor=None, erro=None):
        self.name, self._valor, self._erro = nome, valor, erro

    def load(self):
        if self._erro:
            raise self._erro
        return self._valor


def test_ordem_fixa_e_desconhecidos_por_id_no_fim(criar_modulo_falso):
    pontos = [_Ponto(i, criar_modulo_falso(i)) for i in ("zeta", "mesclador", "alfa", "robo_agregado")]
    assert [m.id for m in carregar_modulos(pontos)] == ["robo_agregado", "mesclador", "alfa", "zeta"]


def test_modulo_que_nao_importa_nao_derruba_os_outros(criar_modulo_falso, caplog):
    pontos = [_Ponto("mesclador", erro=ImportError("pandas")), _Ponto("robo_agregado", criar_modulo_falso("robo_agregado"))]
    with caplog.at_level(logging.ERROR, logger="sistema_financeiro"):
        ids = [m.id for m in carregar_modulos(pontos)]
    assert ids == ["robo_agregado"] and "mesclador" in caplog.text


def test_objeto_que_nao_e_modulo_e_ignorado(caplog):
    with caplog.at_level(logging.ERROR, logger="sistema_financeiro"):
        assert carregar_modulos([_Ponto("mesclador", "texto")]) == []
    assert "mesclador" in caplog.text


def test_id_repetido_fica_o_primeiro(criar_modulo_falso, caplog):
    primeiro, segundo = criar_modulo_falso("a"), criar_modulo_falso("a")
    with caplog.at_level(logging.ERROR, logger="sistema_financeiro"):
        resultado = carregar_modulos([_Ponto("a1", primeiro), _Ponto("a2", segundo)])
    assert len(resultado) == 1 and resultado[0] is primeiro
    assert "a" in caplog.text


def test_robo_agregado_instalado_pelo_entry_point():
    assert "robo_agregado" in [m.id for m in carregar_modulos()]
