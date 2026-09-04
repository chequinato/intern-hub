"""Modelo Estagiario - o usuario central do sistema.

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from banco.conexao import Base


class Estagiario(Base):
    """Estudante que registra ponto e acumula banco de horas."""

    __tablename__ = "estagiarios"

    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    # Opcional de proposito: hoje nao existe tela de cadastro de gestor (ela
    # nasce na parte do Pedro Henrique, secao 3.4). Exigir gestor aqui
    # travaria o cadastro de estagiario.
    gestor_id = Column(Integer, ForeignKey("gestores.id"), nullable=True)

    gestor = relationship("Gestor", back_populates="estagiarios")

    # Um estagiario tem exatamente uma configuracao ativa (README, secao 4).
    configuracao = relationship(
        "Configuracao",
        back_populates="estagiario",
        uselist=False,
        cascade="all, delete-orphan",
    )

    registros = relationship(
        "RegistroPonto",
        back_populates="estagiario",
        cascade="all, delete-orphan",
        order_by="RegistroPonto.data",
    )

    # Pedro Henrique (secao 3.4): quando modelos/solicitacao_ajuste.py existir,
    # descomente a linha abaixo e adicione o back_populates="estagiario" la.
    # Deixar declarado agora quebraria a inicializacao do SQLAlchemy, porque a
    # classe SolicitacaoAjuste ainda nao existe.
    # solicitacoes = relationship("SolicitacaoAjuste", back_populates="estagiario")

    def __repr__(self) -> str:
        return f"<Estagiario id={self.id} nome={self.nome!r}>"
