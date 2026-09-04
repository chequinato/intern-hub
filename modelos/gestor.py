"""Modelo Gestor - responsavel por um ou mais estagiarios.

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from banco.conexao import Base


class Gestor(Base):
    """Quem aprova ou rejeita as solicitacoes de ajuste dos seus estagiarios."""

    __tablename__ = "gestores"

    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)

    # Lado "um" do relacionamento um-para-muitos com Estagiario.
    estagiarios = relationship(
        "Estagiario",
        back_populates="gestor",
        order_by="Estagiario.nome",
    )

    def __repr__(self) -> str:
        return f"<Gestor id={self.id} nome={self.nome!r}>"
