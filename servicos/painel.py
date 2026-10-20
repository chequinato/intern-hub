"""Paineis - o resumo que abre a area do estagiario e a do gestor.

Modulo dono: Miguel (Entrega 3).

Nao existe regra nova aqui: os paineis so juntam, numa resposta, numeros
que os outros servicos ja calculam (saldo.py, calculo.py, vencimento.py,
solicitacao.py, ponto.py). Antes a tela precisaria de cinco ou seis
requisicoes para montar o mesmo resumo; agora e uma.

Recursos do SQLAlchemy usados aqui: query().filter(), filter_by(),
order_by(), limit(), func.count(), e as consultas dos servicos chamados.

Entrega 3 (segunda parte): o painel do estagiario ganhou a agenda do dia
(com a meta reduzida em dia de prova) e os chamados em aberto; o do gestor
ganhou a contagem de chamados da equipe.
"""

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from modelos import Estagiario, RegistroPonto, SolicitacaoAjuste
from modelos.configuracao import (
    LIMITE_ALERTA_NEGATIVO_PADRAO,
    LIMITE_MAXIMO_DIARIO_PADRAO,
    LIMITE_MAXIMO_SEMANAL_PADRAO,
    META_HORAS_DIARIA_PADRAO,
    META_HORAS_SEMANAL_PADRAO,
)
from modelos.solicitacao_ajuste import STATUS_PENDENTE
from servicos.agenda import datas_de_prova, listar_compromissos, meta_do_dia
from servicos.calculo import calcular_horas_trabalhadas, verificar_pendencia_almoco
from servicos.chamados import contagem_por_status
from servicos.estagio import recessos_pendentes_da_equipe, saldo_de_recesso, situacao_do_contrato
from servicos.ponto import proxima_marcacao
from servicos.saldo import calcular_saldo_acumulado, saldo_por_mes, verificar_alerta
from servicos.vencimento import verificar_vencimento

CAMPOS_DO_ALMOCO = ("saida_almoco", "retorno_almoco")


def _config(estagiario: Estagiario) -> dict:
    """Metas e limites do estagiario, com os padroes do projeto como reserva."""
    c = estagiario.configuracao
    return {
        "meta_horas_diaria": c.meta_horas_diaria if c else META_HORAS_DIARIA_PADRAO,
        "meta_horas_semanal": c.meta_horas_semanal if c else META_HORAS_SEMANAL_PADRAO,
        "limite_alerta": c.limite_alerta_negativo if c else LIMITE_ALERTA_NEGATIVO_PADRAO,
        "limite_maximo_diario": c.limite_maximo_diario if c else LIMITE_MAXIMO_DIARIO_PADRAO,
        "limite_maximo_semanal": c.limite_maximo_semanal if c else LIMITE_MAXIMO_SEMANAL_PADRAO,
    }


def _horas(registro: RegistroPonto) -> float:
    return calcular_horas_trabalhadas(
        registro.entrada, registro.saida, registro.saida_almoco, registro.retorno_almoco
    )


def horas_da_semana(estagiario_id: int, hoje: date, session: Session) -> float:
    """Horas trabalhadas de segunda-feira ate hoje (inclusive)."""
    segunda = hoje - timedelta(days=hoje.weekday())
    registros = (
        session.query(RegistroPonto)
        .filter(
            RegistroPonto.estagiario_id == estagiario_id,
            RegistroPonto.data >= segunda,
            RegistroPonto.data <= hoje,
        )
        .all()
    )
    return round(sum(_horas(r) for r in registros), 2)


def _pedidos_pendentes(estagiario_id: int, session: Session) -> int:
    return (
        session.query(func.count(SolicitacaoAjuste.id))
        .filter(
            SolicitacaoAjuste.estagiario_id == estagiario_id,
            SolicitacaoAjuste.status == STATUS_PENDENTE,
        )
        .scalar()
    )


def _pendencias(estagiario_id: int, session: Session) -> list[dict]:
    """Dias fechados com o almoco incompleto - e se ja tem pedido aberto."""
    candidatos = (
        session.query(RegistroPonto)
        .filter(
            RegistroPonto.estagiario_id == estagiario_id,
            RegistroPonto.saida.is_not(None),
        )
        .filter(
            (RegistroPonto.saida_almoco.is_(None))
            | (RegistroPonto.retorno_almoco.is_(None))
        )
        .order_by(RegistroPonto.data.desc())
        .all()
    )
    pendencias = []
    for registro in candidatos:
        if not verificar_pendencia_almoco(registro):
            continue
        pedido_aberto = any(s.status == STATUS_PENDENTE for s in registro.solicitacoes)
        pendencias.append({
            "registro_id": registro.id,
            "data": registro.data,
            "campos_faltando": [c for c in CAMPOS_DO_ALMOCO if getattr(registro, c) is None],
            "pedido_aberto": pedido_aberto,
        })
    return pendencias


