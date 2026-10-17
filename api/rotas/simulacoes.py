"""Rota de /simulacoes - o "e se eu faltar / chegar atrasado".

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Esta rota so LE o banco: ela projeta um cenario em cima do saldo atual e
devolve o resultado, sem gravar nada (README, funcionalidade 8).

Entrega 3 (login, Miguel): toda rota daqui exige login. As regras de quem
pode o que estao em api/permissoes.py.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.permissoes import exigir_ver_estagiario, usuario_logado
from api.schemas import SimulacaoRequest, SimulacaoResponse
from banco.conexao import get_session
from modelos import Usuario
from servicos.simulador import simular_cenario

router = APIRouter(prefix="/simulacoes", tags=["Simulacao"])


@router.post(
    "",
    response_model=SimulacaoResponse,
    summary="Projeta o saldo em um cenario hipotetico",
)
def simular(
    dados: SimulacaoRequest,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> dict:
    """Calcula a projecao para o estagiario informado, sem alterar o banco."""
    exigir_ver_estagiario(dados.estagiario_id, usuario, session)

    return simular_cenario(
        dados.estagiario_id, dados.dias_falta, dados.horas_atraso, session
    )
