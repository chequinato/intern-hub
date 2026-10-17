"""Login: senha guardada em hash e sessoes com prazo de validade.

Modulo dono: Miguel (Entrega 3).

Tres decisoes que vale saber explicar:

1. A senha nunca e gravada. Gravamos um hash PBKDF2-SHA256 com "sal"
   aleatorio (hashlib, da biblioteca padrao do Python - nenhuma lib nova).
   O sal faz duas pessoas com a mesma senha terem hashes diferentes, e as
   200 mil iteracoes deixam cada tentativa de adivinhar lenta de proposito.
2. O token do login e aleatorio (secrets.token_urlsafe) e tambem so vai
   para o banco em hash (SHA-256). Quem tiver uma copia do banco nao
   consegue usar as sessoes abertas.
3. Errar o e-mail e errar a senha devolvem a MESMA mensagem. Assim a tela
   de login nao serve para descobrir quais e-mails tem conta.

Recursos do SQLAlchemy usados aqui: query().filter().first(),
query().filter().delete() (apaga as sessoes vencidas num comando so),
add()/commit()/rollback().
"""

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from modelos import SessaoLogin, Usuario

ALGORITMO = "pbkdf2_sha256"
# Fica numa constante (e nao fixo na funcao) para os testes poderem baixar o
# numero e rodar rapido - em producao, quanto mais, mais lenta a forca bruta.
ITERACOES = 200_000
DURACAO_SESSAO = timedelta(hours=12)
TAMANHO_MINIMO_SENHA = 8

MENSAGEM_LOGIN_INVALIDO = "E-mail ou senha incorretos."


class ErroDeLogin(Exception):
    """Credencial errada. Vira 401."""


def normalizar_email(email: str) -> str:
    """'  Lucas@Empresa.com ' e 'lucas@empresa.com' sao a mesma conta."""
    return email.strip().lower()


def gerar_hash_senha(senha: str) -> str:
    """Devolve 'pbkdf2_sha256$iteracoes$sal$hash', pronto para gravar."""
    sal = secrets.token_hex(16)
    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode(), sal.encode(), ITERACOES)
    return f"{ALGORITMO}${ITERACOES}${sal}${resumo.hex()}"


def conferir_senha(senha: str, senha_hash: str) -> bool:
    """Refaz o hash com o mesmo sal e compara em tempo constante."""
    try:
        algoritmo, iteracoes, sal, esperado = senha_hash.split("$")
    except ValueError:
        return False
    if algoritmo != ALGORITMO:
        return False
    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode(), sal.encode(), int(iteracoes))
    # compare_digest: mesmo motivo do token em api/seguranca.py - o "=="
    # para no primeiro caractere diferente e o tempo entrega a resposta.
    return secrets.compare_digest(resumo.hex(), esperado)


def _hash_do_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class EmailEmUso(Exception):
    """Ja existe conta com esse e-mail. Vira 409."""


def nova_conta(email: str, senha: str, perfil: str, session: Session) -> Usuario:
    """Monta a conta (sem gravar): quem chama liga ao estagiario ou ao gestor
    e faz o commit - assim a pessoa e a conta nascem na mesma transacao."""
    email = normalizar_email(email)
    if session.query(Usuario).filter(Usuario.email == email).first() is not None:
        raise EmailEmUso(f"Ja existe uma conta com o e-mail {email}.")
    return Usuario(email=email, senha_hash=gerar_hash_senha(senha), perfil=perfil)


def entrar(email: str, senha: str, session: Session) -> tuple[str, SessaoLogin]:
    """Confere a senha e abre uma sessao. Devolve (token, sessao)."""
    usuario = session.query(Usuario).filter(Usuario.email == normalizar_email(email)).first()
    if usuario is None or not conferir_senha(senha, usuario.senha_hash):
        raise ErroDeLogin(MENSAGEM_LOGIN_INVALIDO)

    agora = datetime.now()
    # Aproveita o login para limpar as sessoes vencidas DESTA pessoa. O
    # delete() direto na consulta apaga tudo num comando so, sem carregar
    # as linhas para o Python.
    session.query(SessaoLogin).filter(
        SessaoLogin.usuario_id == usuario.id, SessaoLogin.expira_em < agora
    ).delete()

    token = secrets.token_urlsafe(32)
    sessao = SessaoLogin(
        usuario=usuario,
        token_hash=_hash_do_token(token),
        criada_em=agora,
        expira_em=agora + DURACAO_SESSAO,
    )
    session.add(sessao)
    _salvar(session)
    return token, sessao


def usuario_do_token(token: str, session: Session) -> Usuario | None:
    """A conta dona do token, ou None se o token nao existe ou venceu."""
    sessao = (
        session.query(SessaoLogin)
        .filter(SessaoLogin.token_hash == _hash_do_token(token))
        .first()
    )
    if sessao is None or sessao.expira_em < datetime.now():
        return None
    return sessao.usuario


def sair(token: str, session: Session) -> None:
    """Apaga a sessao do token: a partir daqui ele nao vale mais."""
    session.query(SessaoLogin).filter(
        SessaoLogin.token_hash == _hash_do_token(token)
    ).delete()
    _salvar(session)


def trocar_senha(
    usuario: Usuario, senha_atual: str, senha_nova: str, token_atual: str, session: Session
) -> None:
    """Troca a senha e derruba os OUTROS logins abertos da pessoa.

    Se a senha vazou e alguem entrou com ela, trocar a senha precisa
    expulsar essa pessoa - por isso as outras sessoes sao apagadas. A sessao
    de quem esta trocando continua valendo.
    """
    if not conferir_senha(senha_atual, usuario.senha_hash):
        raise ErroDeLogin("A senha atual nao confere.")
    usuario.senha_hash = gerar_hash_senha(senha_nova)
    session.query(SessaoLogin).filter(
        SessaoLogin.usuario_id == usuario.id,
        SessaoLogin.token_hash != _hash_do_token(token_atual),
    ).delete()
    _salvar(session)


def _salvar(session: Session) -> None:
    """commit() com rollback() no erro - mesmo padrao dos outros servicos."""
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
