"""Rotas de /estagiarios.

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).

ESTE ARQUIVO E O MOLDE. Como a fundacao e a primeira parte do projeto, as
rotas dos proximos devs (registros, saldo, relatorio, solicitacoes...) devem
seguir exatamente este padrao:

    1. APIRouter com prefix e tags
    2. sessao injetada com Depends(get_session) - nunca abrir sessao na mao
    3. schema Pydantic validando a entrada
    4. commit() dentro de try, com rollback() no except
    5. status code explicito: 201 ao criar, 404 quando nao encontra
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.schemas import (
    EstagiarioCreate,
    EstagiarioGestorUpdate,
    EstagiarioResponse,
)
from banco.conexao import get_session
from modelos import Configuracao, Estagiario, Gestor

router = APIRouter(prefix="/estagiarios", tags=["Estagiarios"])


@router.post(
    "",
    response_model=EstagiarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um estagiario e a sua configuracao inicial",
)
def criar_estagiario(
    dados: EstagiarioCreate, session: Session = Depends(get_session)
) -> Estagiario:
    """Cria o estagiario e a sua meta de horas em uma unica transacao.

    Ou os dois objetos sao gravados, ou nenhum: um estagiario sem
    configuracao quebraria o calculo de saldo mais a frente.
    """
    if dados.gestor_id is not None:
        gestor = session.query(Gestor).filter_by(id=dados.gestor_id).first()
        if gestor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gestor {dados.gestor_id} nao encontrado.",
            )

    estagiario = Estagiario(nome=dados.nome, gestor_id=dados.gestor_id)
    # Atribuir pelo relationship deixa o SQLAlchemy preencher o estagiario_id
    # da configuracao sozinho, depois que o INSERT do estagiario gerar o id.
    estagiario.configuracao = Configuracao(
        meta_horas_diaria=dados.meta_horas_diaria,
        meta_horas_semanal=dados.meta_horas_semanal,
    )

    session.add(estagiario)
    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o estagiario.",
        ) from erro

    session.refresh(estagiario)
    return estagiario


@router.get(
    "",
    response_model=list[EstagiarioResponse],
    summary="Lista todos os estagiarios cadastrados",
)
def listar_estagiarios(session: Session = Depends(get_session)) -> list[Estagiario]:
    """Sustenta o multiusuario (funcionalidade 10).

    E esta rota que alimenta o seletor "Selecione seu nome" do app.py.
    """
    return session.query(Estagiario).order_by(Estagiario.nome).all()


@router.get(
    "/{estagiario_id}",
    response_model=EstagiarioResponse,
    summary="Consulta um estagiario especifico",
)
def obter_estagiario(
    estagiario_id: int, session: Session = Depends(get_session)
) -> Estagiario:
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {estagiario_id} nao encontrado.",
        )
    return estagiario


@router.patch(
    "/{estagiario_id}",
    response_model=EstagiarioResponse,
    summary="Define ou troca o gestor responsavel pelo estagiario",
)
def vincular_gestor(
    estagiario_id: int,
    dados: EstagiarioGestorUpdate,
    session: Session = Depends(get_session),
) -> Estagiario:
    """Acrescentada por Pedro Henrique (secao 3.4).

    Sem esta rota, o gestor so poderia ser escolhido no momento do cadastro
    do estagiario - e quem ja estava cadastrado antes dos gestores existirem
    nunca apareceria em nenhuma fila de aprovacao.
    """
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {estagiario_id} nao encontrado.",
        )

    if dados.gestor_id is not None:
        gestor = session.query(Gestor).filter_by(id=dados.gestor_id).first()
        if gestor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gestor {dados.gestor_id} nao encontrado.",
            )

    estagiario.gestor_id = dados.gestor_id
    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel atualizar o gestor do estagiario.",
        ) from erro

    session.refresh(estagiario)
    return estagiario
