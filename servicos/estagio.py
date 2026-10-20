"""Regras do contrato de estagio: termo, recesso e relatorio de atividades.

Modulo dono: Miguel (Entrega 3).

As tres regras vem da Lei 11.788/2008 (ver modelos/estagio.py):

1. Termo de compromisso (art. 11) - o estagio tem fim e nao passa de 2 anos
   (exceto pessoa com deficiencia). A 30 dias do fim, o gestor e avisado.
2. Recesso (art. 13) - 30 dias por ano de estagio, proporcional: 2,5 dias
   por mes completo desde o inicio. Pedido pelo estagiario, aprovado pelo
   gestor; dia de recesso aprovado nao conta como falta no relatorio.
3. Relatorio de atividades (art. 9o, VII) - por semestre: o estagiario
   registra o que fez, o gestor avalia e valida, o estagiario da ciencia
   ("vista obrigatoria"). Depois de validado, o semestre fica fechado.

O servico levanta ErroDeEstagio (vira 409) e a rota traduz - mesmo desenho
de servicos/solicitacao.py e servicos/chamados.py.

Recursos do SQLAlchemy usados aqui: func.sum() sobre func.julianday() (dias
de recesso somados no banco, agrupados por status com group_by), filtro de
sobreposicao de periodos (inicio <= fim do outro E fim >= inicio do outro),
func.min(), e o calculo de horas reaproveitado de servicos/saldo.py.
"""

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from modelos import AtividadeEstagio, Estagiario, PedidoRecesso, RegistroPonto, RelatorioAtividades, TermoCompromisso
from modelos.estagio import (
    AVISO_FIM_CONTRATO_DIAS,
    DIAS_RECESSO_POR_ANO,
    DURACAO_MAXIMA_ANOS,
    RECESSO_APROVADO,
    RECESSO_PENDENTE,
    RECESSO_REJEITADO,
    RELATORIO_ABERTO,
    RELATORIO_VALIDADO,
)
from servicos.saldo import _filtro_dias_completos, _trabalhado_segundos


class ErroDeEstagio(Exception):
    """Regra do contrato violada. Vira 409."""


class NaoEncontrado(Exception):
    """Vira 404."""


# --- Termo de compromisso (art. 11) -------------------------------------------


def inicio_do_estagio(estagiario: Estagiario, session: Session) -> date | None:
    """Data do termo; sem termo cadastrado, a data do primeiro ponto."""
    if estagiario.termo is not None:
        return estagiario.termo.data_inicio
    return (
        session.query(func.min(RegistroPonto.data))
        .filter(RegistroPonto.estagiario_id == estagiario.id)
        .scalar()
    )


def validar_periodo_do_termo(inicio: date, fim: date, pessoa_com_deficiencia: bool) -> None:
    if fim <= inicio:
        raise ErroDeEstagio("O fim do estagio precisa ser depois do inicio.")
    limite = inicio + relativedelta(years=DURACAO_MAXIMA_ANOS)
    if fim > limite and not pessoa_com_deficiencia:
        raise ErroDeEstagio(
            f"O estagio nao pode passar de {DURACAO_MAXIMA_ANOS} anos na mesma empresa "
            f"(Lei 11.788/2008, art. 11). Para este inicio, o fim pode ir ate {limite.strftime('%d/%m/%Y')}."
        )


def salvar_termo(estagiario: Estagiario, dados: dict, session: Session) -> TermoCompromisso:
    """Cria ou atualiza o termo do estagiario (so o gestor responsavel chega aqui)."""
    validar_periodo_do_termo(dados["data_inicio"], dados["data_fim"], dados.get("pessoa_com_deficiencia", False))
    termo = estagiario.termo or TermoCompromisso()
    for campo, valor in dados.items():
        setattr(termo, campo, valor)
    estagiario.termo = termo
    _salvar(session)
    session.refresh(termo)
    return termo


def situacao_do_contrato(estagiario: Estagiario, hoje: date) -> dict:
    """Quantos dias faltam, se esta para vencer, se ja acabou."""
    termo = estagiario.termo
    if termo is None:
        return {"cadastrado": False}
    dias_restantes = (termo.data_fim - hoje).days
    return {
        "cadastrado": True,
        "data_inicio": termo.data_inicio,
        "data_fim": termo.data_fim,
        "instituicao_ensino": termo.instituicao_ensino,
        "curso": termo.curso,
        "pessoa_com_deficiencia": termo.pessoa_com_deficiencia,
        "dias_restantes": dias_restantes,
        "vencendo": 0 <= dias_restantes <= AVISO_FIM_CONTRATO_DIAS,
        "encerrado": dias_restantes < 0,
    }


