"""Rota de /simulacoes - o "e se eu faltar / chegar atrasado".

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Esta rota so LE o banco: ela projeta um cenario em cima do saldo atual e
devolve o resultado, sem gravar nada (README, funcionalidade 8).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.schemas import SimulacaoRequest, SimulacaoResponse
from banco.conexao import get_session
from modelos import Estagiario
from servicos.simulador import simular_cenario

router = APIRouter(prefix="/simulacoes", tags=["Simulacao"])


@router.post(
    "",
    response_model=SimulacaoResponse,
    summary="Projeta o saldo em um cenario hipotetico",
)
def simular(
    dados: SimulacaoRequest, session: Session = Depends(get_session)
) -> dict:
    """Calcula a projecao para o estagiario informado, sem alterar o banco."""
    estagiario = session.query(Estagiario).filter_by(id=dados.estagiario_id).first()
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {dados.estagiario_id} nao encontrado.",
        )

    return simular_cenario(
        dados.estagiario_id, dados.dias_falta, dados.horas_atraso, session
    )
