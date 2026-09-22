"""Rotas de /solicitacoes - pedido de ajuste, aprovacao e auditoria.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).
Rota de exportacao em PDF: Arthur Linhares (Desenvolvedor 5 - secao 3.5).

Esta camada e fina de proposito: toda a regra esta em servicos/solicitacao.py.
Aqui so acontecem tres coisas - validar o payload (Pydantic), chamar o
servico, e traduzir o que ele levantou em status code:

    SolicitacaoNaoEncontrada -> 404 Not Found
    ErroDeSolicitacao        -> 409 Conflict
    payload torto            -> 422 (o proprio FastAPI responde)

Rotas:
    POST   /solicitacoes             estagiario pede a correcao
    GET    /solicitacoes             historico completo (auditoria)
    GET    /solicitacoes/pendentes   fila do gestor
    PATCH  /solicitacoes/{id}        gestor aprova ou rejeita
    GET    /solicitacoes/{id}/pdf    comprovante em PDF (funcionalidade 18)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.schemas import (
    SolicitacaoCreate,
    SolicitacaoDecisao,
    SolicitacaoDecisaoResponse,
    SolicitacaoResponse,
)
from banco.conexao import get_session
from modelos import Gestor, SolicitacaoAjuste
from modelos.solicitacao_ajuste import STATUS_APROVADO
from servicos.exportar_pdf import gerar_pdf_solicitacao
from servicos.solicitacao import (
    ErroDeSolicitacao,
    SolicitacaoNaoEncontrada,
    aprovar_solicitacao,
    criar_solicitacao,
    listar_pendentes,
    listar_solicitacoes,
    rejeitar_solicitacao,
)

router = APIRouter(prefix="/solicitacoes", tags=["Solicitacoes"])


def _montar_resposta(solicitacao: SolicitacaoAjuste) -> SolicitacaoResponse:
    """Junta a solicitacao com os dados que a tela precisa para exibi-la.

    O horario_atual e lido do registro na hora: depois de uma aprovacao ele
    passa a ser igual ao horario_sugerido, e e assim que a auditoria mostra
    que a correcao realmente foi aplicada.
    """
    registro = solicitacao.registro
    return SolicitacaoResponse(
        id=solicitacao.id,
        registro_id=solicitacao.registro_id,
        estagiario_id=solicitacao.estagiario_id,
        estagiario_nome=solicitacao.estagiario.nome,
        data_registro=registro.data,
        campo_alterado=solicitacao.campo_alterado,
        horario_atual=getattr(registro, solicitacao.campo_alterado),
        horario_sugerido=solicitacao.horario_sugerido,
        justificativa=solicitacao.justificativa,
        status=solicitacao.status,
        data_solicitacao=solicitacao.data_solicitacao,
        data_resposta=solicitacao.data_resposta,
        gestor_id=solicitacao.gestor_id,
        gestor_nome=solicitacao.gestor.nome if solicitacao.gestor else None,
    )


@router.post(
    "",
    response_model=SolicitacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abre um pedido de ajuste de ponto",
)
def abrir_solicitacao(
    dados: SolicitacaoCreate, session: Session = Depends(get_session)
) -> SolicitacaoResponse:
    """O estagiario pede a correcao de um horario de um dia ja registrado."""
    try:
        solicitacao = criar_solicitacao(
            registro_id=dados.registro_id,
            campo_alterado=dados.campo_alterado,
            horario_sugerido=dados.horario_sugerido,
            justificativa=dados.justificativa,
            session=session,
        )
    except SolicitacaoNaoEncontrada as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(erro)
        ) from erro
    except ErroDeSolicitacao as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(erro)
        ) from erro
    except SQLAlchemyError as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar a solicitacao.",
        ) from erro

    return _montar_resposta(solicitacao)


@router.get(
    "/pendentes",
    response_model=list[SolicitacaoResponse],
    summary="Fila de pedidos pendentes de um gestor",
)
def pendentes_do_gestor(
    session: Session = Depends(get_session),
    gestor_id: int = Query(description="Gestor dono da fila de aprovacoes."),
) -> list[SolicitacaoResponse]:
    """Pedidos pendentes dos estagiarios sob a gestao deste gestor.

    Esta rota vem ANTES de qualquer /solicitacoes/{id} no arquivo de
    proposito: o FastAPI testa as rotas na ordem em que foram declaradas, e
    se houvesse um GET /solicitacoes/{id} antes, "pendentes" seria lido como
    um id e daria erro de validacao.
    """
    gestor = session.query(Gestor).filter_by(id=gestor_id).first()
    if gestor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gestor {gestor_id} nao encontrado.",
        )

    return [_montar_resposta(item) for item in listar_pendentes(gestor_id, session)]


@router.get(
    "",
    response_model=list[SolicitacaoResponse],
    summary="Historico de solicitacoes (base da auditoria)",
)
def historico(
    session: Session = Depends(get_session),
    estagiario_id: int | None = Query(
        default=None, description="Filtra pelos pedidos de um estagiario."
    ),
    status_filtro: str | None = Query(
        default=None,
        alias="status",
        description="Filtra por pendente, aprovado ou rejeitado.",
    ),
) -> list[SolicitacaoResponse]:
    """Tudo que ja foi pedido, com quem respondeu e quando (funcionalidade 17).

    Sem filtro, devolve o historico inteiro - e a visao da tela de auditoria.
    """
    solicitacoes = listar_solicitacoes(
        session, estagiario_id=estagiario_id, status=status_filtro
    )
    return [_montar_resposta(item) for item in solicitacoes]


@router.patch(
    "/{solicitacao_id}",
    response_model=SolicitacaoDecisaoResponse,
    summary="Gestor aprova ou rejeita um pedido",
)
def decidir_solicitacao(
    solicitacao_id: int,
    decisao: SolicitacaoDecisao,
    session: Session = Depends(get_session),
) -> SolicitacaoDecisaoResponse:
    """Aprovar aplica o horario no registro; rejeitar nao encosta nele."""
    gestor = session.query(Gestor).filter_by(id=decisao.gestor_id).first()
    if gestor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gestor {decisao.gestor_id} nao encontrado.",
        )

    try:
        if decisao.status == STATUS_APROVADO:
            solicitacao, saldo = aprovar_solicitacao(
                solicitacao_id, decisao.gestor_id, session
            )
            mensagem = "Ajuste aprovado e aplicado no registro de ponto."
        else:
            solicitacao = rejeitar_solicitacao(
                solicitacao_id, decisao.gestor_id, session
            )
            saldo = None
            mensagem = "Pedido rejeitado. O registro de ponto continua como estava."
    except SolicitacaoNaoEncontrada as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(erro)
        ) from erro
    except ErroDeSolicitacao as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(erro)
        ) from erro
    except SQLAlchemyError as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel registrar a decisao.",
        ) from erro

    return SolicitacaoDecisaoResponse(
        solicitacao=_montar_resposta(solicitacao),
        saldo_acumulado=saldo,
        mensagem=mensagem,
    )


@router.get(
    "/{solicitacao_id}/pdf",
    summary="Baixa o comprovante em PDF de uma solicitacao (funcionalidade 18)",
)
def baixar_pdf(
    solicitacao_id: int, session: Session = Depends(get_session)
) -> Response:
    """Gera o PDF na hora (nao fica guardado em disco) e devolve como anexo.

    Sem response_model de proposito: o retorno aqui e bytes de PDF, nao um
    schema Pydantic - o mesmo motivo por tras de servicos/exportar_pdf.py
    trabalhar direto com o modelo SQLAlchemy em vez de um schema da API.
    """
    solicitacao = (
        session.query(SolicitacaoAjuste).filter_by(id=solicitacao_id).first()
    )
    if solicitacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitacao {solicitacao_id} nao encontrada.",
        )

    pdf_bytes = gerar_pdf_solicitacao(solicitacao)
    nome_arquivo = f"solicitacao_{solicitacao_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