# --- Recesso (art. 13) ----------------------------------------------------------


def _dias_por_status(estagiario_id: int, session: Session) -> dict[str, int]:
    """Dias corridos de recesso por status, somados no banco.

    julianday() transforma a data em numero de dias; fim - inicio + 1 da os
    dias corridos de cada pedido, e o group_by soma por status de uma vez.
    """
    dias = func.julianday(PedidoRecesso.data_fim) - func.julianday(PedidoRecesso.data_inicio) + 1
    linhas = (
        session.query(PedidoRecesso.status, func.sum(dias))
        .filter(PedidoRecesso.estagiario_id == estagiario_id)
        .group_by(PedidoRecesso.status)
        .all()
    )
    return {status: int(total or 0) for status, total in linhas}


def saldo_de_recesso(estagiario: Estagiario, hoje: date, session: Session) -> dict:
    """Direito acumulado (2,5 dias por mes completo), usado, pedido e disponivel."""
    inicio = inicio_do_estagio(estagiario, session)
    if inicio is None:
        meses = 0
    else:
        ate = min(hoje, estagiario.termo.data_fim) if estagiario.termo else hoje
        diferenca = relativedelta(ate, inicio)
        meses = max(diferenca.years * 12 + diferenca.months, 0)
    direito = int(meses * DIAS_RECESSO_POR_ANO / 12)
    por_status = _dias_por_status(estagiario.id, session)
    usados = por_status.get(RECESSO_APROVADO, 0)
    pedidos = por_status.get(RECESSO_PENDENTE, 0)
    return {
        "inicio_estagio": inicio,
        "meses_completos": meses,
        "direito": direito,
        "aprovados": usados,
        "pendentes": pedidos,
        "disponiveis": max(direito - usados - pedidos, 0),
    }


def pedir_recesso(
    estagiario: Estagiario, inicio: date, fim: date, observacao: str | None, hoje: date, session: Session
) -> PedidoRecesso:
    if fim < inicio:
        raise ErroDeEstagio("O fim do recesso precisa ser no mesmo dia ou depois do inicio.")
    if inicio < hoje:
        raise ErroDeEstagio("O recesso e pedido com antecedencia: escolha uma data a partir de hoje.")
    if estagiario.gestor_id is None:
        raise ErroDeEstagio("Voce ainda nao tem gestor responsavel - nao ha quem aprove o recesso.")
    if estagiario.termo is not None and fim > estagiario.termo.data_fim:
        raise ErroDeEstagio("O recesso precisa terminar antes do fim do contrato de estagio.")

    # Periodos se sobrepoem quando um comeca antes do outro terminar e
    # termina depois do outro comecar.
    choque = (
        session.query(PedidoRecesso)
        .filter(
            PedidoRecesso.estagiario_id == estagiario.id,
            PedidoRecesso.status.in_((RECESSO_PENDENTE, RECESSO_APROVADO)),
            PedidoRecesso.data_inicio <= fim,
            PedidoRecesso.data_fim >= inicio,
        )
        .first()
    )
    if choque is not None:
        raise ErroDeEstagio(
            f"Ja existe um recesso de {choque.data_inicio.strftime('%d/%m')} a "
            f"{choque.data_fim.strftime('%d/%m')} nesse periodo."
        )

    dias = (fim - inicio).days + 1
    saldo = saldo_de_recesso(estagiario, hoje, session)
    if dias > saldo["disponiveis"]:
        raise ErroDeEstagio(
            f"O pedido tem {dias} dia(s), mas voce tem {saldo['disponiveis']} dia(s) de recesso "
            f"disponiveis (2,5 por mes completo de estagio, Lei 11.788/2008, art. 13)."
        )

    pedido = PedidoRecesso(
        estagiario_id=estagiario.id, data_inicio=inicio, data_fim=fim,
        observacao=(observacao or "").strip() or None, status=RECESSO_PENDENTE,
    )
    session.add(pedido)
    _salvar(session)
    session.refresh(pedido)
    return pedido


