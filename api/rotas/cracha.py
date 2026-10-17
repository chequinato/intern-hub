"""Rotas de /cracha - o cracha virtual e a verificacao publica pelo QR code.

Modulo dono: Miguel (Entrega 3).

Rotas:
    GET   /cracha/{estagiario_id}             dados do cracha (dono ou gestor)
    GET   /cracha/{estagiario_id}/qrcode.svg  a imagem do QR code
    POST  /cracha/{estagiario_id}/reemitir    codigo novo (dono ou gestor)
    PATCH /cracha/{estagiario_id}             gestor ativa ou desativa
    GET   /cracha/verificar/{codigo}          PUBLICA: o que o QR code abre

A verificacao e a unica rota de negocio sem login: quem escaneia o cracha
na portaria nao tem conta no sistema. Por isso ela devolve o minimo (nome,
gestor, ativo ou nao) e so responde a um codigo aleatorio de 22 caracteres -
nao da para "passear" pelos crachas trocando um numero no endereco.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import exigir_gestor_do_estagiario, exigir_ver_estagiario, usuario_logado
from api.schemas import CrachaResponse, CrachaStatusUpdate, CrachaVerificacaoResponse
from banco.conexao import get_session
from modelos import Estagiario, Usuario
from servicos.cracha import (
    buscar_por_codigo,
    definir_ativo,
    inicio_do_estagio,
    obter_cracha,
    qrcode_svg,
    reemitir,
)

router = APIRouter(prefix="/cracha", tags=["Cracha"])


def _endereco_do_frontend() -> str:
    """Para onde o QR code aponta: o primeiro endereco do FRONTEND_URL."""
    primeiro = (os.getenv("FRONTEND_URL") or "http://localhost:5173").split(",")[0]
    return primeiro.strip().rstrip("/")


def _url_verificacao(codigo: str) -> str:
    return f"{_endereco_do_frontend()}/verificar/{codigo}"


def _resposta(estagiario: Estagiario, session: Session) -> CrachaResponse:
    cracha = obter_cracha(estagiario, session)
    return CrachaResponse(
        estagiario_id=estagiario.id,
        nome=estagiario.nome,
        gestor_nome=estagiario.gestor.nome if estagiario.gestor else None,
        codigo=cracha.codigo,
        ativo=cracha.ativo,
        emitido_em=cracha.emitido_em,
        inicio_estagio=inicio_do_estagio(estagiario.id, session),
        url_verificacao=_url_verificacao(cracha.codigo),
    )


def _salvando(acao):
    try:
        return acao()
    except SQLAlchemyError as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o cracha.",
        ) from erro


# Declarada antes de /{estagiario_id}: o FastAPI testa as rotas na ordem, e
# "verificar" nao pode ser lido como um id (mesmo cuidado de
# /solicitacoes/pendentes).
@router.get(
    "/verificar/{codigo}",
    response_model=CrachaVerificacaoResponse,
    summary="Verificacao publica do cracha (o endereco do QR code)",
)
def verificar(codigo: str, session: Session = Depends(get_session)) -> CrachaVerificacaoResponse:
    cracha = buscar_por_codigo(codigo, session)
    if cracha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cracha nao encontrado. O codigo pode ter sido reemitido.",
        )
    estagiario = cracha.estagiario
    return CrachaVerificacaoResponse(
        nome=estagiario.nome,
        gestor_nome=estagiario.gestor.nome if estagiario.gestor else None,
        ativo=cracha.ativo,
        emitido_em=cracha.emitido_em,
        inicio_estagio=inicio_do_estagio(estagiario.id, session),
    )


@router.get("/{estagiario_id}", response_model=CrachaResponse, summary="Dados do cracha")
def obter(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> CrachaResponse:
    """Na primeira vez, o cracha e emitido (obter_cracha cria o codigo)."""
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)
    return _salvando(lambda: _resposta(estagiario, session))


@router.get("/{estagiario_id}/qrcode.svg", summary="QR code do cracha em SVG")
def baixar_qrcode(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Response:
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)
    cracha = _salvando(lambda: obter_cracha(estagiario, session))
    return Response(
        content=qrcode_svg(_url_verificacao(cracha.codigo)), media_type="image/svg+xml"
    )


@router.post(
    "/{estagiario_id}/reemitir",
    response_model=CrachaResponse,
    summary="Gera um codigo novo (o QR code antigo para de valer)",
)
def reemitir_cracha(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> CrachaResponse:
    """O proprio estagiario pode reemitir (perdeu o cracha impresso)."""
    estagiario = exigir_ver_estagiario(estagiario_id, usuario, session)
    cracha = _salvando(lambda: obter_cracha(estagiario, session))
    _salvando(lambda: reemitir(cracha, session))
    return _resposta(estagiario, session)


@router.patch(
    "/{estagiario_id}",
    response_model=CrachaResponse,
    summary="Gestor ativa ou desativa o cracha (fim do estagio)",
)
def ativar_ou_desativar(
    estagiario_id: int,
    dados: CrachaStatusUpdate,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> CrachaResponse:
    estagiario = exigir_gestor_do_estagiario(estagiario_id, usuario, session)
    cracha = _salvando(lambda: obter_cracha(estagiario, session))
    _salvando(lambda: definir_ativo(cracha, dados.ativo, session))
    return _resposta(estagiario, session)
