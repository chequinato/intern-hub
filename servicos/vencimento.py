"""Vencimento do banco de horas - saldo positivo que esta perto de expirar.

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Regra do README (secao 11): uma hora positiva vence se nao for compensada
dentro do prazo (padrao: 2 meses). O prazo e lido da Configuracao do proprio
estagiario, e nao fixo no codigo, porque o grupo pode ajusta-lo depois.

A conta e feita so em cima dos dias ANTERIORES a data limite: se aqueles dias
sozinhos ja deixavam a pessoa com credito, esse credito e o que esta prestes
a vencer. Se eles somam zero ou negativo, nao ha credito antigo nenhum - e
por isso a funcao devolve None em vez de avisar.
"""

from datetime import date

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from modelos.configuracao import (
    META_HORAS_DIARIA_PADRAO,
    PRAZO_VENCIMENTO_MESES_PADRAO,
    Configuracao,
)
from modelos.registro_ponto import RegistroPonto
from servicos.calculo import calcular_horas_trabalhadas


def verificar_vencimento(estagiario_id: int, session: Session) -> str | None:
    """Devolve o aviso de vencimento, ou None quando nao ha nada a avisar."""
    configuracao = (
        session.query(Configuracao).filter_by(estagiario_id=estagiario_id).first()
    )
    if configuracao is not None:
        prazo_meses = configuracao.prazo_vencimento_meses
        meta_diaria = configuracao.meta_horas_diaria
    else:
        prazo_meses = PRAZO_VENCIMENTO_MESES_PADRAO
        meta_diaria = META_HORAS_DIARIA_PADRAO

    data_limite = date.today() - relativedelta(months=prazo_meses)

    registros_antigos = (
        session.query(RegistroPonto)
        .filter(
            RegistroPonto.estagiario_id == estagiario_id,
            RegistroPonto.data <= data_limite,
            # So dias fechados entram na conta, igual ao calculo do saldo.
            RegistroPonto.saida.is_not(None),
        )
        .all()
    )
    if not registros_antigos:
        return None

    saldo_antigo = 0.0
    for registro in registros_antigos:
        horas = calcular_horas_trabalhadas(
            registro.entrada,
            registro.saida,
            registro.saida_almoco,
            registro.retorno_almoco,
        )
        saldo_antigo += horas - meta_diaria

    if saldo_antigo <= 0:
        return None

    return (
        f"Atencao: {saldo_antigo:.2f}h de credito foram geradas ha mais de "
        f"{prazo_meses} meses e podem expirar se nao forem compensadas."
    )
