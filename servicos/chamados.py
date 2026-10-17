"""Regras dos chamados: o estagiario abre, o gestor acompanha e resolve.

Modulo dono: Miguel (Entrega 3).

Segue o mesmo desenho de servicos/solicitacao.py (Pedro Henrique): o
servico levanta excecao e a rota so traduz para status code. Quem pode
fazer o que (estagiario x gestor) e conferido antes, na rota, com as
funcoes de api/permissoes.py; aqui ficam as regras do proprio chamado:

    - so abre chamado quem tem gestor (senao ninguem receberia);
    - o andamento so vai para a frente: aberto -> em andamento -> resolvido;
    - chamado resolvido nao recebe mensagem nova (abra outro);
    - a primeira mensagem do gestor num chamado aberto ja o coloca
      "em andamento": responder e comecar a tratar.

Recursos do SQLAlchemy usados aqui: relationship (chamado.mensagens),
query().filter(), case() para ordenar por prioridade (alta primeiro),
func.count() com group_by() para o resumo por status do painel.
"""

from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from modelos import Chamado, Estagiario, MensagemChamado
from modelos.chamado import (
    AUTOR_ESTAGIARIO,
    AUTOR_GESTOR,
    PRIORIDADE_ALTA,
    PRIORIDADE_MEDIA,
    STATUS_ABERTO,
    STATUS_CHAMADO,
    STATUS_EM_ANDAMENTO,
    STATUS_RESOLVIDO,
)


class ChamadoNaoEncontrado(Exception):
    """Vira 404."""


class ErroDeChamado(Exception):
    """Regra do chamado violada. Vira 409."""


# Ordem de atendimento: alta primeiro. case() transforma o texto da
# prioridade num numero dentro do proprio ORDER BY do banco.
_ORDEM_PRIORIDADE = case(
    (Chamado.prioridade == PRIORIDADE_ALTA, 0),
    (Chamado.prioridade == PRIORIDADE_MEDIA, 1),
    else_=2,
)
# Resolvidos vao para o fim da lista.
_ORDEM_STATUS = case((Chamado.status == STATUS_RESOLVIDO, 1), else_=0)


def abrir_chamado(
    estagiario: Estagiario,
    titulo: str,
    categoria: str,
    prioridade: str,
    descricao: str,
    session: Session,
) -> Chamado:
    """Cria o chamado com a descricao como primeira mensagem da conversa."""
    if estagiario.gestor_id is None:
        raise ErroDeChamado(
            "Voce ainda nao tem gestor responsavel - nao ha quem receba o chamado."
        )

    agora = datetime.now()
    chamado = Chamado(
        estagiario_id=estagiario.id,
        gestor_id=estagiario.gestor_id,
        titulo=titulo.strip(),
        categoria=categoria,
        prioridade=prioridade,
        status=STATUS_ABERTO,
        aberto_em=agora,
        atualizado_em=agora,
    )
    # Pelo relationship: o SQLAlchemy grava o chamado e a mensagem juntos e
    # preenche o chamado_id da mensagem sozinho.
    chamado.mensagens.append(
        MensagemChamado(autor=AUTOR_ESTAGIARIO, texto=descricao.strip(), enviada_em=agora)
    )
    session.add(chamado)
    _salvar(session)
    session.refresh(chamado)
    return chamado


def buscar_chamado(chamado_id: int, session: Session) -> Chamado:
    chamado = session.query(Chamado).filter_by(id=chamado_id).first()
    if chamado is None:
        raise ChamadoNaoEncontrado(f"Chamado {chamado_id} nao encontrado.")
    return chamado


def listar_chamados(
    session: Session,
    estagiario_id: int | None = None,
    gestor_id: int | None = None,
    status: str | None = None,
) -> list[Chamado]:
    """Visao do estagiario (os dele) ou do gestor (os que ele recebeu).

    Ordem: os em aberto antes dos resolvidos, a prioridade alta primeiro e,
    empatando, o mais antigo primeiro - quem esta esperando ha mais tempo.
    """
    consulta = session.query(Chamado)
    if estagiario_id is not None:
        consulta = consulta.filter(Chamado.estagiario_id == estagiario_id)
    if gestor_id is not None:
        consulta = consulta.filter(Chamado.gestor_id == gestor_id)
    if status is not None:
        consulta = consulta.filter(Chamado.status == status)
    return consulta.order_by(_ORDEM_STATUS, _ORDEM_PRIORIDADE, Chamado.aberto_em).all()


def enviar_mensagem(chamado: Chamado, autor: str, texto: str, session: Session) -> Chamado:
    """Acrescenta uma mensagem a conversa do chamado."""
    if chamado.status == STATUS_RESOLVIDO:
        raise ErroDeChamado("Este chamado ja foi resolvido. Abra um novo se precisar.")

    agora = datetime.now()
    chamado.mensagens.append(MensagemChamado(autor=autor, texto=texto.strip(), enviada_em=agora))
    if autor == AUTOR_GESTOR and chamado.status == STATUS_ABERTO:
        chamado.status = STATUS_EM_ANDAMENTO
    chamado.atualizado_em = agora
    _salvar(session)
    session.refresh(chamado)
    return chamado


def mudar_status(chamado: Chamado, novo_status: str, session: Session) -> Chamado:
    """O gestor move o chamado para a frente (nunca para tras)."""
    if novo_status not in STATUS_CHAMADO:
        raise ErroDeChamado(f"Status invalido: {novo_status}.")

    atual = STATUS_CHAMADO.index(chamado.status)
    novo = STATUS_CHAMADO.index(novo_status)
    if novo <= atual:
        raise ErroDeChamado(
            f"O chamado ja esta {chamado.status.replace('_', ' ')} - o andamento so vai para a frente."
        )

    agora = datetime.now()
    chamado.status = novo_status
    chamado.atualizado_em = agora
    if novo_status == STATUS_RESOLVIDO:
        chamado.resolvido_em = agora
    _salvar(session)
    session.refresh(chamado)
    return chamado


def contagem_por_status(session: Session, **filtro) -> dict[str, int]:
    """{'aberto': 2, 'em_andamento': 1, 'resolvido': 5} - um GROUP BY so."""
    consulta = session.query(Chamado.status, func.count(Chamado.id))
    if filtro.get("estagiario_id") is not None:
        consulta = consulta.filter(Chamado.estagiario_id == filtro["estagiario_id"])
    if filtro.get("gestor_id") is not None:
        consulta = consulta.filter(Chamado.gestor_id == filtro["gestor_id"])
    contagem = dict(consulta.group_by(Chamado.status).all())
    return {status: contagem.get(status, 0) for status in STATUS_CHAMADO}


def _salvar(session: Session) -> None:
    """commit() com rollback() no erro - mesmo padrao de servicos/solicitacao.py."""
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
