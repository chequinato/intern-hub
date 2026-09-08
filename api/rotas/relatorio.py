from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
import calendar

from banco.conexao import get_session
from modelos.registro_ponto import RegistroPonto
from api.schemas import RelatorioMensalResponse
from servicos.saldo import calcular_saldo_acumulado
from servicos.vencimento import verificar_vencimento
from servicos.calculo import calcular_horas_trabalhadas
from servicos.feriados import eh_dia_util

router = APIRouter(prefix="/relatorio", tags=["Relatório"])

@router.get("/{estagiario_id}", response_model=RelatorioMensalResponse)
def obter_relatorio(estagiario_id: int, mes: int, ano: int, session: Session = Depends(get_session)):
    # 1. Busca todos os registros do mês
    registros_mes = session.query(RegistroPonto).filter(
        RegistroPonto.estagiario_id == estagiario_id,
        extract('month', RegistroPonto.data) == mes,
        extract('year', RegistroPonto.data) == ano
    ).order_by(RegistroPonto.data).all()
    
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
            "saldo_do_dia": horas_dia - 6.0 # Assumindo 6h de meta diária padrão
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
        "total_horas_trabalhadas": total_horas,
        "dias_uteis_trabalhados": len(registros_mes),
        "faltas": faltas, # Faltas calculadas perfeitamente!
        "saldo_acumulado": saldo_atual,
        "aviso_vencimento": aviso,
        "evolucao_diaria": evolucao
    }