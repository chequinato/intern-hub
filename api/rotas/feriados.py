"""Rotas de /feriados - o calendario de dias nao uteis.

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Segue o molde da fundacao (api/rotas/estagiarios.py): caminho sem barra no
fim, status code explicito e commit dentro de try com rollback no except.

Entrega 3 (login, Miguel): qualquer pessoa logada ve o calendario; so
gestor cadastra ou remove feriado (um feriado muda as faltas de todo mundo).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import exigir_gestor, usuario_logado
from api.schemas import FeriadoCreate, FeriadoResponse
from banco.conexao import get_session
from modelos import Feriado, Usuario

router = APIRouter(prefix="/feriados", tags=["Feriados"])


@router.post(
    "",
    response_model=FeriadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um dia nao util",
)
def cadastrar_feriado(
    dados: FeriadoCreate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Feriado:
    """Cadastra o feriado, recusando data repetida com 409 em vez de erro 500.

    A coluna data tem unique=True no modelo: sem esta checagem, cadastrar o
    mesmo dia duas vezes estouraria direto no banco.
    """
    exigir_gestor(usuario)
    ja_existe = session.query(Feriado).filter_by(data=dados.data).first()
    if ja_existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"O dia {dados.data.isoformat()} ja esta cadastrado como "
                f"{ja_existe.descricao}."
            ),
        )

    feriado = Feriado(data=dados.data, descricao=dados.descricao)
    session.add(feriado)
    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o feriado.",
        ) from erro

    session.refresh(feriado)
    return feriado


@router.get(
    "",
    response_model=list[FeriadoResponse],
    summary="Lista os dias nao uteis cadastrados",
)
def listar_feriados(
    _usuario: Usuario = Depends(usuario_logado), session: Session = Depends(get_session)
) -> list[Feriado]:
    """Ordem cronologica - e assim que a tela e o relatorio esperam a lista."""
    return session.query(Feriado).order_by(Feriado.data).all()


@router.delete(
    "/{feriado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um dia nao util",
)
def remover_feriado(
    feriado_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> None:
    """Acrescentada na Entrega 3 (Miguel), para a tela de feriados do gestor.

    Remover um feriado faz aquele dia voltar a contar como dia util - o
    relatorio passa a cobrar ponto nele na proxima consulta.
    """
    exigir_gestor(usuario)
    feriado = session.query(Feriado).filter_by(id=feriado_id).first()
    if feriado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feriado {feriado_id} nao encontrado.",
        )
    session.delete(feriado)
    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel remover o feriado.",
        ) from erro
