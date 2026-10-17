"""Rotas de /relatorio - o resumo do mes, a tendencia e a exportacao.

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).
Exportacao em PDF/Excel: Arthur Linhares (secao 3.5).
Tendencia mes a mes: Miguel (Entrega 3).

O relatorio junta o que outros servicos ja calculam (horas do dia em
servicos/calculo.py, saldo em servicos/saldo.py, vencimento em
servicos/vencimento.py, dia util em servicos/feriados.py) e acrescenta a
conta propria dele: as faltas do mes.

Entrega 3 (login, Miguel): o relatorio abre para o proprio estagiario e
para o gestor dele (api/permissoes.py).

Recursos do SQLAlchemy usados aqui: extract("month"/"year") para filtrar o
mes, func.min() para achar o primeiro ponto do estagiario, filter(),
filter_by() e order_by().
"""

import calendar
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from api.permissoes import exigir_ver_estagiario, usuario_logado
from api.schemas import RelatorioMensalResponse, TendenciaMes
from banco.conexao import get_session
from modelos.configuracao import META_HORAS_DIARIA_PADRAO, Configuracao
from modelos.registro_ponto import RegistroPonto
from modelos.usuario import Usuario
from servicos.agenda import datas_de_prova, meta_do_dia
from servicos.calculo import calcular_horas_trabalhadas
from servicos.exportar_relatorio import gerar_relatorio_excel, gerar_relatorio_pdf
from servicos.feriados import eh_dia_util
from servicos.saldo import calcular_saldo_acumulado, saldo_por_mes
from servicos.vencimento import verificar_vencimento

router = APIRouter(prefix="/relatorio", tags=["Relatório"])


