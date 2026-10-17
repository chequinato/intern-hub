"""Rota de /ponto - bater o ponto na hora, um clique por marcacao.

Modulo dono: Miguel (Entrega 3).

Fina, como as demais: chama servicos/ponto.py e traduz o erro de regra em
409. A resposta reaproveita _montar_resposta de api/rotas/registros.py,
para o registro voltar com as mesmas horas, pendencia e aviso de limite
legal que a rota de registro completo devolve.

Com o login, so o proprio estagiario bate o proprio ponto.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import exigir_o_proprio_estagiario, usuario_logado
from api.rotas.registros import _montar_resposta
from api.schemas import PontoRequest, PontoResponse
from banco.conexao import get_session
from modelos import Usuario
from servicos.ponto import ErroDePonto, bater_ponto, proxima_marcacao

router = APIRouter(prefix="/ponto", tags=["Ponto"])


def _agora() -> datetime:
    """Hora do servidor. Fica numa funcao para os testes poderem fixar a hora."""
    return datetime.now()


@router.post(
    "/{estagiario_id}",
    response_model=PontoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bate o ponto agora (entrada, almoco, retorno ou saida)",
)
def marcar_ponto(
    estagiario_id: int,
    dados: PontoRequest | None = None,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> PontoResponse:
    """Marca a hora atual no proximo horario vazio do dia de hoje."""
    exigir_o_proprio_estagiario(estagiario_id, usuario, session)
    marcacao = dados.marcacao if dados else None
    try:
        registro, campo = bater_ponto(estagiario_id, _agora(), session, marcacao)
    except LookupError as erro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(erro)) from erro
    except ErroDePonto as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro)) from erro
    except SQLAlchemyError as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o ponto.",
        ) from erro

    return PontoResponse(
        campo_marcado=campo,
        proxima_marcacao=proxima_marcacao(registro),
        registro=_montar_resposta(registro, session),
    )
