"""Modelo Compromisso - a agenda do estagiario (provas, aulas, reunioes).

Modulo dono: Miguel (Entrega 3).

Por que existe: o estagiario concilia estagio e faculdade, e a Lei do
Estagio leva isso em conta. O art. 10, paragrafo 2o, da Lei 11.788/2008 diz
que, nos periodos de avaliacao, a carga horaria do estagio cai pelo menos
pela metade. Ate aqui o sistema nao sabia quando era dia de prova e cobrava
a meta cheia - o estagiario ficava devendo horas que a lei nao cobra.

Um compromisso do tipo "prova" faz a meta daquele dia cair pela metade no
saldo, no relatorio e no limite legal (servicos/agenda.py). Os outros tipos
sao so agenda: aparecem no painel e podem ir para o Google Agenda.

Recursos do SQLAlchemy usados aqui: Column, ForeignKey, relationship.
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from banco.conexao import Base

TIPO_PROVA = "prova"
TIPOS_COMPROMISSO = (TIPO_PROVA, "aula", "reuniao", "entrega", "outro")


class Compromisso(Base):
    """Um item da agenda de um estagiario."""

    __tablename__ = "compromissos"

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False, index=True)
    titulo = Column(String(120), nullable=False)
    tipo = Column(String(20), nullable=False)
    data = Column(Date, nullable=False)
    # Horario opcional: sem inicio, o compromisso vale o dia inteiro.
    inicio = Column(Time, nullable=True)
    fim = Column(Time, nullable=True)
    local = Column(String(120), nullable=True)
    observacao = Column(String(300), nullable=True)

    estagiario = relationship("Estagiario", back_populates="compromissos")

    def __repr__(self) -> str:
        return f"<Compromisso id={self.id} tipo={self.tipo!r} data={self.data}>"