@router.get(
    "/{estagiario_id}/tendencia",
    response_model=list[TendenciaMes],
    summary="Saldo mes a mes (tendencia do semestre, funcionalidade 19)",
)
def obter_tendencia(
    estagiario_id: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> list[dict]:
    """Acrescentada na Entrega 3 (Miguel). A conta, com group_by() no banco,
    mora em servicos/saldo.py (saldo_por_mes).

    Declarada antes de /{estagiario_id} por clareza - as duas nao conflitam,
    porque esta tem um pedaco a mais no caminho.
    """
    exigir_ver_estagiario(estagiario_id, usuario, session)
    return saldo_por_mes(estagiario_id, session)


@router.get(
    "/{estagiario_id}",
    response_model=RelatorioMensalResponse,
    summary="Resumo do mes: horas, faltas, saldo e evolucao dia a dia",
)
def obter_relatorio(
    estagiario_id: int,
    mes: int,
    ano: int,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> dict:
    """Monta o relatorio de um mes em quatro passos (comentados abaixo)."""
    exigir_ver_estagiario(estagiario_id, usuario, session)
    # 1. Os registros de ponto do mes, em ordem de data.
    registros_mes = (
        session.query(RegistroPonto)
        .filter(
            RegistroPonto.estagiario_id == estagiario_id,
            extract("month", RegistroPonto.data) == mes,
            extract("year", RegistroPonto.data) == ano,
        )
        .order_by(RegistroPonto.data)
        .all()
    )

    # A meta diaria vem da configuracao DESTE estagiario. Antes estava fixa em
    # 6.0 no codigo, o que dava saldo diario errado para quem tem outra meta.
    configuracao = (
        session.query(Configuracao).filter_by(estagiario_id=estagiario_id).first()
    )
    meta_diaria = (
        configuracao.meta_horas_diaria
        if configuracao is not None
        else META_HORAS_DIARIA_PADRAO
    )

    # 2. Horas de cada dia e o saldo do dia (horas - meta). Entrega 3: em dia
    # de prova a meta e a metade (Lei 11.788/2008, servicos/agenda.py).
    primeiro_do_mes = date(ano, mes, 1)
    ultimo_do_mes = date(ano, mes, calendar.monthrange(ano, mes)[1])
    provas = datas_de_prova(estagiario_id, session, primeiro_do_mes, ultimo_do_mes)
    total_horas = 0.0
    evolucao = []
    for registro in registros_mes:
        horas_dia = calcular_horas_trabalhadas(
            registro.entrada, registro.saida, registro.saida_almoco, registro.retorno_almoco
        )
        total_horas += horas_dia
        evolucao.append({
            "data": registro.data,
            "horas_trabalhadas": horas_dia,
            "saldo_do_dia": round(horas_dia - meta_do_dia(meta_diaria, registro.data, provas), 2),
            "dia_de_prova": registro.data in provas,
        })

    # 3. Faltas: dia util (sem fim de semana e sem feriado), ja passado, sem
    # ponto. Um conjunto (set) com os dias trabalhados deixa a busca rapida.
    dias_trabalhados = {registro.data.day for registro in registros_mes}
    faltas = 0
    # Entrega 3: alem do total, a lista das datas - o calendario do
    # relatorio pinta cada falta no dia certo, com a mesma regra daqui.
    datas_faltas = []
    hoje = date.today()
    ultimo_dia_mes = calendar.monthrange(ano, mes)[1]

    # No mes atual, dia que ainda nao chegou nao e falta; nos meses passados,
    # a conta vai ate o ultimo dia (30 ou 31).
    dia_limite = hoje.day if (ano == hoje.year and mes == hoje.month) else ultimo_dia_mes

    # Só conta falta a partir do primeiro ponto que o estagiário bateu na
    # vida. Antes, a conta começava sempre no dia 1: quem começou o estágio
    # no dia 28 aparecia com 20 faltas em setembro. func.min() pede ao banco a
    # menor data, sem trazer os registros para o Python.
    primeiro_registro = (
        session.query(func.min(RegistroPonto.data))
        .filter(RegistroPonto.estagiario_id == estagiario_id)
        .scalar()
    )

    for dia in range(1, dia_limite + 1):
        data_atual = date(ano, mes, dia)
        if primeiro_registro is None or data_atual < primeiro_registro:
            continue
        if eh_dia_util(data_atual, session) and dia not in dias_trabalhados:
            faltas += 1
            datas_faltas.append(data_atual)

    # 4. Saldo do banco de horas (todo o periodo) e aviso de vencimento.
    saldo_atual = calcular_saldo_acumulado(estagiario_id, session)
    aviso = verificar_vencimento(estagiario_id, session)

    return {
        "mes": mes,
        "ano": ano,
        "total_horas_trabalhadas": round(total_horas, 2),
        "dias_uteis_trabalhados": len(registros_mes),
        "faltas": faltas,
        "datas_faltas": datas_faltas,
        "saldo_acumulado": saldo_atual,
        "aviso_vencimento": aviso,
        "evolucao_diaria": evolucao,
        "datas_provas": sorted(provas),
    }


@router.get(
    "/{estagiario_id}/exportar",
    summary="Exporta o relatório mensal em PDF ou Excel (funcionalidade 9)",
)
def exportar_relatorio(
    estagiario_id: int,
    mes: int,
    ano: int,
    formato: Literal["pdf", "excel"] = Query(
        ..., description="Formato do arquivo: pdf ou excel"
    ),
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> Response:
    """Reaproveita obter_relatorio (mesma função, chamada direto - nao via
    HTTP) pra nao duplicar a lógica de faltas/evolução, e só formata o
    resultado dela em PDF ou Excel via servicos/exportar_relatorio.py.

    Sem response_model de proposito, igual a rota de PDF de solicitacoes:
    o retorno aqui e o arquivo bruto, nao um schema Pydantic.
    """
    dados_mes = obter_relatorio(estagiario_id, mes, ano, usuario, session)

    if formato == "pdf":
        conteudo = gerar_relatorio_pdf(dados_mes)
        media_type = "application/pdf"
        extensao = "pdf"
    else:
        conteudo = gerar_relatorio_excel(dados_mes)
        media_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        extensao = "xlsx"

    nome_arquivo = f"relatorio_{estagiario_id}_{mes:02d}_{ano}.{extensao}"
    return Response(
        content=conteudo,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