def buscar_recesso(pedido_id: int, session: Session) -> PedidoRecesso:
    pedido = session.query(PedidoRecesso).filter_by(id=pedido_id).first()
    if pedido is None:
        raise NaoEncontrado(f"Pedido de recesso {pedido_id} nao encontrado.")
    return pedido


def decidir_recesso(pedido: PedidoRecesso, gestor_id: int, aprovar: bool, session: Session) -> PedidoRecesso:
    if pedido.status != RECESSO_PENDENTE:
        raise ErroDeEstagio(f"Este pedido ja foi respondido (status: {pedido.status}).")
    pedido.status = RECESSO_APROVADO if aprovar else RECESSO_REJEITADO
    pedido.respondido_em = datetime.now()
    pedido.gestor_id = gestor_id
    _salvar(session)
    session.refresh(pedido)
    return pedido


def cancelar_recesso(pedido: PedidoRecesso, session: Session) -> None:
    """O estagiario desiste de um pedido que ainda nao foi respondido."""
    if pedido.status != RECESSO_PENDENTE:
        raise ErroDeEstagio("So da para cancelar um pedido que ainda esta pendente.")
    session.delete(pedido)
    _salvar(session)


def recessos_pendentes_da_equipe(gestor_id: int, session: Session) -> list[PedidoRecesso]:
    return (
        session.query(PedidoRecesso)
        .join(Estagiario, PedidoRecesso.estagiario_id == Estagiario.id)
        .filter(Estagiario.gestor_id == gestor_id, PedidoRecesso.status == RECESSO_PENDENTE)
        .order_by(PedidoRecesso.data_inicio)
        .all()
    )


def datas_de_recesso(estagiario_id: int, session: Session, inicio: date, fim: date) -> set[date]:
    """Dias de recesso APROVADO no intervalo - o relatorio nao conta como falta."""
    pedidos = (
        session.query(PedidoRecesso)
        .filter(
            PedidoRecesso.estagiario_id == estagiario_id,
            PedidoRecesso.status == RECESSO_APROVADO,
            PedidoRecesso.data_inicio <= fim,
            PedidoRecesso.data_fim >= inicio,
        )
        .all()
    )
    dias = set()
    for p in pedidos:
        dia = max(p.data_inicio, inicio)
        while dia <= min(p.data_fim, fim):
            dias.add(dia)
            dia += timedelta(days=1)
    return dias


# --- Relatorio de atividades (art. 9o, VII) ------------------------------------------


def semestre_de(data: date) -> tuple[int, int]:
    return data.year, 1 if data.month <= 6 else 2


def periodo_do_semestre(ano: int, semestre: int) -> tuple[date, date]:
    if semestre == 1:
        return date(ano, 1, 1), date(ano, 6, 30)
    return date(ano, 7, 1), date(ano, 12, 31)


def _relatorio(estagiario_id: int, ano: int, semestre: int, session: Session) -> RelatorioAtividades | None:
    return (
        session.query(RelatorioAtividades)
        .filter_by(estagiario_id=estagiario_id, ano=ano, semestre=semestre)
        .first()
    )


def _semestre_fechado(estagiario_id: int, data: date, session: Session) -> bool:
    relatorio = _relatorio(estagiario_id, *semestre_de(data), session)
    return relatorio is not None and relatorio.status == RELATORIO_VALIDADO


def registrar_atividade(estagiario: Estagiario, data: date, descricao: str, hoje: date, session: Session) -> AtividadeEstagio:
    if data > hoje:
        raise ErroDeEstagio("Registre atividades que ja aconteceram (a data nao pode ser no futuro).")
    if _semestre_fechado(estagiario.id, data, session):
        raise ErroDeEstagio("O relatorio deste semestre ja foi validado pelo gestor: ele esta fechado.")
    atividade = AtividadeEstagio(estagiario_id=estagiario.id, data=data, descricao=descricao.strip())
    session.add(atividade)
    _salvar(session)
    session.refresh(atividade)
    return atividade


def buscar_atividade(atividade_id: int, session: Session) -> AtividadeEstagio:
    atividade = session.query(AtividadeEstagio).filter_by(id=atividade_id).first()
    if atividade is None:
        raise NaoEncontrado(f"Atividade {atividade_id} nao encontrada.")
    return atividade


