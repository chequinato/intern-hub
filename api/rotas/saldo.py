"""Rota de /saldo - o banco de horas acumulado.

Modulo dono: Gustavo Legieri (Desenvolvedor 2 - secao 3.2).

Fina camada HTTP sobre servicos/saldo.py: recebe o id, chama o servico (que
soma no banco via func.sum()) e devolve o saldo + se esta em alerta.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.schemas import SaldoResponse
from banco.conexao import get_session
from modelos import Configuracao, Estagiario
from modelos.configuracao import LIMITE_ALERTA_NEGATIVO_PADRAO
from servicos.saldo import calcular_saldo_acumulado, verificar_alerta

router = APIRouter(prefix="/saldo", tags=["Saldo"])


@router.get(
    "/{estagiario_id}",
    response_model=SaldoResponse,
    summary="Retorna o saldo acumulado de horas do estagiario",
)
def obter_saldo(
    estagiario_id: int, session: Session = Depends(get_session)
) -> SaldoResponse:
    """Saldo do banco de horas + estado do alerta (-5h, README secao 11)."""
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {estagiario_id} nao encontrado.",
        )

    # O limite de alerta e por estagiario (fica na configuracao). Se por algum
    # motivo nao houver configuracao, caimos no padrao do projeto (-5h).
    configuracao = (
        session.query(Configuracao)
        .filter_by(estagiario_id=estagiario_id)
        .first()
    )
    limite = (
        configuracao.limite_alerta_negativo
        if configuracao is not None
        else LIMITE_ALERTA_NEGATIVO_PADRAO
    )

    saldo = calcular_saldo_acumulado(estagiario_id, session)
    dias = len(
        [
            registro
            for registro in estagiario.registros
            if registro.saida is not None
            and registro.saida_almoco is not None
            and registro.retorno_almoco is not None
        ]
    )

    return SaldoResponse(
        estagiario_id=estagiario_id,
        saldo_acumulado=saldo,
        em_alerta=verificar_alerta(saldo, limite),
        limite_alerta=limite,
        dias_registrados=dias,
    )
