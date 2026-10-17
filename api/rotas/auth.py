"""Rotas de /auth - entrar, sair, quem sou eu e trocar a senha.

Modulo dono: Miguel (Entrega 3).

O cadastro nao mora aqui: criar um estagiario (POST /estagiarios) ou um
gestor (POST /gestores) ja cria a conta junto, na mesma transacao. Aqui fica
so o que acontece com uma conta que ja existe.

Rotas:
    POST  /auth/entrar   e-mail e senha -> token (vale 12 horas)
    POST  /auth/sair     invalida o token atual
    GET   /auth/eu       quem e o dono do token
    PATCH /auth/senha    troca a senha (e derruba os outros logins)
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.permissoes import token_do_login, usuario_logado
from api.schemas import LoginRequest, LoginResponse, TrocarSenhaRequest, UsuarioResponse
from banco.conexao import get_session
from modelos import Usuario
from servicos.autenticacao import ErroDeLogin, entrar, sair, trocar_senha

router = APIRouter(prefix="/auth", tags=["Login"])


@router.post("/entrar", response_model=LoginResponse, summary="Entra com e-mail e senha")
def fazer_login(dados: LoginRequest, session: Session = Depends(get_session)) -> LoginResponse:
    """Devolve o token que vai no header Authorization das proximas chamadas.

    Tentativas erradas tem limite proprio de 10 por minuto por IP
    (api/seguranca.py), para ninguem testar senhas em sequencia.
    """
    try:
        token, sessao = entrar(dados.email, dados.senha, session)
    except ErroDeLogin as erro:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(erro)) from erro
    except SQLAlchemyError as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel abrir a sessao.",
        ) from erro

    return LoginResponse(
        token=token,
        expira_em=sessao.expira_em,
        usuario=UsuarioResponse.model_validate(sessao.usuario),
    )


@router.post("/sair", status_code=status.HTTP_204_NO_CONTENT, summary="Encerra o login atual")
def fazer_logout(
    token: str = Depends(token_do_login), session: Session = Depends(get_session)
) -> Response:
    sair(token, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/eu", response_model=UsuarioResponse, summary="Quem esta logado")
def quem_sou_eu(usuario: Usuario = Depends(usuario_logado)) -> Usuario:
    """O frontend chama ao abrir: se o token venceu, volta para o login."""
    return usuario


@router.patch("/senha", status_code=status.HTTP_204_NO_CONTENT, summary="Troca a propria senha")
def mudar_senha(
    dados: TrocarSenhaRequest,
    token: str = Depends(token_do_login),
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Response:
    try:
        trocar_senha(usuario, dados.senha_atual, dados.senha_nova, token, session)
    except ErroDeLogin as erro:
        # 400 e nao 401: a pessoa esta logada, so digitou a senha atual errada.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)) from erro
    return Response(status_code=status.HTTP_204_NO_CONTENT)
