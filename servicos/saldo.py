"""Calculo do saldo (banco de horas) de um estagiario.

Modulo dono: Gustavo Legieri (Desenvolvedor 2 - secao 3.2).

Enquanto calculo.py resolve UM dia isolado (em Python puro), este modulo
resolve o ACUMULADO ao longo do tempo - e e aqui que o SQLAlchemy mostra
servico. Em vez de carregar todos os registros para a memoria e somar na mao
(o "ler arquivo por arquivo" que o README secao 0.1 cita como o trabalho que o
ORM nos poupa), pedimos ao banco a soma pronta com func.sum().

Recursos do SQLAlchemy usados aqui: func.sum, func.count, func.cast,
func.strftime, case, query().filter(), group_by() (tendencia mes a mes,
acrescentada na Entrega 3) e in_() com subconsulta (dia de prova, Entrega 3).

Dia de prova (Entrega 3, Miguel - servicos/agenda.py): pela Lei do Estagio,
a carga horaria cai pelo menos pela metade nos dias de avaliacao. Nesses
dias a meta conta pela metade. A conta continua inteira no banco: um
case() marca com 1 os dias cuja data esta na subconsulta das provas, e o
func.sum() desse 1 diz quantos dias completos foram de prova.
"""

from sqlalchemy import Integer, case, func
from sqlalchemy.orm import Session

from modelos import Configuracao, RegistroPonto
from modelos.configuracao import LIMITE_ALERTA_NEGATIVO_PADRAO
from servicos.agenda import FATOR_META_DIA_DE_PROVA, subconsulta_dias_de_prova
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


def _trabalhado_segundos():
    """Expressao SQL: segundos trabalhados em um dia, ja sem o almoco.

    trabalhado = (saida - entrada) - max(almoco_real, 1h). Fica numa funcao
    propria porque duas consultas usam exatamente a mesma conta: o saldo
    acumulado e a tendencia mes a mes (saldo_por_mes, logo abaixo).
    """
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
    return bruto_segundos - almoco_efetivo


def _dia_de_prova(estagiario_id: int):
    """Expressao SQL: 1 se o dia do registro e dia de prova, 0 se nao."""
    return case(
        (RegistroPonto.data.in_(subconsulta_dias_de_prova(estagiario_id)), 1),
        else_=0,
    )


def _meta_total(meta_diaria: float, dias: int, dias_de_prova: int) -> float:
    """Meta somada de N dias, com os dias de prova valendo a fracao da lei."""
    dias_normais = dias - dias_de_prova
    return meta_diaria * dias_normais + meta_diaria * FATOR_META_DIA_DE_PROVA * dias_de_prova


def _filtro_dias_completos(estagiario_id: int) -> tuple:
    """Condicoes do filter(): so dias do estagiario com os quatro horarios."""
    return (
        RegistroPonto.estagiario_id == estagiario_id,
        RegistroPonto.saida.is_not(None),
        RegistroPonto.saida_almoco.is_not(None),
        RegistroPonto.retorno_almoco.is_not(None),
    )


def calcular_saldo_acumulado(estagiario_id: int, session: Session) -> float:
    """Saldo total (banco de horas) do estagiario, somado no proprio banco.

    Conta apenas dias COMPLETOS (entrada, saida, saida e retorno do almoco
    preenchidos). Dias em andamento ou com pendencia de almoco ficam de fora
    ate serem resolvidos - por isso o filtro is_not(None) nos quatro horarios.

    Para cada dia: trabalhado = (saida - entrada) - max(almoco_real, 1h).
    O func.sum() soma esse trabalhado de todos os dias de uma vez; o
    func.count() diz quantos dias entraram na conta, para descontar a meta.

    saldo = horas_trabalhadas_totais - meta somada dos dias completos
    (a meta de um dia de prova conta pela metade)
    """
    meta_diaria = _meta_diaria(estagiario_id, session)

    total_segundos, dias_completos, dias_de_prova = (
        session.query(
            func.sum(_trabalhado_segundos()),
            func.count(RegistroPonto.id),
            func.sum(_dia_de_prova(estagiario_id)),
        )
        .filter(*_filtro_dias_completos(estagiario_id))
        .one()
    )

    if not dias_completos:
        return 0.0

    horas_trabalhadas = (total_segundos or 0) / 3600
    saldo = horas_trabalhadas - _meta_total(meta_diaria, dias_completos, dias_de_prova or 0)
    return round(saldo, 2)


def verificar_alerta(
    saldo_acumulado: float, limite: float = LIMITE_ALERTA_NEGATIVO_PADRAO
) -> bool:
    """Diz se o saldo negativo ja atingiu o limite de alerta.

    O limite padrao e -5h (README secao 11). Dispara quando o saldo esta em
    -5h ou pior (ex: -5.0, -6.3). Um saldo de -4.9 ainda nao alerta.
    """
    return saldo_acumulado <= limite


def saldo_por_mes(estagiario_id: int, session: Session) -> list[dict]:
    """Tendencia do banco de horas: horas e saldo de cada mes, em ordem.

    Funcionalidade 19 do refinamento ("tendencia do semestre"). Mesma conta
    do saldo acumulado, so que o banco agrupa por mes com group_by() em vez
    de somar tudo de uma vez: func.strftime("%Y-%m") transforma a data em
    "2026-09", e cada grupo devolve as horas e os dias completos daquele mes.

    O saldo_acumulado de cada linha soma os meses anteriores - e o que o
    grafico de tendencia desenha. O ultimo valor bate com
    calcular_saldo_acumulado().
    """
    meta_diaria = _meta_diaria(estagiario_id, session)
    mes = func.strftime("%Y-%m", RegistroPonto.data)

    linhas = (
        session.query(
            mes.label("mes"),
            func.sum(_trabalhado_segundos()),
            func.count(RegistroPonto.id),
            func.sum(_dia_de_prova(estagiario_id)),
        )
        .filter(*_filtro_dias_completos(estagiario_id))
        .group_by(mes)
        .order_by(mes)
        .all()
    )

    resultado = []
    acumulado = 0.0
    for mes_texto, segundos, dias, dias_de_prova in linhas:
        horas = (segundos or 0) / 3600
        saldo_mes = horas - _meta_total(meta_diaria, dias, dias_de_prova or 0)
        acumulado += saldo_mes
        ano, numero_mes = mes_texto.split("-")
        resultado.append({
            "ano": int(ano),
            "mes": int(numero_mes),
            "horas_trabalhadas": round(horas, 2),
            "dias_completos": dias,
            "saldo_mes": round(saldo_mes, 2),
            "saldo_acumulado": round(acumulado, 2),
        })
    return resultado


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
