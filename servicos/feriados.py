"""Dia util ou nao - a regra que o relatorio usa para contar faltas.

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Um dia so cobra ponto se for de segunda a sexta e nao estiver cadastrado
como feriado (modelos/feriado.py).

Recursos do SQLAlchemy usados aqui: query().filter().first().
"""

from datetime import date

from sqlalchemy.orm import Session

from modelos.feriado import Feriado


def eh_dia_util(data: date, session: Session) -> bool:
    """True se o dia cobra ponto; False para fim de semana ou feriado."""
    # weekday(): 0 = segunda ... 4 = sexta, 5 = sabado, 6 = domingo.
    if data.weekday() > 4:
        return False

    feriado = session.query(Feriado).filter(Feriado.data == data).first()
    return feriado is None
