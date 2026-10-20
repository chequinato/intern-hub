"""Modelos do contrato de estagio: termo de compromisso, recesso e atividades.

Modulo dono: Miguel (Entrega 3).

Ate aqui o sistema controlava as HORAS. Estas tabelas controlam o ESTAGIO,
naquilo que a Lei 11.788/2008 exige da empresa:

- TermoCompromisso (art. 11): o estagio tem inicio e fim, e nao pode passar
  de 2 anos na mesma empresa (salvo pessoa com deficiencia). O sistema avisa
  o gestor quando o contrato esta para acabar.
- PedidoRecesso (art. 13): 30 dias de recesso por ano de estagio,
  proporcional quando o estagio tem menos de um ano. O estagiario pede, o
  gestor aprova; dia de recesso aprovado nao conta como falta.
- AtividadeEstagio + RelatorioAtividades (art. 9o, VII): a empresa envia a
  faculdade, no minimo a cada 6 meses, um relatorio de atividades "com vista
  obrigatoria ao estagiario". O estagiario registra o que fez; o gestor
  avalia e valida o semestre; o estagiario da ciencia; sai o PDF.

Por que tabelas novas, e nao colunas em Estagiario: o create_all so cria
tabelas que faltam - quem ja tem o banco nao perde nada (mesmo motivo do
cracha, modelos/cracha.py).

Recursos do SQLAlchemy usados aqui: ForeignKey com unique=True (1-para-1),
UniqueConstraint (um relatorio por estagiario e semestre), relationship com
cascade e order_by, Boolean, Date e DateTime com default.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from banco.conexao import Base

# Art. 11: duracao maxima do estagio na mesma parte concedente.
DURACAO_MAXIMA_ANOS = 2
# Art. 13: 30 dias de recesso por ano -> 2,5 dias por mes completo.
DIAS_RECESSO_POR_ANO = 30
# Aviso de fim de contrato com esta antecedencia.
AVISO_FIM_CONTRATO_DIAS = 30

RECESSO_PENDENTE = "pendente"
RECESSO_APROVADO = "aprovado"
RECESSO_REJEITADO = "rejeitado"

RELATORIO_ABERTO = "aberto"        # o estagiario ainda esta registrando
RELATORIO_VALIDADO = "validado"    # o gestor avaliou e fechou o semestre


class TermoCompromisso(Base):
    """Inicio e fim do estagio, como estao no termo de compromisso assinado."""

    __tablename__ = "termos_compromisso"

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False, unique=True)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    instituicao_ensino = Column(String(120), nullable=True)
    curso = Column(String(120), nullable=True)
    # Art. 11: o limite de 2 anos nao vale para estagiario com deficiencia.
    pessoa_com_deficiencia = Column(Boolean, nullable=False, default=False)

    estagiario = relationship("Estagiario", back_populates="termo")

    def __repr__(self) -> str:
        return f"<TermoCompromisso estagiario_id={self.estagiario_id} {self.data_inicio}..{self.data_fim}>"


class PedidoRecesso(Base):
    """Um periodo de recesso pedido pelo estagiario (dias corridos)."""

    __tablename__ = "pedidos_recesso"

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False, index=True)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    observacao = Column(String(300), nullable=True)
    status = Column(String(20), nullable=False, default=RECESSO_PENDENTE)
    pedido_em = Column(DateTime, nullable=False, default=datetime.now)
    respondido_em = Column(DateTime, nullable=True)
    gestor_id = Column(Integer, ForeignKey("gestores.id"), nullable=True)

    estagiario = relationship("Estagiario", back_populates="recessos")
    gestor = relationship("Gestor")

    @property
    def dias(self) -> int:
        """Dias corridos do periodo, contando o primeiro e o ultimo."""
        return (self.data_fim - self.data_inicio).days + 1

    def __repr__(self) -> str:
        return f"<PedidoRecesso id={self.id} {self.data_inicio}..{self.data_fim} status={self.status!r}>"


class AtividadeEstagio(Base):
    """Uma entrada do diario de atividades (o que foi feito no estagio)."""

    __tablename__ = "atividades_estagio"

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False, index=True)
    data = Column(Date, nullable=False)
    descricao = Column(String(1000), nullable=False)
    criada_em = Column(DateTime, nullable=False, default=datetime.now)

    estagiario = relationship("Estagiario", back_populates="atividades")

    def __repr__(self) -> str:
        return f"<AtividadeEstagio id={self.id} data={self.data}>"


class RelatorioAtividades(Base):
    """O fechamento de um semestre: avaliacao do gestor e ciencia do estagiario."""

    __tablename__ = "relatorios_atividades"
    # Um relatorio so por estagiario e semestre - o banco recusa o segundo.
    __table_args__ = (UniqueConstraint("estagiario_id", "ano", "semestre"),)

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False)
    ano = Column(Integer, nullable=False)
    semestre = Column(Integer, nullable=False)  # 1 (jan-jun) ou 2 (jul-dez)
    avaliacao_gestor = Column(String(1500), nullable=True)
    status = Column(String(20), nullable=False, default=RELATORIO_ABERTO)
    validado_em = Column(DateTime, nullable=True)
    gestor_id = Column(Integer, ForeignKey("gestores.id"), nullable=True)
    # "Vista obrigatoria ao estagiario" (art. 9o, VII): quando ele deu ciencia.
    ciente_em = Column(DateTime, nullable=True)

    estagiario = relationship("Estagiario", back_populates="relatorios_atividades")
    gestor = relationship("Gestor")

    def __repr__(self) -> str:
        return f"<RelatorioAtividades estagiario_id={self.estagiario_id} {self.ano}/{self.semestre}>"
