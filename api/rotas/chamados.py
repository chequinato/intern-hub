"""Rotas de /chamados - o estagiario pede ajuda, o gestor acompanha.

Modulo dono: Miguel (Entrega 3).

Camada fina, no molde de api/rotas/solicitacoes.py: confere quem esta
logado (api/permissoes.py), chama servicos/chamados.py e traduz excecao em
status code:

    ChamadoNaoEncontrado -> 404
    ErroDeChamado        -> 409
    sem permissao        -> 403

Rotas:
    POST   /chamados                   estagiario abre
    GET    /chamados                   os meus (estagiario) / os da equipe (gestor)
    GET    /chamados/{id}              o chamado com a conversa inteira
    POST   /chamados/{id}/mensagens    estagiario ou gestor escreve
    PATCH  /chamados/{id}              gestor muda o andamento
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import SEM_PERMISSAO, exigir_gestor, exigir_o_proprio_estagiario, usuario_logado
from api.schemas import (
    ChamadoCreate,
    ChamadoDetalheResponse,
    ChamadoResponse,
    ChamadoStatusUpdate,
    MensagemCreate,
)
from banco.conexao import get_session
from modelos import Chamado, Usuario
from modelos.chamado import AUTOR_ESTAGIARIO, AUTOR_GESTOR
from modelos.usuario import PERFIL_ESTAGIARIO
from servicos.chamados import (
    ChamadoNaoEncontrado,
    ErroDeChamado,
    abrir_chamado,
    buscar_chamado,
    enviar_mensagem,
    listar_chamados,
    mudar_status,
)

router = APIRouter(prefix="/chamados", tags=["Chamados"])


def _resumo(chamado: Chamado) -> dict:
    """Campos do chamado + nomes e o resumo da conversa, para a lista."""
    return {
        "id": chamado.id,
        "estagiario_id": chamado.estagiario_id,
        "estagiario_nome": chamado.estagiario.nome,
        "gestor_id": chamado.gestor_id,
        "gestor_nome": chamado.gestor.nome,
        "titulo": chamado.titulo,
        "categoria": chamado.categoria,
        "prioridade": chamado.prioridade,
        "status": chamado.status,
        "aberto_em": chamado.aberto_em,
        "atualizado_em": chamado.atualizado_em,
        "resolvido_em": chamado.resolvido_em,
        "total_mensagens": len(chamado.mensagens),
        "ultima_mensagem_de": chamado.mensagens[-1].autor if chamado.mensagens else AUTOR_ESTAGIARIO,
    }


def _detalhe(chamado: Chamado) -> ChamadoDetalheResponse:
    return ChamadoDetalheResponse(**_resumo(chamado), mensagens=chamado.mensagens)


def _chamado_visivel(chamado_id: int, usuario: Usuario, session: Session) -> Chamado:
    """O chamado, se for do estagiario logado ou do gestor que o recebeu."""
    try:
        chamado = buscar_chamado(chamado_id, session)
    except ChamadoNaoEncontrado as erro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(erro)) from erro
    if usuario.perfil == PERFIL_ESTAGIARIO:
        permitido = chamado.estagiario_id == usuario.estagiario_id
    else:
        permitido = chamado.gestor_id == usuario.gestor_id
    if not permitido:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SEM_PERMISSAO)
    return chamado


def _executar(acao):
    """Roda a acao do servico traduzindo as excecoes em status code."""
    try:
        return acao()
    except ErroDeChamado as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro)) from erro
    except SQLAlchemyError as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o chamado.",
        ) from erro


@router.post(
    "",
    response_model=ChamadoDetalheResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abre um chamado para o gestor responsavel",
)
def criar(
    dados: ChamadoCreate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> ChamadoDetalheResponse:
    """O estagiario vem do login - nao existe estagiario_id no payload."""
    if usuario.perfil != PERFIL_ESTAGIARIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chamados sao abertos pelo estagiario.",
        )
    estagiario = exigir_o_proprio_estagiario(usuario.estagiario_id, usuario, session)
    chamado = _executar(lambda: abrir_chamado(
        estagiario, dados.titulo, dados.categoria, dados.prioridade, dados.descricao, session
    ))
    return _detalhe(chamado)


@router.get("", response_model=list[ChamadoResponse], summary="Lista os chamados que voce ve")
def listar(
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
    status_filtro: str | None = Query(
        default=None, alias="status", description="aberto, em_andamento ou resolvido"
    ),
) -> list[dict]:
    if usuario.perfil == PERFIL_ESTAGIARIO:
        chamados = listar_chamados(session, estagiario_id=usuario.estagiario_id, status=status_filtro)
    else:
        chamados = listar_chamados(session, gestor_id=exigir_gestor(usuario), status=status_filtro)
    return [_resumo(c) for c in chamados]


@router.get("/{chamado_id}", response_model=ChamadoDetalheResponse, summary="Chamado com a conversa")
def obter(
    chamado_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> ChamadoDetalheResponse:
    return _detalhe(_chamado_visivel(chamado_id, usuario, session))


@router.post(
    "/{chamado_id}/mensagens",
    response_model=ChamadoDetalheResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Escreve na conversa do chamado",
)
def escrever(
    chamado_id: int,
    dados: MensagemCreate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> ChamadoDetalheResponse:
    """O autor sai do perfil de quem esta logado, nao do payload."""
    chamado = _chamado_visivel(chamado_id, usuario, session)
    autor = AUTOR_ESTAGIARIO if usuario.perfil == PERFIL_ESTAGIARIO else AUTOR_GESTOR
    return _detalhe(_executar(lambda: enviar_mensagem(chamado, autor, dados.texto, session)))


@router.patch(
    "/{chamado_id}",
    response_model=ChamadoDetalheResponse,
    summary="Gestor muda o andamento (em andamento, resolvido)",
)
def andamento(
    chamado_id: int,
    dados: ChamadoStatusUpdate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> ChamadoDetalheResponse:
    exigir_gestor(usuario)
    chamado = _chamado_visivel(chamado_id, usuario, session)
    return _detalhe(_executar(lambda: mudar_status(chamado, dados.status, session)))