def resumo_estagiario(estagiario: Estagiario, hoje: date, session: Session) -> dict:
    """Tudo o que o painel inicial do estagiario mostra, numa resposta so."""
    config = _config(estagiario)
    saldo = calcular_saldo_acumulado(estagiario.id, session)

    registro_hoje = (
        session.query(RegistroPonto)
        .filter_by(estagiario_id=estagiario.id, data=hoje)
        .first()
    )
    ultimos = (
        session.query(RegistroPonto)
        .filter(RegistroPonto.estagiario_id == estagiario.id)
        .order_by(RegistroPonto.data.desc())
        .limit(10)
        .all()
    )

    dia_de_prova = hoje in datas_de_prova(estagiario.id, session, hoje, hoje)
    chamados = contagem_por_status(session, estagiario_id=estagiario.id)

    return {
        "estagiario_id": estagiario.id,
        "nome": estagiario.nome,
        "hoje": hoje,
        **config,
        "dia_de_prova_hoje": dia_de_prova,
        "meta_hoje": meta_do_dia(config["meta_horas_diaria"], hoje, {hoje} if dia_de_prova else set()),
        "compromissos_hoje": listar_compromissos(estagiario.id, session, hoje, hoje),
        "proximos_compromissos": listar_compromissos(
            estagiario.id, session, hoje + timedelta(days=1), hoje + timedelta(days=14)
        )[:5],
        "chamados_em_aberto": chamados["aberto"] + chamados["em_andamento"],
        "contrato": situacao_do_contrato(estagiario, hoje),
        "recesso": saldo_de_recesso(estagiario, hoje, session),
        "saldo_acumulado": saldo,
        "em_alerta": verificar_alerta(saldo, config["limite_alerta"]),
        "horas_semana": horas_da_semana(estagiario.id, hoje, session),
        "horas_hoje": _horas(registro_hoje) if registro_hoje else 0.0,
        "registro_hoje": registro_hoje,
        "proxima_marcacao": proxima_marcacao(registro_hoje),
        "pendencias": _pendencias(estagiario.id, session),
        "pedidos_pendentes": _pedidos_pendentes(estagiario.id, session),
        "aviso_vencimento": verificar_vencimento(estagiario.id, session),
        "ultimos_dias": [
            {
                "data": r.data,
                "horas_trabalhadas": _horas(r),
                "completo": r.saida is not None and not verificar_pendencia_almoco(r),
            }
            for r in reversed(ultimos)
        ],
        "tendencia": saldo_por_mes(estagiario.id, session),
    }


def resumo_equipe(gestor_id: int, hoje: date, session: Session) -> dict:
    """Visao do gestor: um resumo por estagiario dele e os totais da equipe."""
    equipe = (
        session.query(Estagiario)
        .filter(Estagiario.gestor_id == gestor_id)
        .order_by(Estagiario.nome)
        .all()
    )

    linhas = []
    for estagiario in equipe:
        config = _config(estagiario)
        saldo = calcular_saldo_acumulado(estagiario.id, session)
        semana = horas_da_semana(estagiario.id, hoje, session)
        ultimo = (
            session.query(func.max(RegistroPonto.data))
            .filter(RegistroPonto.estagiario_id == estagiario.id)
            .scalar()
        )
        recentes = (
            session.query(RegistroPonto)
            .filter(
                RegistroPonto.estagiario_id == estagiario.id,
                RegistroPonto.data > hoje - timedelta(days=7),
                RegistroPonto.data <= hoje,
            )
            .all()
        )
        acima_no_dia = sum(1 for r in recentes if _horas(r) > config["limite_maximo_diario"])
        linhas.append({
            "estagiario_id": estagiario.id,
            "nome": estagiario.nome,
            "saldo_acumulado": saldo,
            "em_alerta": verificar_alerta(saldo, config["limite_alerta"]),
            "limite_alerta": config["limite_alerta"],
            "horas_semana": semana,
            "limite_maximo_semanal": config["limite_maximo_semanal"],
            "meta_horas_semanal": config["meta_horas_semanal"],
            "acima_limite_semanal": semana > config["limite_maximo_semanal"],
            # A semana corrente pode ter so um ou dois dias (ex: segunda de
            # feriado); por isso o painel olha tambem os ultimos 7 dias.
            "dias_acima_limite_diario": acima_no_dia,
            "pendencias": len(_pendencias(estagiario.id, session)),
            "pedidos_pendentes": _pedidos_pendentes(estagiario.id, session),
            "ultimo_ponto": ultimo,
            "dias_para_fim_contrato": situacao_do_contrato(estagiario, hoje).get("dias_restantes"),
            "recessos_pendentes": sum(1 for r in estagiario.recessos if r.status == "pendente"),
        })

    chamados = contagem_por_status(session, gestor_id=gestor_id)

    return {
        "gestor_id": gestor_id,
        "hoje": hoje,
        "chamados_sem_resposta": chamados["aberto"],
        "chamados_em_andamento": chamados["em_andamento"],
        "contratos_vencendo": sum(
            1 for l in linhas
            if l["dias_para_fim_contrato"] is not None and 0 <= l["dias_para_fim_contrato"] <= 30
        ),
        "recessos_pendentes": len(recessos_pendentes_da_equipe(gestor_id, session)),
        "total_estagiarios": len(linhas),
        "em_alerta": sum(1 for l in linhas if l["em_alerta"]),
        "acima_limite_semanal": sum(1 for l in linhas if l["acima_limite_semanal"]),
        "acima_limite_legal": sum(
            1 for l in linhas if l["acima_limite_semanal"] or l["dias_acima_limite_diario"]
        ),
        "pedidos_na_fila": sum(l["pedidos_pendentes"] for l in linhas),
        "saldo_medio": round(sum(l["saldo_acumulado"] for l in linhas) / len(linhas), 2) if linhas else 0.0,
        "equipe": linhas,
    }
