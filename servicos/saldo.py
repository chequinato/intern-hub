"""Calculo do saldo (banco de horas) de um estagiario.

Modulo dono: Gustavo Legieri (Desenvolvedor 2 - secao 3.2).

Enquanto calculo.py resolve UM dia isolado (em Python puro), este modulo
resolve o ACUMULADO ao longo do tempo - e e aqui que o SQLAlchemy mostra
servico. Em vez de carregar todos os registros para a memoria e somar na mao
(o "ler arquivo por arquivo" que o README secao 0.1 cita como o trabalho que o
ORM nos poupa), pedimos ao banco a soma pronta com func.sum().

Recursos do SQLAlchemy usados aqui: func.sum, func.count, func.cast,
func.strftime, case, query().filter().
"""

from sqlalchemy import Integer, case, func
from sqlalchemy.orm import Session

from modelos import Configuracao, RegistroPonto
from modelos.configuracao import LIMITE_ALERTA_NEGATIVO_PADRAO
from servicos.calculo import ALMOCO_MINIMO_HORAS, calcular_horas_trabalhadas

ALMOCO_MINIMO_SEGUNDOS = int(ALMOCO_MINIMO_HORAS * 3600)


def calcular_saldo_dia(registro, meta_horas_diaria: float) -> float:
    """Saldo de um unico dia: horas trabalhadas menos a meta diaria.

    Positivo = credito (trabalhou mais que a meta); negativo = deve horas.
    Reaproveita calcular_horas_trabalhadas() para nao repetir a regra do
    almoco em dois lugares.
    """
    horas = calcular_horas_trabalhadas(
        registro.entrada,
        registro.saida,
        registro.saida_almoco,
        registro.retorno_almoco,
    )
    return round(horas - meta_horas_diaria, 2)


def _segundos_do_horario(coluna):
    """Expressao SQL: transforma uma coluna Time em segundos desde 00:00.

    O SQLite guarda Time como texto 'HH:MM:SS'. Com strftime extraimos hora,
    minuto e segundo e montamos os segundos do dia - assim da para somar
    horarios diretamente no banco, sem trazer nada para o Python.
    """
    return (
        func.cast(func.strftime("%H", coluna), Integer) * 3600
        + func.cast(func.strftime("%M", coluna), Integer) * 60
        + func.cast(func.strftime("%S", coluna), Integer)
    )


def calcular_saldo_acumulado(estagiario_id: int, session: Session) -> float:
    """Saldo total (banco de horas) do estagiario, somado no proprio banco.

    Conta apenas dias COMPLETOS (entrada, saida, saida e retorno do almoco
    preenchidos). Dias em andamento ou com pendencia de almoco ficam de fora
    ate serem resolvidos - por isso o filtro is_not(None) nos quatro horarios.

    Para cada dia: trabalhado = (saida - entrada) - max(almoco_real, 1h).
    O func.sum() soma esse trabalhado de todos os dias de uma vez; o
    func.count() diz quantos dias entraram na conta, para descontar a meta.

    saldo = horas_trabalhadas_totais - (meta_diaria * dias_completos)
    """
    meta_diaria = _meta_diaria(estagiario_id, session)

    bruto_segundos = _segundos_do_horario(RegistroPonto.saida) - _segundos_do_horario(
        RegistroPonto.entrada
    )
    almoco_real_segundos = _segundos_do_horario(
        RegistroPonto.retorno_almoco
    ) - _segundos_do_horario(RegistroPonto.saida_almoco)

    # Respeita o intervalo minimo de almoco (1h) tambem na consulta, para bater
    # exatamente com o que calculo.py faz em Python.
    almoco_efetivo = case(
        (almoco_real_segundos > ALMOCO_MINIMO_SEGUNDOS, almoco_real_segundos),
        else_=ALMOCO_MINIMO_SEGUNDOS,
    )
    trabalhado_segundos = bruto_segundos - almoco_efetivo

    total_segundos, dias_completos = (
        session.query(
            func.sum(trabalhado_segundos),
            func.count(RegistroPonto.id),
        )
        .filter(
            RegistroPonto.estagiario_id == estagiario_id,
            RegistroPonto.saida.is_not(None),
            RegistroPonto.saida_almoco.is_not(None),
            RegistroPonto.retorno_almoco.is_not(None),
        )
        .one()
    )

    if not dias_completos:
        return 0.0

    horas_trabalhadas = (total_segundos or 0) / 3600
    saldo = horas_trabalhadas - (meta_diaria * dias_completos)
    return round(saldo, 2)


def verificar_alerta(
    saldo_acumulado: float, limite: float = LIMITE_ALERTA_NEGATIVO_PADRAO
) -> bool:
    """Diz se o saldo negativo ja atingiu o limite de alerta.

    O limite padrao e -5h (README secao 11). Dispara quando o saldo esta em
    -5h ou pior (ex: -5.0, -6.3). Um saldo de -4.9 ainda nao alerta.
    """
    return saldo_acumulado <= limite


def _meta_diaria(estagiario_id: int, session: Session) -> float:
    """Le a meta de horas diaria do estagiario na tabela de configuracao."""
    configuracao = (
        session.query(Configuracao)
        .filter(Configuracao.estagiario_id == estagiario_id)
        .first()
    )
    if configuracao is None:
        # Estagiario e configuracao nascem juntos (fundacao do Pedro), entao
        # isso so acontece com dado inconsistente. Sem meta, o saldo nao faz
        # sentido: tratamos como meta 0 (todo dia trabalhado vira credito).
        return 0.0
    return configuracao.meta_horas_diaria
