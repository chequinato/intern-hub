"""Modelo SolicitacaoAjuste - o pedido de correcao de um ponto ja registrado.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).

Por que esta tabela existe: o RegistroPonto e o fato ("foi isso que aconteceu").
Quando o estagiario esquece de marcar o retorno do almoco, a correcao nao pode
ser uma edicao silenciosa no registro - alguem precisa autorizar. Esta tabela
guarda o pedido, a justificativa, quem respondeu e quando, e por isso ela
sozinha ja resolve tambem a auditoria (funcionalidade 17 do README): nao
precisa de uma segunda tabela de historico.

Recursos do SQLAlchemy usados aqui: Column, ForeignKey, relationship, DateTime
com default.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from banco.conexao import Base

# Estados possiveis de uma solicitacao. Ficam como constantes para que rota,
# servico e tela usem exatamente a mesma palavra - um "aprovada" no plural em
# um lugar so quebraria o filtro do outro.
STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_REJEITADO = "rejeitado"

# Campos do RegistroPonto que uma solicitacao pode corrigir. A data do
# registro NAO entra nesta lista de proposito: mudar a data transformaria a
# correcao em um registro de outro dia, que e um caso diferente.
CAMPOS_AJUSTAVEIS = ("entrada", "saida", "saida_almoco", "retorno_almoco")


class SolicitacaoAjuste(Base):
    """Pedido de ajuste de um horario de um RegistroPonto."""

    __tablename__ = "solicitacoes_ajuste"

    id = Column(Integer, primary_key=True)

    # A qual marcacao de ponto o pedido se refere.
    registro_id = Column(Integer, ForeignKey("registros_ponto.id"), nullable=False)
    # Guardado tambem aqui (e nao so via registro.estagiario_id) porque a tela
    # de auditoria e a listagem do gestor filtram por estagiario o tempo todo,
    # e assim a consulta nao precisa de um join so para isso.
    estagiario_id = Column(Integer, ForeignKey("estagiarios.id"), nullable=False)

    # Qual horario corrigir ("entrada", "saida", "saida_almoco" ou
    # "retorno_almoco") e para qual valor.
    campo_alterado = Column(String(20), nullable=False)
    horario_sugerido = Column(Time, nullable=False)
    justificativa = Column(String(300), nullable=False)

    status = Column(String(20), nullable=False, default=STATUS_PENDENTE)

    # datetime.now sem parenteses: passamos a FUNCAO para o SQLAlchemy chamar
    # na hora do INSERT. Com parenteses, a hora seria a da subida da API e
    # todas as solicitacoes nasceriam com o mesmo horario.
    data_solicitacao = Column(DateTime, nullable=False, default=datetime.now)
    # So e preenchida quando o gestor aprova ou rejeita.
    data_resposta = Column(DateTime, nullable=True)
    gestor_id = Column(Integer, ForeignKey("gestores.id"), nullable=True)

    registro = relationship("RegistroPonto", back_populates="solicitacoes")
    estagiario = relationship("Estagiario", back_populates="solicitacoes")
    gestor = relationship("Gestor")

    def __repr__(self) -> str:
        return (
            f"<SolicitacaoAjuste id={self.id} registro_id={self.registro_id} "
            f"campo={self.campo_alterado!r} status={self.status!r}>"
        )
