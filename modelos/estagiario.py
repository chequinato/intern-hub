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

    # Pedro Henrique (secao 3.4): os pedidos de ajuste de ponto desta pessoa.
    # Apagar o estagiario apaga junto as solicitacoes dele - sem o cascade,
    # sobrariam linhas apontando para um estagiario que nao existe mais.
    solicitacoes = relationship(
        "SolicitacaoAjuste",
        back_populates="estagiario",
        cascade="all, delete-orphan",
        order_by="SolicitacaoAjuste.data_solicitacao",
    )

    def __repr__(self) -> str:
        return f"<Estagiario id={self.id} nome={self.nome!r}>"
