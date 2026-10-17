"""Rota de /saldo - o banco de horas acumulado.

Modulo dono: Gustavo Legieri (Desenvolvedor 2 - secao 3.2).

Fina camada HTTP sobre servicos/saldo.py: recebe o id, chama o servico (que
soma no banco via func.sum()) e devolve o saldo + se esta em alerta.

Entrega 3 (login, Miguel): toda rota daqui exige login. As regras de quem
pode o que estao em api/permissoes.py.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.permissoes import exigir_ver_estagiario, usuario_logado
from api.schemas import SaldoResponse
from banco.conexao import get_session
from modelos import Configuracao, Usuario
from modelos.configuracao import LIMITE_ALERTA_NEGATIVO_PADRAO
from servicos.saldo import calcular_saldo_acumulado, verificar_alerta

router = APIRouter(prefix="/saldo", tags=["Saldo"])


@router.get(
    "/{estagiario_id}",
    response_model=SaldoResponse,
    summary="Retorna o saldo acumulado de horas do estagiario",
)
def obter_saldo(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> SaldoResponse:
    """Saldo do banco de horas + estado do alerta (-5h, README secao 11)."""
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)

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
