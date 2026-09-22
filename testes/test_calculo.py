"""testes/test_calculo.py

Casos de teste de servicos/calculo.py (Gustavo, secao 3.2).
Modulo dono: Arthur Linhares (Desenvolvedor 5 - secao 3.5 + Qualidade e
documentacao).

Rodar com:
    pytest testes/test_calculo.py -v
    (ou so `pytest -v` na raiz do projeto, pra rodar a suite inteira)

Regra que estes testes conferem com mais cuidado (README secao 11): o
almoco descontado tem um PISO de 1h - mesmo se a pessoa marcou um almoco
mais curto por completo (saida_almoco e retorno_almoco preenchidos), ainda
assim descontamos 1h. Essa regra pegou um teste meu de primeira - ver
"CASO QUE FALHOU E FOI CORRIGIDO" abaixo.
"""

from datetime import time
from types import SimpleNamespace

import pytest

from servicos.calculo import (
    calcular_horas_trabalhadas,
    validar_ordem_dos_horarios,
    verificar_pendencia_almoco,
)


def horario(hora: int, minuto: int = 0) -> time:
    """Atalho pra nao escrever time(hora, minuto) toda hora."""
    return time(hora, minuto)


# --- calcular_horas_trabalhadas ------------------------------------------------


def test_dia_normal_com_almoco_de_1h_exata():
    """8h as 17h com 1h de almoço (12h-13h) = 8h trabalhadas."""
    resultado = calcular_horas_trabalhadas(
        horario(8), horario(17), horario(12), horario(13)
    )
    assert resultado == 8.0


def test_almoco_mais_longo_que_o_minimo_desconta_o_valor_real():
    """Almoço de 1h30 (mais que o mínimo) desconta o valor REAL, não 1h."""
    resultado = calcular_horas_trabalhadas(
        horario(8), horario(18), horario(12), horario(13, 30)
    )
    assert resultado == 8.5  # 10h de expediente - 1h30 de almoço


def test_almoco_marcado_mas_curto_ainda_desconta_o_minimo_de_1h():
    """CASO QUE FALHOU E FOI CORRIGIDO.

    Suposição inicial: se a pessoa marcou entrada E volta do almoço
    (saida_almoco=12:00, retorno_almoco=12:30 - 30 minutos reais, os
    dois campos preenchidos, nada pendente), o sistema descontaria os
    30 minutos reais. Escrevi o teste esperando 8.5h (9h de expediente
    - 0.5h de almoço) e ele FALHOU: o valor real devolvido é 8.0h.

    Motivo, olhando _desconto_do_almoco: o mínimo de 1h (README seção
    11) não é só um valor de reserva pra quando falta marcação - é um
    PISO que vale mesmo com o almoço marcado por inteiro
    (`max(intervalo_real, ALMOCO_MINIMO_HORAS)`). Corrigi a expectativa
    pra 8.0h, que é o comportamento correto e documentado no docstring
    de _desconto_do_almoco.
    """
    resultado = calcular_horas_trabalhadas(
        horario(8), horario(17), horario(12), horario(12, 30)
    )
    assert resultado == 8.0  # não 8.5 - o mínimo de 1h vale mesmo com almoço marcado


def test_sem_nenhuma_marcacao_de_almoco_ainda_desconta_o_minimo():
    """Sem saida_almoco nem retorno_almoco: desconta o mínimo (1h) mesmo
    assim - o dia só vira pendência depois, em verificar_pendencia_almoco.
    """
    resultado = calcular_horas_trabalhadas(horario(8), horario(17))
    assert resultado == 8.0


def test_so_uma_marcacao_de_almoco_tambem_desconta_o_minimo():
    """saida_almoco marcada mas falta o retorno: mesma regra do mínimo."""
    resultado = calcular_horas_trabalhadas(
        horario(8), horario(17), horario(12), None
    )
    assert resultado == 8.0


def test_dia_em_andamento_sem_saida_devolve_zero():
    """Sem horário de saída, o dia ainda está em andamento: 0.0, não erro."""
    assert calcular_horas_trabalhadas(horario(8), None) == 0.0