def remover_atividade(atividade: AtividadeEstagio, session: Session) -> None:
    if _semestre_fechado(atividade.estagiario_id, atividade.data, session):
        raise ErroDeEstagio("O relatorio deste semestre ja foi validado: as atividades nao mudam mais.")
    session.delete(atividade)
    _salvar(session)


def resumo_do_semestre(estagiario: Estagiario, ano: int, semestre: int, session: Session) -> dict:
    """Tudo o que o relatorio semestral mostra (tela e PDF)."""
    inicio, fim = periodo_do_semestre(ano, semestre)
    atividades = (
        session.query(AtividadeEstagio)
        .filter(
            AtividadeEstagio.estagiario_id == estagiario.id,
            AtividadeEstagio.data >= inicio,
            AtividadeEstagio.data <= fim,
        )
        .order_by(AtividadeEstagio.data)
        .all()
    )
    # Mesma conta do saldo (servicos/saldo.py), so que limitada ao semestre.
    segundos, dias = (
        session.query(func.sum(_trabalhado_segundos()), func.count(RegistroPonto.id))
        .filter(*_filtro_dias_completos(estagiario.id), RegistroPonto.data >= inicio, RegistroPonto.data <= fim)
        .one()
    )
    relatorio = _relatorio(estagiario.id, ano, semestre, session)
    return {
        "estagiario_id": estagiario.id,
        "estagiario_nome": estagiario.nome,
        "ano": ano,
        "semestre": semestre,
        "inicio": inicio,
        "fim": fim,
        "horas_trabalhadas": round((segundos or 0) / 3600, 2),
        "dias_trabalhados": dias or 0,
        "atividades": atividades,
        "status": relatorio.status if relatorio else RELATORIO_ABERTO,
        "avaliacao_gestor": relatorio.avaliacao_gestor if relatorio else None,
        "validado_em": relatorio.validado_em if relatorio else None,
        "gestor_nome": relatorio.gestor.nome if relatorio and relatorio.gestor else None,
        "ciente_em": relatorio.ciente_em if relatorio else None,
        "instituicao_ensino": estagiario.termo.instituicao_ensino if estagiario.termo else None,
        "curso": estagiario.termo.curso if estagiario.termo else None,
    }


def avaliar_semestre(
    estagiario: Estagiario, ano: int, semestre: int, gestor_id: int, avaliacao: str, validar: bool, session: Session
) -> RelatorioAtividades:
    """O gestor escreve a avaliacao; com validar=True, fecha o semestre."""
    relatorio = _relatorio(estagiario.id, ano, semestre, session)
    if relatorio is not None and relatorio.status == RELATORIO_VALIDADO:
        raise ErroDeEstagio("Este semestre ja foi validado.")
    if validar:
        inicio, fim = periodo_do_semestre(ano, semestre)
        tem_atividade = (
            session.query(AtividadeEstagio.id)
            .filter(
                AtividadeEstagio.estagiario_id == estagiario.id,
                AtividadeEstagio.data >= inicio,
                AtividadeEstagio.data <= fim,
            )
            .first()
        )
        if tem_atividade is None:
            raise ErroDeEstagio("Nao da para validar um semestre sem nenhuma atividade registrada.")
        if not avaliacao.strip():
            raise ErroDeEstagio("Escreva a avaliacao antes de validar o semestre.")

    if relatorio is None:
        relatorio = RelatorioAtividades(estagiario_id=estagiario.id, ano=ano, semestre=semestre)
        session.add(relatorio)
    relatorio.avaliacao_gestor = avaliacao.strip() or None
    relatorio.gestor_id = gestor_id
    if validar:
        relatorio.status = RELATORIO_VALIDADO
        relatorio.validado_em = datetime.now()
    _salvar(session)
    session.refresh(relatorio)
    return relatorio


def dar_ciencia(estagiario: Estagiario, ano: int, semestre: int, session: Session) -> RelatorioAtividades:
    """O estagiario confirma que viu o relatorio validado (vista obrigatoria)."""
    relatorio = _relatorio(estagiario.id, ano, semestre, session)
    if relatorio is None or relatorio.status != RELATORIO_VALIDADO:
        raise ErroDeEstagio("O gestor ainda nao validou o relatorio deste semestre.")
    if relatorio.ciente_em is None:
        relatorio.ciente_em = datetime.now()
        _salvar(session)
        session.refresh(relatorio)
    return relatorio


def _salvar(session: Session) -> None:
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
