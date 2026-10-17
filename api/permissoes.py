"""Quem esta logado e o que essa pessoa pode ver - as regras de acesso da API.

Modulo dono: Miguel (Entrega 3).

O login (servicos/autenticacao.py) diz QUEM e a pessoa. Este modulo diz o
que ela pode fazer. As regras sao poucas e valem para a API inteira:

    - o estagiario ve e altera so os PROPRIOS dados;
    - o gestor ve os dados dos estagiarios da equipe dele, mas nao bate
      ponto nem abre pedido em nome deles;
    - so o gestor responsavel decide pedidos de ajuste, responde chamados,
      altera a meta, cadastra feriado e desativa cracha.

Status code de cada caso:
    401 - nao mandou token, ou o token venceu / nao existe (faca login)
    403 - esta logado, mas aquilo nao e seu (sem permissao)
    404 - o id nao existe

As funcoes exigir_* recebem o usuario ja logado e levantam HTTPException:
cada rota chama a que precisa logo no comeco, antes de qualquer consulta.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from banco.conexao import get_session
from modelos import Estagiario, Usuario
from modelos.usuario import PERFIL_ESTAGIARIO, PERFIL_GESTOR
from servicos.autenticacao import usuario_do_token

# Header "Authorization: Bearer <token>". auto_error=False: sem o header, o
# FastAPI entrega None e quem decide a mensagem somos nos (401 em portugues).
# Tambem e o que faz aparecer o botao "Authorize" na pagina /docs.
_portador = HTTPBearer(auto_error=False)

SEM_LOGIN = "Faca login para continuar."
SEM_PERMISSAO = "Voce nao tem permissao para acessar estes dados."


def token_do_login(
    credenciais: HTTPAuthorizationCredentials | None = Security(_portador),
) -> str:
    """O token que veio no header, ou 401 se nao veio nenhum."""
    if credenciais is None or not credenciais.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=SEM_LOGIN)
    return credenciais.credentials


def usuario_logado(
    token: str = Depends(token_do_login), session: Session = Depends(get_session)
) -> Usuario:
    """Dependencia das rotas protegidas: a conta dona do token."""
    usuario = usuario_do_token(token, session)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sua sessao expirou. Faca login de novo.",
        )
    return usuario


def usuario_opcional(
    credenciais: HTTPAuthorizationCredentials | None = Security(_portador),
    session: Session = Depends(get_session),
) -> Usuario | None:
    """Como usuario_logado, mas sem exigir: devolve None se nao houver login.

    Usado no cadastro de gestor, que e aberto so enquanto nao existe nenhum
    gestor no banco (ver api/rotas/gestores.py).
    """
    if credenciais is None:
        return None
    return usuario_do_token(credenciais.credentials, session)


def _proibido() -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SEM_PERMISSAO)


def _buscar_estagiario(estagiario_id: int, session: Session) -> Estagiario:
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {estagiario_id} nao encontrado.",
        )
    return estagiario


def pode_ver_estagiario(usuario: Usuario, estagiario: Estagiario) -> bool:
    """O proprio estagiario, ou o gestor responsavel por ele."""
    if usuario.perfil == PERFIL_ESTAGIARIO:
        return usuario.estagiario_id == estagiario.id
    return usuario.gestor_id is not None and estagiario.gestor_id == usuario.gestor_id


def exigir_ver_estagiario(estagiario_id: int, usuario: Usuario, session: Session) -> Estagiario:
    """Leitura (saldo, relatorio, historico...): o proprio ou o gestor dele."""
    estagiario = _buscar_estagiario(estagiario_id, session)
    if not pode_ver_estagiario(usuario, estagiario):
        raise _proibido()
    return estagiario


def exigir_o_proprio_estagiario(
    estagiario_id: int, usuario: Usuario, session: Session
) -> Estagiario:
    """Escrita (bater ponto, pedir ajuste, abrir chamado): so a propria pessoa.

    O gestor ve, mas nao age no lugar do estagiario - senao um pedido de
    ajuste poderia ser aberto e aprovado pela mesma pessoa.
    """
    estagiario = _buscar_estagiario(estagiario_id, session)
    if usuario.perfil != PERFIL_ESTAGIARIO or usuario.estagiario_id != estagiario.id:
        raise _proibido()
    return estagiario


def exigir_gestor_do_estagiario(
    estagiario_id: int, usuario: Usuario, session: Session
) -> Estagiario:
    """Decisoes sobre o estagiario (meta, cracha): so o gestor responsavel."""
    estagiario = _buscar_estagiario(estagiario_id, session)
    if usuario.perfil != PERFIL_GESTOR or estagiario.gestor_id != usuario.gestor_id:
        raise _proibido()
    return estagiario


def exigir_gestor(usuario: Usuario) -> int:
    """Qualquer gestor logado. Devolve o id do gestor."""
    if usuario.perfil != PERFIL_GESTOR or usuario.gestor_id is None:
        raise _proibido()
    return usuario.gestor_id


def exigir_o_proprio_gestor(gestor_id: int, usuario: Usuario) -> None:
    """Rotas com gestor_id no caminho ou no payload: tem que ser voce."""
    if exigir_gestor(usuario) != gestor_id:
        raise _proibido()
