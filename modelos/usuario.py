"""Modelos Usuario e SessaoLogin - quem pode entrar no sistema, e com qual senha.

Modulo dono: Miguel (Entrega 3).

Ate a Entrega 3 a tela de entrada era um seletor de perfil: qualquer pessoa
escolhia "Sou gestor" e aprovava os proprios pedidos de ajuste. O login
fecha esse buraco - cada conta pertence a UM estagiario ou a UM gestor, e a
API so mostra os dados que aquela conta pode ver (api/permissoes.py).

Por que duas tabelas:
- Usuario guarda as credenciais (e-mail e o HASH da senha, nunca a senha).
- SessaoLogin guarda cada login aberto. O token devolvido no login fica
  aqui (tambem em hash), com prazo de validade. Sair do sistema e so apagar
  a linha - um token que nao esta na tabela nao vale mais.

Por que Usuario e separado de Estagiario/Gestor: os dois perfis entram pela
mesma tela, com o mesmo tipo de credencial. Colocar email/senha nas duas
tabelas duplicaria a regra; aqui ela mora uma vez so.

Recursos do SQLAlchemy usados aqui: ForeignKey com unique=True (um-para-um
com Estagiario e com Gestor), relationship com cascade, Column com index.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from banco.conexao import Base

PERFIL_ESTAGIARIO = "estagiario"
PERFIL_GESTOR = "gestor"
PERFIS = (PERFIL_ESTAGIARIO, PERFIL_GESTOR)


class Usuario(Base):
    """A conta de acesso de um estagiario ou de um gestor."""

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    # index=True: o login procura a conta pelo e-mail toda vez.
    email = Column(String(120), nullable=False, unique=True, index=True)
    # Formato "pbkdf2_sha256$iteracoes$sal$hash" (servicos/autenticacao.py).
    senha_hash = Column(String(200), nullable=False)
    perfil = Column(String(20), nullable=False)

    # Exatamente um dos dois fica preenchido, conforme o perfil. unique=True:
    # uma pessoa tem uma conta so.
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=True, unique=True)
    gestor_id = Column(Integer, ForeignKey("gestores.id"), nullable=True, unique=True)

    criado_em = Column(DateTime, nullable=False, default=datetime.now)

    estagiario = relationship("Estagiario", back_populates="usuario")
    gestor = relationship("Gestor", back_populates="usuario")
    sessoes = relationship(
        "SessaoLogin", back_populates="usuario", cascade="all, delete-orphan"
    )

    @property
    def nome(self) -> str:
        """Nome de quem e dono da conta (o login nao guarda nome proprio)."""
        dono = self.estagiario if self.perfil == PERFIL_ESTAGIARIO else self.gestor
        return dono.nome if dono is not None else self.email

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email!r} perfil={self.perfil!r}>"


class SessaoLogin(Base):
    """Um login aberto: o token (em hash) e ate quando ele vale."""

    __tablename__ = "sessoes_login"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # O token em si so existe na resposta do login e no navegador da pessoa.
    # Aqui fica o SHA-256 dele: quem copiar o banco nao consegue entrar.
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    criada_em = Column(DateTime, nullable=False, default=datetime.now)
    expira_em = Column(DateTime, nullable=False)

    usuario = relationship("Usuario", back_populates="sessoes")

    def __repr__(self) -> str:
        return f"<SessaoLogin id={self.id} usuario_id={self.usuario_id}>"
