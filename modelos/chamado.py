"""Modelos Chamado e MensagemChamado - pedidos de ajuda ao gestor.

Modulo dono: Miguel (Entrega 3).

Por que existe: a solicitacao de ajuste (modelos/solicitacao_ajuste.py) so
serve para corrigir um horario de ponto. Os outros problemas do dia a dia
do estagio - acesso bloqueado, computador com defeito, sistema fora do ar,
duvida sobre documento - nao tinham canal nenhum no sistema. O chamado e
esse canal: o estagiario abre, o gestor responsavel recebe na fila dele,
encaminha para quem resolve e marca o andamento.

O chamado tem uma conversa (MensagemChamado) em vez de um campo "resposta"
unico: estagiario e gestor podem trocar quantas mensagens precisarem, e o
historico fica inteiro, em ordem.

Recursos do SQLAlchemy usados aqui: ForeignKey, relationship com
cascade="all, delete-orphan" e order_by, DateTime com default.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from banco.conexao import Base

STATUS_ABERTO = "aberto"
STATUS_EM_ANDAMENTO = "em_andamento"
STATUS_RESOLVIDO = "resolvido"
STATUS_CHAMADO = (STATUS_ABERTO, STATUS_EM_ANDAMENTO, STATUS_RESOLVIDO)

CATEGORIAS_CHAMADO = ("acesso", "equipamento", "sistema", "documentacao", "outro")

PRIORIDADE_BAIXA = "baixa"
PRIORIDADE_MEDIA = "media"
PRIORIDADE_ALTA = "alta"
PRIORIDADES_CHAMADO = (PRIORIDADE_BAIXA, PRIORIDADE_MEDIA, PRIORIDADE_ALTA)

AUTOR_ESTAGIARIO = "estagiario"
AUTOR_GESTOR = "gestor"


class Chamado(Base):
    """Um problema que o estagiario nao resolve sozinho."""

    __tablename__ = "chamados"

    id = Column(Integer, primary_key=True)
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False)
    # Gravado na abertura (e nao lido de estagiario.gestor_id na hora): se o
    # estagiario trocar de gestor depois, o chamado antigo continua com quem
    # o recebeu.
    gestor_id = Column(Integer, ForeignKey("gestores.id"), nullable=False)

    titulo = Column(String(120), nullable=False)
    categoria = Column(String(20), nullable=False)
    prioridade = Column(String(10), nullable=False, default=PRIORIDADE_MEDIA)
    status = Column(String(20), nullable=False, default=STATUS_ABERTO)

    aberto_em = Column(DateTime, nullable=False, default=datetime.now)
    atualizado_em = Column(DateTime, nullable=False, default=datetime.now)
    resolvido_em = Column(DateTime, nullable=True)

    estagiario = relationship("Estagiario", back_populates="chamados")
    gestor = relationship("Gestor", back_populates="chamados")
    mensagens = relationship(
        "MensagemChamado",
        back_populates="chamado",
        cascade="all, delete-orphan",
        order_by="MensagemChamado.enviada_em",
    )

    def __repr__(self) -> str:
        return f"<Chamado id={self.id} status={self.status!r} titulo={self.titulo!r}>"


class MensagemChamado(Base):
    """Uma mensagem da conversa de um chamado."""

    __tablename__ = "mensagens_chamado"

    id = Column(Integer, primary_key=True)
    chamado_id = Column(Integer, ForeignKey("chamados.id"), nullable=False)
    # Quem escreveu: "estagiario" ou "gestor". Basta o papel, porque cada
    # chamado so tem um estagiario e um gestor.
    autor = Column(String(20), nullable=False)
    texto = Column(String(1000), nullable=False)
    enviada_em = Column(DateTime, nullable=False, default=datetime.now)

    chamado = relationship("Chamado", back_populates="mensagens")

    def __repr__(self) -> str:
        return f"<MensagemChamado id={self.id} chamado_id={self.chamado_id} autor={self.autor!r}>"
