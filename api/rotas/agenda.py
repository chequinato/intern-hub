"""Rotas de /agenda - compromissos do estagiario e a exportacao para calendario.

Modulo dono: Miguel (Entrega 3).

A regra que importa (dia de prova = meta pela metade) mora em
servicos/agenda.py; aqui ficam o cadastro, a lista e o arquivo .ics.

Rotas:
    GET    /agenda/{estagiario_id}       compromissos (filtro por periodo)
    POST   /agenda                       estagiario cadastra
    DELETE /agenda/{compromisso_id}      estagiario remove
    GET    /agenda/{estagiario_id}/ics   arquivo para o Google Agenda/Outlook
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import SEM_PERMISSAO, exigir_o_proprio_estagiario, exigir_ver_estagiario, usuario_logado
from api.schemas import CompromissoCreate, CompromissoResponse
from banco.conexao import get_session
from modelos import Compromisso, Usuario
from modelos.usuario import PERFIL_ESTAGIARIO
from servicos.agenda import gerar_ics, listar_compromissos

router = APIRouter(prefix="/agenda", tags=["Agenda"])


@router.get(
    "/{estagiario_id}",
    response_model=list[CompromissoResponse],
    summary="Compromissos do estagiario, em ordem de data",
)
def listar(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
    inicio: date | None = Query(default=None, description="A partir desta data (inclusive)."),
    fim: date | None = Query(default=None, description="Ate esta data (inclusive)."),
) -> list[Compromisso]:
    """O gestor tambem ve: e assim que ele sabe quando o estagiario tem prova."""
    exigir_ver_estagiario(estagiario_id, usuario, session)
    return listar_compromissos(estagiario_id, session, inicio, fim)


@router.post(
    "",
    response_model=CompromissoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um compromisso na agenda",
)
def cadastrar(
    dados: CompromissoCreate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Compromisso:
    """Quem cadastra e o proprio estagiario (o id vem do login)."""
    if usuario.perfil != PERFIL_ESTAGIARIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SEM_PERMISSAO)
    estagiario = exigir_o_proprio_estagiario(usuario.estagiario_id, usuario, session)

    compromisso = Compromisso(estagiario_id=estagiario.id, **dados.model_dump())
    session.add(compromisso)
    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o compromisso.",
        ) from erro
    session.refresh(compromisso)
    return compromisso


@router.delete(
    "/{compromisso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um compromisso",
)
def remover(
    compromisso_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Response:
    compromisso = session.query(Compromisso).filter_by(id=compromisso_id).first()
    if compromisso is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compromisso {compromisso_id} nao encontrado.",
        )
    exigir_o_proprio_estagiario(compromisso.estagiario_id, usuario, session)

    session.delete(compromisso)
    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel remover o compromisso.",
        ) from erro
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{estagiario_id}/ics",
    summary="Baixa a agenda em .ics (Google Agenda, Outlook, celular)",
)
def exportar_ics(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
    inicio: date | None = Query(default=None),
) -> Response:
    """Sem response_model: devolve o arquivo, como a exportacao do relatorio.

    Por padrao exporta de hoje em diante - quem importa no Google Agenda
    quer os proximos compromissos, nao o semestre que ja passou.
    """
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)
    compromissos = listar_compromissos(estagiario_id, session, inicio or date.today())
    conteudo = gerar_ics(compromissos, estagiario.nome)
    return Response(
        content=conteudo,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="agenda_{estagiario_id}.ics"'},
    )
