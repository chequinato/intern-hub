"""Modelo RegistroPonto - uma marcacao de ponto de um dia.

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).
O calculo de horas em cima destes campos e da parte do Gustavo (secao 3.2).
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, Time
from sqlalchemy.orm import relationship

from banco.conexao import Base


class RegistroPonto(Base):
    """Entrada, saida e o intervalo de almoco de um dia de trabalho.

    saida_almoco e retorno_almoco sao campos separados, e nao um "intervalo"
    generico: o README exige distinguir os dois para detectar pendencia
    (quem esqueceu de marcar o retorno).
    """

    __tablename__ = "registros_ponto"

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False)
    data = Column(Date, nullable=False)

    # Nao existe registro de ponto sem hora de entrada.
    entrada = Column(Time, nullable=False)
    # Os demais nascem vazios e vao sendo preenchidos ao longo do dia. Um dia
    # que termina com almoco incompleto vira "pendencia" - regra implementada
    # por verificar_pendencia_almoco(), em servicos/calculo.py (Gustavo).
    saida = Column(Time, nullable=True)
    saida_almoco = Column(Time, nullable=True)
    retorno_almoco = Column(Time, nullable=True)

    estagiario = relationship("Estagiario", back_populates="registros")

    def __repr__(self) -> str:
        return f"<RegistroPonto id={self.id} estagiario_id={self.estagiario_id} data={self.data}>"
