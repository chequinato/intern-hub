"""Rotas de /gestores - quem aprova ou rejeita os ajustes de ponto.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).

A tabela de gestores ja nasceu na fundacao (modelos/gestor.py), mas ate aqui
nao havia como cadastrar nenhum - e sem gestor cadastrado a fila de
aprovacoes seria sempre vazia. Estas duas rotas fecham esse buraco e
alimentam o seletor "Sou gestor" do app.py.

Segue o molde da fundacao (api/rotas/estagiarios.py).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.schemas import GestorCreate, GestorResponse
from banco.conexao import get_session
from modelos import Gestor

router = APIRouter(prefix="/gestores", tags=["Gestores"])


@router.post(
    "",
    response_model=GestorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um gestor",
)
def criar_gestor(
    dados: GestorCreate, session: Session = Depends(get_session)
) -> Gestor:
    """Cria o gestor. Os estagiarios sao vinculados depois, pelo PATCH."""
    gestor = Gestor(nome=dados.nome)
    session.add(gestor)
    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o gestor.",
        ) from erro

    session.refresh(gestor)
    return gestor


@router.get(
    "",
    response_model=list[GestorResponse],
    summary="Lista os gestores cadastrados",
)
def listar_gestores(session: Session = Depends(get_session)) -> list[Gestor]:
    """Alimenta o seletor de perfil "Sou gestor" e o vinculo do estagiario."""
    return session.query(Gestor).order_by(Gestor.nome).all()
