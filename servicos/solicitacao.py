"""Regras das solicitacoes de ajuste de ponto.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).

Aqui mora a regra do fluxo "estagiario pede, gestor decide": quem pode pedir
o que, o que torna um pedido invalido, e o que acontece com o RegistroPonto
quando o gestor aprova.

Duas decisoes deste modulo que vale saber explicar:

1. O servico levanta EXCECAO em vez de devolver mensagem de erro. Assim a
   rota (api/rotas/solicitacoes.py) fica sendo so um tradutor de excecao para
   status code HTTP, e as mesmas regras podem ser testadas com pytest sem
   subir a API.
2. Aprovar NAO grava o horario sugerido as cegas: antes de escrever no
   registro, o servico monta como o dia FICARIA e passa essa combinacao pela
   mesma validacao que a rota de registro usa (validar_ordem_dos_horarios,
   em servicos/calculo.py). Sem isso, uma aprovacao distraida deixaria no
   banco um dia com retorno do almoco depois da saida - um estado que a
   propria API recusaria se alguem tentasse cadastrar direto.

Recursos do SQLAlchemy usados aqui: query().join(), filter(), filter_by(),
order_by(), commit()/rollback().
"""

from datetime import datetime, time

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from modelos import Estagiario, RegistroPonto, SolicitacaoAjuste
from modelos.solicitacao_ajuste import (
    CAMPOS_AJUSTAVEIS,
    STATUS_APROVADO,
    STATUS_PENDENTE,
    STATUS_REJEITADO,
)
from servicos.calculo import validar_ordem_dos_horarios
from servicos.saldo import calcular_saldo_acumulado


class SolicitacaoNaoEncontrada(Exception):
    """Pediram uma solicitacao (ou um registro) que nao existe. Vira 404."""


class ErroDeSolicitacao(Exception):
    """Regra de negocio violada (pedido repetido, ja respondido...). Vira 409."""


def criar_solicitacao(
    registro_id: int,
    campo_alterado: str,
    horario_sugerido: time,
    justificativa: str,
    session: Session,
) -> SolicitacaoAjuste:
    """Cria um pedido de correcao para um horario de um registro existente.

    O estagiario nao vem por parametro de proposito: ele e lido do proprio
    registro. Assim ninguem consegue abrir um pedido em nome de outra pessoa
    mandando um estagiario_id diferente no payload.
    """
    registro = session.query(RegistroPonto).filter_by(id=registro_id).first()
    if registro is None:
        raise SolicitacaoNaoEncontrada(f"Registro {registro_id} nao encontrado.")

    if campo_alterado not in CAMPOS_AJUSTAVEIS:
        raise ErroDeSolicitacao(
            f"O campo {campo_alterado} nao pode ser ajustado. "
            f"Escolha um entre: {', '.join(CAMPOS_AJUSTAVEIS)}."
        )

    # Dois pedidos pendentes para o mesmo horario do mesmo dia se anulariam:
    # o gestor aprovaria o primeiro e o segundo apagaria a decisao dele.
    repetido = (
        session.query(SolicitacaoAjuste)
        .filter_by(
            registro_id=registro_id,
            campo_alterado=campo_alterado,
            status=STATUS_PENDENTE,
        )
        .first()
    )
    if repetido is not None:
        raise ErroDeSolicitacao(
            f"Ja existe um pedido pendente para o campo {campo_alterado} "
            f"do dia {registro.data.isoformat()}."
        )

    if horario_sugerido == getattr(registro, campo_alterado):
        raise ErroDeSolicitacao(
            "O horario sugerido e igual ao que ja esta no registro - "
            "nao ha o que corrigir."
        )

    # Falha cedo: se o horario sugerido ja deixaria o dia fora de ordem, nao
    # faz sentido ocupar a fila do gestor com um pedido impossivel.
    problema = _problema_no_dia_ajustado(registro, campo_alterado, horario_sugerido)
    if problema is not None:
        raise ErroDeSolicitacao(f"Horario sugerido invalido: {problema}.")

    solicitacao = SolicitacaoAjuste(
        registro_id=registro.id,
        estagiario_id=registro.estagiario_id,
        campo_alterado=campo_alterado,
        horario_sugerido=horario_sugerido,
        justificativa=justificativa.strip(),
        status=STATUS_PENDENTE,
    )
    session.add(solicitacao)
    _salvar(session)
    session.refresh(solicitacao)
    return solicitacao


def listar_pendentes(gestor_id: int, session: Session) -> list[SolicitacaoAjuste]:
    """Fila do gestor: so os pedidos pendentes dos estagiarios dele.

    O join com Estagiario e o que garante isso - sem ele, um gestor veria os
    pedidos de estagiarios de outro gestor.
    """
    return (
        session.query(SolicitacaoAjuste)
        .join(Estagiario, SolicitacaoAjuste.estagiario_id == Estagiario.id)
        .filter(
            Estagiario.gestor_id == gestor_id,
            SolicitacaoAjuste.status == STATUS_PENDENTE,
        )
        .order_by(SolicitacaoAjuste.data_solicitacao)
        .all()
    )


