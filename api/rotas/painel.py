"""Rotas de /painel - o resumo que abre cada area da interface.

Modulo dono: Miguel (Entrega 3).

Duas rotas, uma por perfil. As duas so leem o banco: toda a conta mora
em servicos/painel.py, que por sua vez reaproveita saldo, calculo,
vencimento e solicitacao.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.schemas import PainelEstagiarioResponse, PainelGestorResponse
from banco.conexao import get_session
from modelos import Estagiario, Gestor
from servicos.painel import resumo_equipe, resumo_estagiario

router = APIRouter(prefix="/painel", tags=["Painel"])


def _hoje() -> date:
    """Data do servidor. Fica numa funcao para os testes poderem fixar o dia."""
    return date.today()


@router.get(
    "/estagiario/{estagiario_id}",
    response_model=PainelEstagiarioResponse,
    summary="Resumo do estagiario: saldo, semana, pendencias e tendencia",
)
def painel_do_estagiario(
    estagiario_id: int, session: Session = Depends(get_session)
) -> dict:
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {estagiario_id} nao encontrado.",
        )
    return resumo_estagiario(estagiario, _hoje(), session)


@router.get(
    "/gestor/{gestor_id}",
    response_model=PainelGestorResponse,
    summary="Visao da equipe: saldo, alertas e pedidos de cada estagiario",
)
def painel_do_gestor(gestor_id: int, session: Session = Depends(get_session)) -> dict:
    gestor = session.query(Gestor).filter_by(id=gestor_id).first()
    if gestor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gestor {gestor_id} nao encontrado.",
        )
    return resumo_equipe(gestor_id, _hoje(), session)
