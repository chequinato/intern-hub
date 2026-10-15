"""Modelo Feriado - um dia nao util do calendario.

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Dia cadastrado aqui nao cobra ponto: o relatorio mensal nao conta falta
nele (servicos/feriados.py, eh_dia_util). Nao tem chave estrangeira: vale
para todos os estagiarios e e consultado pela data.

Recursos do SQLAlchemy usados aqui: Column com unique=True (nao existe
feriado repetido no mesmo dia) e index=True.
"""

from sqlalchemy import Column, Date, Integer, String

from banco.conexao import Base


class Feriado(Base):
    """Um dia nao util, com a descricao que aparece na tela."""

    __tablename__ = "feriados"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, unique=True, nullable=False)
    descricao = Column(String(120), nullable=False)

    def __repr__(self) -> str:
        return f"<Feriado data={self.data} descricao={self.descricao!r}>"
