"""Modelo Configuracao - a meta de horas de um estagiario.

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).

Os valores padrao vem da secao 11 do README ("Parametros e decisoes
fechadas"). Eles ficam aqui como constantes para que a API e as telas usem
a mesma fonte, em vez de repetir o numero -5.0 espalhado pelo codigo.
"""

from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from banco.conexao import Base

# Horas sao guardadas em decimal: 6.0 = 6 horas, 5.5 = 5 horas e 30 minutos.
META_HORAS_DIARIA_PADRAO = 6.0
META_HORAS_SEMANAL_PADRAO = 30.0
# Saldo em que o sistema dispara o alerta de horas negativas (README 11).
LIMITE_ALERTA_NEGATIVO_PADRAO = -5.0
# Meses ate um saldo positivo vencer se nao for compensado (README 11).
PRAZO_VENCIMENTO_MESES_PADRAO = 2
# Teto legal de horas do estagiario (Lei 11.788/2008, README secao 11 e
# funcionalidade 23). Fica configuravel, e nao travado no codigo, porque a
# propria lei permite calendario alternado com teto de 8h/40h.
LIMITE_MAXIMO_DIARIO_PADRAO = 6.0
LIMITE_MAXIMO_SEMANAL_PADRAO = 30.0


class Configuracao(Base):
    """Meta contratada e limites de um estagiario.

    O vinculo com Estagiario e um-para-um (unique=True no ForeignKey): cada
    estagiario tem uma unica meta ativa. Sem esse vinculo, o multiusuario
    (funcionalidade 10) nao funcionaria - todos dividiriam a mesma meta.
    """

    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(
        Integer, ForeignKey("estagiarios.id"), nullable=False, unique=True
    )

    meta_horas_diaria = Column(Float, nullable=False, default=META_HORAS_DIARIA_PADRAO)
    meta_horas_semanal = Column(Float, nullable=False, default=META_HORAS_SEMANAL_PADRAO)
    limite_alerta_negativo = Column(
        Float, nullable=False, default=LIMITE_ALERTA_NEGATIVO_PADRAO
    )
    prazo_vencimento_meses = Column(
        Integer, nullable=False, default=PRAZO_VENCIMENTO_MESES_PADRAO
    )
    limite_maximo_diario = Column(
        Float, nullable=False, default=LIMITE_MAXIMO_DIARIO_PADRAO
    )
    limite_maximo_semanal = Column(
        Float, nullable=False, default=LIMITE_MAXIMO_SEMANAL_PADRAO
    )

    estagiario = relationship("Estagiario", back_populates="configuracao")

    def __repr__(self) -> str:
        return (
            f"<Configuracao estagiario_id={self.estagiario_id} "
            f"meta_diaria={self.meta_horas_diaria}>"
        )
