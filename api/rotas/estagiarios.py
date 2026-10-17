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

Entrega 3 (login, Miguel): o cadastro continua aberto - e por ele que o
estagiario cria a propria conta -, mas todas as outras rotas exigem login
e respeitam as regras de api/permissoes.py:
    - a lista mostra so quem a pessoa pode ver (a si mesma, ou a equipe);
    - a meta e os limites so mudam pelo gestor responsavel (antes o proprio
      estagiario podia baixar a meta e "ganhar" saldo);
    - so gestor vincula estagiario, e so os que estao sem gestor ou na
      equipe dele.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import (
    exigir_gestor,
    exigir_gestor_do_estagiario,
    exigir_ver_estagiario,
    usuario_logado,
)
from api.schemas import (
    ConfiguracaoResponse,
    ConfiguracaoUpdate,
    EstagiarioCreate,
    EstagiarioGestorUpdate,
    EstagiarioResponse,
)
from banco.conexao import get_session
from modelos import Configuracao, Estagiario, Gestor, Usuario
from modelos.usuario import PERFIL_ESTAGIARIO
from servicos.autenticacao import EmailEmUso, nova_conta

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
    """Cria o estagiario, a sua meta de horas e a conta de login em uma
    unica transacao.

    Ou os tres objetos sao gravados, ou nenhum: um estagiario sem
    configuracao quebraria o calculo de saldo mais a frente, e um sem conta
    nao conseguiria entrar no sistema.
    """
    if dados.gestor_id is not None:
        gestor = session.query(Gestor).filter_by(id=dados.gestor_id).first()
        if gestor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gestor {dados.gestor_id} nao encontrado.",
            )

    try:
        conta = nova_conta(dados.email, dados.senha, PERFIL_ESTAGIARIO, session)
    except EmailEmUso as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro)) from erro

    estagiario = Estagiario(nome=dados.nome, gestor_id=dados.gestor_id)
    estagiario.usuario = conta
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
    summary="Lista os estagiarios que voce pode ver",
)
def listar_estagiarios(
    usuario: Usuario = Depends(usuario_logado), session: Session = Depends(get_session)
) -> list[Estagiario]:
    """Sustenta o multiusuario (funcionalidade 10).

    Ate a Entrega 3 devolvia todo mundo, para o seletor de perfil. Com o
    login, o gestor ve a propria equipe e o estagiario ve so a si mesmo.
    """
    consulta = session.query(Estagiario)
    if usuario.perfil == PERFIL_ESTAGIARIO:
        consulta = consulta.filter(Estagiario.id == usuario.estagiario_id)
    else:
        consulta = consulta.filter(Estagiario.gestor_id == usuario.gestor_id)
    return consulta.order_by(Estagiario.nome).all()


@router.get(
    "/{estagiario_id}",
    response_model=EstagiarioResponse,
    summary="Consulta um estagiario especifico",
)
def obter_estagiario(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Estagiario:
    return exigir_ver_estagiario(estagiario_id, usuario, session)


@router.patch(
    "/{estagiario_id}",
    response_model=EstagiarioResponse,
    summary="Define ou troca o gestor responsavel pelo estagiario",
)
def vincular_gestor(
    estagiario_id: int,
    dados: EstagiarioGestorUpdate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Estagiario:
    """Acrescentada por Pedro Henrique (secao 3.4).

    Sem esta rota, o gestor so poderia ser escolhido no momento do cadastro
    do estagiario - e quem ja estava cadastrado antes dos gestores existirem
    nunca apareceria em nenhuma fila de aprovacao.

    Entrega 3 (login): so um gestor usa esta rota, e so para estagiario sem
    gestor (adotar) ou da propria equipe (repassar para outro gestor). Se o
    estagiario pudesse trocar o proprio gestor, poderia escolher um amigo
    para aprovar os ajustes dele.
    """
    gestor_logado = exigir_gestor(usuario)
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {estagiario_id} nao encontrado.",
        )
    if estagiario.gestor_id not in (None, gestor_logado):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este estagiario esta na equipe de outro gestor.",
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


@router.patch(
    "/{estagiario_id}/configuracao",
    response_model=ConfiguracaoResponse,
    summary="Altera a meta de horas e os limites do estagiario",
)
def alterar_configuracao(
    estagiario_id: int,
    dados: ConfiguracaoUpdate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Configuracao:
    """Acrescentada na Entrega 3 (Miguel).

    Ate aqui a meta so era definida no cadastro. So os campos enviados no
    payload mudam (exclude_unset): mandar so a meta diaria nao zera os
    limites. Mudar a meta muda o saldo na hora, porque ele nao fica gravado -
    e somado de novo a cada consulta (servicos/saldo.py).

    Com o login, so o gestor responsavel altera: a meta e contratual, e o
    estagiario que pudesse baixar a propria meta ganharia saldo sem
    trabalhar.
    """
    estagiario = exigir_gestor_do_estagiario(estagiario_id, usuario, session)

    configuracao = estagiario.configuracao
    if configuracao is None:
        configuracao = Configuracao()
        estagiario.configuracao = configuracao

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        if valor is not None:
            setattr(configuracao, campo, valor)

    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar a configuracao.",
        ) from erro

    session.refresh(configuracao)
    return configuracao
