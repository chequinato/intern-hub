"""Rotas de /painel - o resumo que abre cada area da interface.

Modulo dono: Miguel (Entrega 3).

Duas rotas, uma por perfil. As duas so leem o banco: toda a conta mora
em servicos/painel.py, que por sua vez reaproveita saldo, calculo,
vencimento e solicitacao.

Com o login: o painel do estagiario abre para ele e para o gestor dele; o
painel da equipe, so para o proprio gestor.
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.permissoes import exigir_o_proprio_gestor, exigir_ver_estagiario, usuario_logado
from api.schemas import PainelEstagiarioResponse, PainelGestorResponse
from banco.conexao import get_session
from modelos import Usuario
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
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> dict:
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)
    return resumo_estagiario(estagiario, _hoje(), session)


@router.get(
    "/gestor/{gestor_id}",
    response_model=PainelGestorResponse,
    summary="Visao da equipe: saldo, alertas e pedidos de cada estagiario",
)
def painel_do_gestor(
    gestor_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> dict:
    exigir_o_proprio_gestor(gestor_id, usuario)
    return resumo_equipe(gestor_id, _hoje(), session)
