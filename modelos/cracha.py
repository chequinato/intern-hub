"""Modelo Cracha - o cracha virtual do estagiario, com codigo para QR code.

Modulo dono: Miguel (Entrega 3).

Por que existe: o cracha serve para comprovar o vinculo de estagio (na
portaria, no RH, na faculdade) sem expor dado nenhum do banco de horas. O
QR code aponta para uma pagina publica de verificacao que mostra so o nome,
o gestor e se o cracha esta ATIVO.

Por que uma tabela propria, e nao uma coluna em Estagiario:
- o codigo pode ser reemitido (cracha perdido): o antigo deixa de valer na
  hora, porque a verificacao procura o codigo NOVO;
- o gestor pode desativar o cracha (fim do estagio) sem apagar o
  estagiario nem o historico de ponto;
- e uma tabela nova nao exige mexer na tabela de estagiarios de quem ja tem
  o banco criado (o create_all so cria tabelas que faltam, nao colunas).

Recursos do SQLAlchemy usados aqui: ForeignKey com unique=True (um-para-um),
Boolean com default, relationship.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from banco.conexao import Base


class Cracha(Base):
    """O cracha virtual de um estagiario."""

    __tablename__ = "crachas"

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False, unique=True)
    # Codigo aleatorio (secrets.token_urlsafe): nao da para adivinhar o
    # cracha de outra pessoa trocando um numero na URL.
    codigo = Column(String(32), nullable=False, unique=True, index=True)
    ativo = Column(Boolean, nullable=False, default=True)
    emitido_em = Column(DateTime, nullable=False, default=datetime.now)

    estagiario = relationship("Estagiario", back_populates="cracha")

    def __repr__(self) -> str:
        return f"<Cracha estagiario_id={self.estagiario_id} ativo={self.ativo}>"
