"""Cracha virtual: codigo de verificacao e o QR code que aponta para ele.

Modulo dono: Miguel (Entrega 3).

O QR code e gerado aqui, no Python, com a lib qrcode - em SVG, que nao
precisa de biblioteca de imagem (Pillow) e fica nitido em qualquer tamanho,
inclusive impresso. Ele aponta para a pagina publica de verificacao do
frontend (/verificar/<codigo>), que consulta GET /cracha/verificar/<codigo>.

O que a verificacao mostra e o minimo para comprovar o vinculo: nome, gestor,
se o cracha esta ativo e desde quando. Nada de saldo, horario ou pendencia -
quem escaneia o cracha na portaria nao precisa (nem deve) ver o banco de
horas de ninguem.

Recursos do SQLAlchemy usados aqui: query().filter_by(), func.min() (data do
primeiro ponto = inicio do estagio), relationship (estagiario.cracha).
"""

import secrets
from datetime import date, datetime

import qrcode
import qrcode.image.svg
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from modelos import Cracha, Estagiario, RegistroPonto


def _novo_codigo() -> str:
    # 16 bytes aleatorios -> 22 caracteres de URL. Impossivel de adivinhar.
    return secrets.token_urlsafe(16)


def obter_cracha(estagiario: Estagiario, session: Session) -> Cracha:
    """O cracha do estagiario - emitido na primeira vez que alguem pede."""
    if estagiario.cracha is None:
        estagiario.cracha = Cracha(codigo=_novo_codigo(), ativo=True, emitido_em=datetime.now())
        _salvar(session)
        session.refresh(estagiario)
    return estagiario.cracha


def reemitir(cracha: Cracha, session: Session) -> Cracha:
    """Codigo novo (cracha perdido): o QR code antigo deixa de valer na hora."""
    cracha.codigo = _novo_codigo()
    cracha.emitido_em = datetime.now()
    cracha.ativo = True
    _salvar(session)
    session.refresh(cracha)
    return cracha


def definir_ativo(cracha: Cracha, ativo: bool, session: Session) -> Cracha:
    """O gestor desativa (fim do estagio) ou reativa o cracha."""
    cracha.ativo = ativo
    _salvar(session)
    session.refresh(cracha)
    return cracha


def inicio_do_estagio(estagiario_id: int, session: Session) -> date | None:
    """A data do primeiro ponto - o mesmo func.min() do relatorio (Pietro)."""
    return (
        session.query(func.min(RegistroPonto.data))
        .filter(RegistroPonto.estagiario_id == estagiario_id)
        .scalar()
    )


def buscar_por_codigo(codigo: str, session: Session) -> Cracha | None:
    return session.query(Cracha).filter_by(codigo=codigo).first()


def qrcode_svg(conteudo: str) -> bytes:
    """O QR code de `conteudo` (a URL de verificacao) em SVG."""
    imagem = qrcode.make(
        conteudo,
        image_factory=qrcode.image.svg.SvgPathImage,
        border=1,
        # Correcao de erro M: o QR continua lendo com ate ~15% da imagem
        # danificada (cracha impresso amassado, tela trincada).
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    return imagem.to_string()


def _salvar(session: Session) -> None:
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
