"""Rotas de /gestores - quem aprova ou rejeita os ajustes de ponto.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).

A tabela de gestores ja nasceu na fundacao (modelos/gestor.py), mas ate aqui
nao havia como cadastrar nenhum - e sem gestor cadastrado a fila de
aprovacoes seria sempre vazia. Estas duas rotas fecham esse buraco e
alimentam o seletor "Sou gestor" do app.py.

Segue o molde da fundacao (api/rotas/estagiarios.py).

Entrega 3 (login, Miguel): cadastrar gestor ficou restrito. O primeiro
gestor do banco se cadastra sozinho (alguem precisa comecar); depois disso,
so um gestor logado cadastra outro. Sem essa regra, um estagiario criaria
uma conta de gestor, se colocaria na equipe dela e aprovaria os proprios
ajustes. A lista continua aberta: o cadastro de estagiario precisa dela
para a pessoa escolher o gestor.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import usuario_opcional
from api.schemas import GestorCreate, GestorResponse
from banco.conexao import get_session
from modelos import Gestor, Usuario
from modelos.usuario import PERFIL_GESTOR
from servicos.autenticacao import EmailEmUso, nova_conta

router = APIRouter(prefix="/gestores", tags=["Gestores"])


@router.post(
    "",
    response_model=GestorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um gestor",
)
def criar_gestor(
    dados: GestorCreate,
    usuario: Usuario | None = Depends(usuario_opcional),
    session: Session = Depends(get_session),
) -> Gestor:
    """Cria o gestor e a conta dele. Os estagiarios escolhem o gestor no
    cadastro, ou sao vinculados depois pelo PATCH /estagiarios/{id}."""
    ja_existe_gestor = session.query(Gestor).first() is not None
    if ja_existe_gestor and (usuario is None or usuario.perfil != PERFIL_GESTOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="So um gestor logado pode cadastrar outro gestor.",
        )

    try:
        conta = nova_conta(dados.email, dados.senha, PERFIL_GESTOR, session)
    except EmailEmUso as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro)) from erro

    gestor = Gestor(nome=dados.nome)
    gestor.usuario = conta
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
    """Alimenta a escolha do gestor no cadastro do estagiario. Fica aberta
    (sem login) porque quem esta se cadastrando ainda nao tem conta; devolve
    so id e nome."""
    return session.query(Gestor).order_by(Gestor.nome).all()