def test_expediente_curto_nunca_fica_negativo():
    """30 minutos de expediente é menos que o mínimo do almoço (1h): o
    resultado tem que ficar em 0.0, nunca virar número negativo.
    """
    resultado = calcular_horas_trabalhadas(horario(8), horario(8, 30))
    assert resultado == 0.0


def test_arredondamento_com_minutos_quebrados():
    """08:15 às 17:50 com 1h de almoço = 9h35 brutas menos 1h = 8h35,
    arredondado pra 2 casas (8.58), igual o resto do sistema usa."""
    resultado = calcular_horas_trabalhadas(
        horario(8, 15), horario(17, 50), horario(12), horario(13)
    )
    assert resultado == 8.58


# --- validar_ordem_dos_horarios ------------------------------------------------


def test_horarios_em_ordem_correta_nao_da_erro():
    assert (
        validar_ordem_dos_horarios(horario(8), horario(17), horario(12), horario(13))
        is None
    )


def test_dia_so_com_entrada_e_valido():
    """Um dia em andamento (só entrada marcada) não é um erro de ordem."""
    assert validar_ordem_dos_horarios(horario(8)) is None


def test_pendencia_de_almoco_e_valida_para_a_ordem_dos_horarios():
    """Faltar o retorno do almoço é uma pendência (tratada depois por
    verificar_pendencia_almoco e pela tela de solicitações) mas NÃO é um
    erro de ordem dos horários.
    """
    assert (
        validar_ordem_dos_horarios(horario(8), horario(17), horario(12), None)
        is None
    )


@pytest.mark.parametrize(
    "entrada, saida, saida_almoco, retorno_almoco, mensagem_esperada",
    [
        (horario(8), horario(7), None, None,
         "a saida precisa ser depois da entrada"),
        (horario(8), horario(8), None, None,
         "a saida precisa ser depois da entrada"),
        (horario(8), horario(17), horario(7), None,
         "a saida para o almoco precisa ser depois da entrada"),
        (horario(8), horario(17), horario(17, 30), None,
         "a saida para o almoco precisa ser antes da saida do expediente"),
        (horario(8), horario(17), horario(12), horario(11, 30),
         "o retorno do almoco precisa ser depois da saida para o almoco"),
        (horario(8), horario(17), horario(12), horario(17, 30),
         "o retorno do almoco precisa ser antes da saida do expediente"),
    ],
)
def test_cada_regra_de_ordem_devolve_a_mensagem_certa(
    entrada, saida, saida_almoco, retorno_almoco, mensagem_esperada
):
    resultado = validar_ordem_dos_horarios(entrada, saida, saida_almoco, retorno_almoco)
    assert resultado == mensagem_esperada


# --- verificar_pendencia_almoco -------------------------------------------------


def _registro(saida=None, saida_almoco=None, retorno_almoco=None):
    """Objeto simples com os 3 atributos que a função lê via getattr - não
    precisa de um RegistroPonto de verdade nem de banco pra este teste.
    """
    return SimpleNamespace(
        saida=saida, saida_almoco=saida_almoco, retorno_almoco=retorno_almoco
    )


def test_dia_em_andamento_nao_e_pendencia():
    registro = _registro(saida=None)
    assert verificar_pendencia_almoco(registro) is False


def test_dia_completo_sem_pendencia():
    registro = _registro(
        saida=horario(17), saida_almoco=horario(12), retorno_almoco=horario(13)
    )
    assert verificar_pendencia_almoco(registro) is False


@pytest.mark.parametrize(
    "saida_almoco, retorno_almoco",
    [
        (None, horario(13)),  # faltou marcar a saída pro almoço
        (horario(12), None),  # faltou marcar a volta do almoço
        (None, None),  # faltaram os dois
    ],
)
def test_dia_completo_com_almoco_incompleto_e_pendencia(saida_almoco, retorno_almoco):
    registro = _registro(
        saida=horario(17), saida_almoco=saida_almoco, retorno_almoco=retorno_almoco
    )
    assert verificar_pendencia_almoco(registro) is True
