"""Simulacao de cenarios - o "e se eu faltar / chegar atrasado".

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Este servico so LE: ele parte do saldo real (calculado por servicos/saldo.py)
e projeta o efeito de faltas e atrasos em cima dele. Nada e gravado no banco,
que e exatamente o que a funcionalidade 8 do README pede.
"""

from sqlalchemy.orm import Session

from modelos.configuracao import META_HORAS_DIARIA_PADRAO, Configuracao
from servicos.saldo import calcular_saldo_acumulado


def simular_cenario(
    estagiario_id: int, dias_falta: int, horas_atraso: float, session: Session
) -> dict:
    """Projeta o saldo do estagiario depois de N faltas e X horas de atraso.

    Cada falta custa uma meta diaria inteira (o dia nao trabalhado continua
    sendo cobrado); cada hora de atraso custa uma hora. O saldo projetado e o
    saldo de hoje menos esse total.
    """
    # filter_by(estagiario_id=...) e essencial aqui: sem ele, a consulta
    # traria a configuracao do PRIMEIRO estagiario do banco e a simulacao de
    # todo mundo usaria a meta da mesma pessoa.
    configuracao = (
        session.query(Configuracao).filter_by(estagiario_id=estagiario_id).first()
    )
    meta_diaria = (
        configuracao.meta_horas_diaria
        if configuracao is not None
        else META_HORAS_DIARIA_PADRAO
    )

    saldo_atual = calcular_saldo_acumulado(estagiario_id, session)

    impacto_total = (dias_falta * meta_diaria) + horas_atraso
    saldo_projetado = saldo_atual - impacto_total

    return {
        "saldo_atual": round(saldo_atual, 2),
        "saldo_projetado": round(saldo_projetado, 2),
        # Negativo porque e o quanto o cenario TIRA do saldo.
        "impacto_horas": round(-impacto_total, 2),
    }
