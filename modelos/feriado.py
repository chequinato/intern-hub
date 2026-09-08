from sqlalchemy import Column, Integer, String, Date
from banco.conexao import Base

class Feriado(Base):
    __tablename__ = 'feriados'

    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, unique=True, nullable=False)
    descricao = Column(String, nullable=False)