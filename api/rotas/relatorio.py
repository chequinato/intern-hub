from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
from typing import Literal
import calendar

from banco.conexao import get_session
from modelos.configuracao import META_HORAS_DIARIA_PADRAO, Configuracao
from modelos.registro_ponto import RegistroPonto
from api.schemas import RelatorioMensalResponse
from servicos.saldo import calcular_saldo_acumulado
from servicos.vencimento import verificar_vencimento
from servicos.calculo import calcular_horas_trabalhadas
from servicos.feriados import eh_dia_util
from servicos.exportar_relatorio import gerar_relatorio_excel, gerar_relatorio_pdf

router = APIRouter(prefix="/relatorio", tags=["Relatório"])

@router.get("/{estagiario_id}", response_model=RelatorioMensalResponse)
def obter_relatorio(estagiario_id: int, mes: int, ano: int, session: Session = Depends(get_session)):
    # 1. Busca todos os registros do mês
    registros_mes = session.query(RegistroPonto).filter(
        RegistroPonto.estagiario_id == estagiario_id,
        extract('month', RegistroPonto.data) == mes,
        extract('year', RegistroPonto.data) == ano
    ).order_by(RegistroPonto.data).all()
    
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

    total_horas = 0.0
    evolucao = []
    
    # Cria um conjunto (set) apenas com os dias que o estagiário bateu ponto para busca rápida
    dias_trabalhados = {reg.data.day for reg in registros_mes}
    
    # 2. Processa as horas trabalhadas
    for reg in registros_mes:
        horas_dia = calcular_horas_trabalhadas(reg.entrada, reg.saida, reg.saida_almoco, reg.retorno_almoco)
        total_horas += horas_dia
        evolucao.append({
            "data": reg.data,
            "horas_trabalhadas": horas_dia,
            "saldo_do_dia": round(horas_dia - meta_diaria, 2)
        })
        
    # 3. LÓGICA DE FALTAS (O coração do seu requisito!)
    faltas = 0
    hoje = date.today()
    ultimo_dia_mes = calendar.monthrange(ano, mes)[1]
    
    # Se estiver olhando o mês atual, não conta falta de dias do futuro. Para meses passados, olha até o dia 30/31.
    dia_limite = hoje.day if (ano == hoje.year and mes == hoje.month) else ultimo_dia_mes
    
    for dia in range(1, dia_limite + 1):
        data_atual = date(ano, mes, dia)
        
        # A Mágica: Se é dia útil (sem fim de semana e sem feriado) E a pessoa não bateu ponto...
        if eh_dia_util(data_atual, session) and dia not in dias_trabalhados:
            faltas += 1

    # 4. Busca avisos e saldo final
    saldo_atual = calcular_saldo_acumulado(estagiario_id, session)
    aviso = verificar_vencimento(estagiario_id, session)
    
    return {
        "mes": mes,
        "ano": ano,
        "total_horas_trabalhadas": round(total_horas, 2),
        "dias_uteis_trabalhados": len(registros_mes),
        "faltas": faltas, # Faltas calculadas perfeitamente!
        "saldo_acumulado": saldo_atual,
        "aviso_vencimento": aviso,
        "evolucao_diaria": evolucao
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
    session: Session = Depends(get_session),
) -> Response:
    """Reaproveita obter_relatorio (mesma função, chamada direto - nao via
    HTTP) pra nao duplicar a lógica de faltas/evolução, e só formata o
    resultado dela em PDF ou Excel via servicos/exportar_relatorio.py.

    Sem response_model de proposito, igual a rota de PDF de solicitacoes:
    o retorno aqui e o arquivo bruto, nao um schema Pydantic.
    """
    dados_mes = obter_relatorio(estagiario_id, mes, ano, session)

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