def listar_solicitacoes(
    session: Session,
    estagiario_id: int | None = None,
    status: str | None = None,
) -> list[SolicitacaoAjuste]:
    """Historico completo - e a consulta que sustenta a tela de auditoria.

    Sem filtro nenhum devolve tudo (visao do gestor). Com estagiario_id
    devolve so os pedidos daquela pessoa (visao do estagiario na tela dele).
    Mais recentes primeiro, que e a ordem que a auditoria pede.
    """
    consulta = session.query(SolicitacaoAjuste)
    if estagiario_id is not None:
        consulta = consulta.filter(SolicitacaoAjuste.estagiario_id == estagiario_id)
    if status is not None:
        consulta = consulta.filter(SolicitacaoAjuste.status == status)
    return consulta.order_by(SolicitacaoAjuste.data_solicitacao.desc()).all()


def aprovar_solicitacao(
    solicitacao_id: int, gestor_id: int, session: Session
) -> tuple[SolicitacaoAjuste, float]:
    """Aplica o horario sugerido no registro original e fecha o pedido.

    Devolve a solicitacao ja aprovada e o saldo do estagiario recalculado
    depois da correcao - e esse numero que a tela do gestor mostra para ele
    ver o efeito do que acabou de aprovar.
    """
    solicitacao = _buscar_pendente_do_gestor(solicitacao_id, gestor_id, session)
    registro = solicitacao.registro

    problema = _problema_no_dia_ajustado(
        registro, solicitacao.campo_alterado, solicitacao.horario_sugerido
    )
    if problema is not None:
        raise ErroDeSolicitacao(
            f"Aprovar deixaria o dia {registro.data.isoformat()} inconsistente: "
            f"{problema}. Peca um novo horario ao estagiario."
        )

    # setattr porque o campo a alterar vem como texto ("saida_almoco"). E o
    # mesmo que escrever registro.saida_almoco = horario_sugerido, so que
    # decidido em tempo de execucao.
    setattr(registro, solicitacao.campo_alterado, solicitacao.horario_sugerido)

    solicitacao.status = STATUS_APROVADO
    solicitacao.data_resposta = datetime.now()
    solicitacao.gestor_id = gestor_id

    _salvar(session)
    session.refresh(solicitacao)

    # O saldo nao fica guardado em lugar nenhum: ele e somado no banco toda
    # vez que alguem pergunta (servicos/saldo.py, func.sum). Entao corrigir o
    # registro ja e "recalcular o saldo" - aqui so lemos o valor novo.
    saldo = calcular_saldo_acumulado(solicitacao.estagiario_id, session)
    return solicitacao, saldo


def rejeitar_solicitacao(
    solicitacao_id: int, gestor_id: int, session: Session
) -> SolicitacaoAjuste:
    """Fecha o pedido como rejeitado, sem encostar no RegistroPonto.

    O registro fica exatamente como estava - inclusive com a pendencia de
    almoco, se era esse o caso. Rejeitar nao apaga o pedido: ele continua no
    historico da auditoria, com a data da resposta e quem respondeu.
    """
    solicitacao = _buscar_pendente_do_gestor(solicitacao_id, gestor_id, session)

    solicitacao.status = STATUS_REJEITADO
    solicitacao.data_resposta = datetime.now()
    solicitacao.gestor_id = gestor_id

    _salvar(session)
    session.refresh(solicitacao)
    return solicitacao


# --- Funcoes de apoio --------------------------------------------------------


def _buscar_pendente_do_gestor(
    solicitacao_id: int, gestor_id: int, session: Session
) -> SolicitacaoAjuste:
    """Busca a solicitacao e confere que ESTE gestor pode decidir sobre ela."""
    solicitacao = session.query(SolicitacaoAjuste).filter_by(id=solicitacao_id).first()
    if solicitacao is None:
        raise SolicitacaoNaoEncontrada(f"Solicitacao {solicitacao_id} nao encontrada.")

    if solicitacao.status != STATUS_PENDENTE:
        raise ErroDeSolicitacao(
            f"Esta solicitacao ja foi respondida (status: {solicitacao.status})."
        )

    # Quem decide e o gestor responsavel por aquele estagiario, e mais ninguem.
    if solicitacao.estagiario.gestor_id != gestor_id:
        raise ErroDeSolicitacao("Este estagiario nao esta sob a gestao deste gestor.")

    return solicitacao


def _problema_no_dia_ajustado(
    registro: RegistroPonto, campo_alterado: str, horario_sugerido: time
) -> str | None:
    """Simula a correcao e diz o que quebraria, ou None se ficar tudo certo.

    Monta os quatro horarios como eles FICARIAM depois do ajuste (sem gravar
    nada) e entrega para validar_ordem_dos_horarios, a mesma funcao que a
    rota de registro usa.
    """
    horarios = {
        "entrada": registro.entrada,
        "saida": registro.saida,
        "saida_almoco": registro.saida_almoco,
        "retorno_almoco": registro.retorno_almoco,
    }
    horarios[campo_alterado] = horario_sugerido

    if horarios["entrada"] is None:
        return "o registro ficaria sem hora de entrada"

    return validar_ordem_dos_horarios(
        horarios["entrada"],
        horarios["saida"],
        horarios["saida_almoco"],
        horarios["retorno_almoco"],
    )


def _salvar(session: Session) -> None:
    """commit() com rollback() no erro - o mesmo padrao das rotas da fundacao.

    A excecao do SQLAlchemy sobe como ela e, de proposito: falha de banco nao
    e regra de negocio, entao a rota a transforma em 500, e nao em 409.
    """
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
