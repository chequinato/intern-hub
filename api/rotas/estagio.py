"""Rotas de /estagio - termo de compromisso, recesso e relatorio de atividades.

Modulo dono: Miguel (Entrega 3).

Camada fina: confere quem esta logado (api/permissoes.py), chama
servicos/estagio.py e traduz excecao em status code (NaoEncontrado -> 404,
ErroDeEstagio -> 409, sem permissao -> 403).

Rotas:
    GET    /estagio/{id}                                contrato, saldo de recesso e pedidos
    PUT    /estagio/{id}/termo                          gestor cadastra/edita o termo
    POST   /estagio/recessos                            estagiario pede recesso
    GET    /estagio/recessos/pendentes                  fila de recesso do gestor
    PATCH  /estagio/recessos/{pedido_id}                gestor aprova ou rejeita
    DELETE /estagio/recessos/{pedido_id}                estagiario cancela (se pendente)
    POST   /estagio/atividades                          estagiario registra atividade
    DELETE /estagio/atividades/{atividade_id}           estagiario remove (semestre aberto)
    GET    /estagio/{id}/semestre/{ano}/{semestre}      relatorio do semestre
    PUT    /estagio/{id}/semestre/{ano}/{semestre}      gestor avalia (e valida)
    POST   /estagio/{id}/semestre/{ano}/{semestre}/ciencia   estagiario da ciencia
    GET    /estagio/{id}/semestre/{ano}/{semestre}/pdf  o relatorio em PDF
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import (
    SEM_PERMISSAO,
    exigir_gestor,
    exigir_gestor_do_estagiario,
    exigir_o_proprio_estagiario,
    exigir_ver_estagiario,
    usuario_logado,
)
from api.schemas import (
    AtividadeCreate,
    AtividadeResponse,
    AvaliacaoSemestre,
    ContratoResponse,
    EstagioResponse,
    RecessoCreate,
    RecessoDecisao,
    RecessoResponse,
    SemestreResponse,
    TermoUpdate,
)
from banco.conexao import get_session
from modelos import PedidoRecesso, Usuario
from modelos.usuario import PERFIL_ESTAGIARIO
from servicos import estagio as regras
from servicos.exportar_atividades import gerar_pdf_atividades

router = APIRouter(prefix="/estagio", tags=["Contrato de estagio"])

Ano = Annotated[int, Path(ge=2000, le=2100)]
Semestre = Annotated[int, Path(ge=1, le=2)]


def _hoje() -> date:
    """Data do servidor. Fica numa funcao para os testes poderem fixar o dia."""
    return date.today()


def _executar(acao):
    """Roda a regra traduzindo as excecoes do servico em status code."""
    try:
        return acao()
    except regras.NaoEncontrado as erro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(erro)) from erro
    except regras.ErroDeEstagio as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro)) from erro
    except SQLAlchemyError as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar.",
        ) from erro


def _recesso(pedido: PedidoRecesso) -> RecessoResponse:
    return RecessoResponse(
        id=pedido.id,
        estagiario_id=pedido.estagiario_id,
        estagiario_nome=pedido.estagiario.nome,
        data_inicio=pedido.data_inicio,
        data_fim=pedido.data_fim,
        dias=pedido.dias,
        observacao=pedido.observacao,
        status=pedido.status,
        pedido_em=pedido.pedido_em,
        respondido_em=pedido.respondido_em,
        gestor_nome=pedido.gestor.nome if pedido.gestor else None,
    )


def _estagiario_logado(usuario: Usuario, session: Session):
    if usuario.perfil != PERFIL_ESTAGIARIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SEM_PERMISSAO)
    return exigir_o_proprio_estagiario(usuario.estagiario_id, usuario, session)


# --- Recesso (rotas com caminho fixo vem antes de /{estagiario_id}) -----------------


@router.post("/recessos", response_model=RecessoResponse, status_code=status.HTTP_201_CREATED,
             summary="Pede um periodo de recesso (art. 13)")
def pedir_recesso(
    dados: RecessoCreate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> RecessoResponse:
    estagiario = _estagiario_logado(usuario, session)
    pedido = _executar(lambda: regras.pedir_recesso(
        estagiario, dados.data_inicio, dados.data_fim, dados.observacao, _hoje(), session
    ))
    return _recesso(pedido)


@router.get("/recessos/pendentes", response_model=list[RecessoResponse],
            summary="Pedidos de recesso esperando o gestor")
def recessos_pendentes(
    usuario: Usuario = Depends(usuario_logado), session: Session = Depends(get_session)
) -> list[RecessoResponse]:
    gestor_id = exigir_gestor(usuario)
    return [_recesso(p) for p in regras.recessos_pendentes_da_equipe(gestor_id, session)]


@router.patch("/recessos/{pedido_id}", response_model=RecessoResponse,
              summary="Gestor aprova ou rejeita um recesso")
def decidir_recesso(
    pedido_id: int,
    dados: RecessoDecisao,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> RecessoResponse:
    gestor_id = exigir_gestor(usuario)
    pedido = _executar(lambda: regras.buscar_recesso(pedido_id, session))
    exigir_gestor_do_estagiario(pedido.estagiario_id, usuario, session)
    pedido = _executar(lambda: regras.decidir_recesso(pedido, gestor_id, dados.status == "aprovado", session))
    return _recesso(pedido)


@router.delete("/recessos/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Estagiario cancela um pedido pendente")
def cancelar_recesso(
    pedido_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Response:
    pedido = _executar(lambda: regras.buscar_recesso(pedido_id, session))
    exigir_o_proprio_estagiario(pedido.estagiario_id, usuario, session)
    _executar(lambda: regras.cancelar_recesso(pedido, session))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Atividades ------------------------------------------------------------------


@router.post("/atividades", response_model=AtividadeResponse, status_code=status.HTTP_201_CREATED,
             summary="Registra uma atividade do estagio")
def registrar_atividade(
    dados: AtividadeCreate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
):
    estagiario = _estagiario_logado(usuario, session)
    return _executar(lambda: regras.registrar_atividade(estagiario, dados.data, dados.descricao, _hoje(), session))


@router.delete("/atividades/{atividade_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove uma atividade (so com o semestre aberto)")
def remover_atividade(
    atividade_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Response:
    atividade = _executar(lambda: regras.buscar_atividade(atividade_id, session))
    exigir_o_proprio_estagiario(atividade.estagiario_id, usuario, session)
    _executar(lambda: regras.remover_atividade(atividade, session))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Por estagiario -------------------------------------------------------------------


@router.get("/{estagiario_id}", response_model=EstagioResponse,
            summary="Contrato, saldo de recesso e pedidos do estagiario")
def obter_estagio(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> EstagioResponse:
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)
    hoje = _hoje()
    return EstagioResponse(
        contrato=regras.situacao_do_contrato(estagiario, hoje),
        recesso=regras.saldo_de_recesso(estagiario, hoje, session),
        pedidos=[_recesso(p) for p in reversed(estagiario.recessos)],
    )


@router.put("/{estagiario_id}/termo", response_model=ContratoResponse,
            summary="Gestor cadastra ou edita o termo de compromisso (art. 11)")
def salvar_termo(
    estagiario_id: int,
    dados: TermoUpdate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> dict:
    estagiario = exigir_gestor_do_estagiario(estagiario_id, usuario, session)
    _executar(lambda: regras.salvar_termo(estagiario, dados.model_dump(), session))
    return regras.situacao_do_contrato(estagiario, _hoje())


@router.get("/{estagiario_id}/semestre/{ano}/{semestre}", response_model=SemestreResponse,
            summary="Relatorio de atividades do semestre (art. 9o, VII)")
def obter_semestre(
    estagiario_id: int,
    ano: Ano,
    semestre: Semestre,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> dict:
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)
    return regras.resumo_do_semestre(estagiario, ano, semestre, session)


@router.put("/{estagiario_id}/semestre/{ano}/{semestre}", response_model=SemestreResponse,
            summary="Gestor avalia o semestre (validar=true fecha o relatorio)")
def avaliar_semestre(
    estagiario_id: int,
    dados: AvaliacaoSemestre,
    ano: Ano,
    semestre: Semestre,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> dict:
    estagiario = exigir_gestor_do_estagiario(estagiario_id, usuario, session)
    _executar(lambda: regras.avaliar_semestre(
        estagiario, ano, semestre, usuario.gestor_id, dados.avaliacao, dados.validar, session
    ))
    return regras.resumo_do_semestre(estagiario, ano, semestre, session)


@router.post("/{estagiario_id}/semestre/{ano}/{semestre}/ciencia", response_model=SemestreResponse,
             summary="Estagiario da ciencia do relatorio validado")
def dar_ciencia(
    estagiario_id: int,
    ano: Ano,
    semestre: Semestre,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> dict:
    estagiario = exigir_o_proprio_estagiario(estagiario_id, usuario, session)
    _executar(lambda: regras.dar_ciencia(estagiario, ano, semestre, session))
    return regras.resumo_do_semestre(estagiario, ano, semestre, session)


@router.get("/{estagiario_id}/semestre/{ano}/{semestre}/pdf",
            summary="Relatorio de atividades do semestre em PDF")
def baixar_pdf(
    estagiario_id: int,
    ano: Ano,
    semestre: Semestre,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Response:
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)
    conteudo = gerar_pdf_atividades(regras.resumo_do_semestre(estagiario, ano, semestre, session))
    nome = f"relatorio_atividades_{estagiario_id}_{ano}_{semestre}.pdf"
    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
