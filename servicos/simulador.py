from sqlalchemy.orm import Session
from modelos.configuracao import Configuracao
from servicos.saldo import calcular_saldo_acumulado # Supõe que Gustavo criou isso

def simular_cenario(estagiario_id: int, dias_falta: int, horas_atraso: float, session: Session) -> dict:
    # Pega configuração global (ou vinculada ao estagiário)
    config = session.query(Configuracao).first()
    meta_diaria = config.meta_horas_diaria if config else 6.0
    
    # Busca o saldo atual do estagiário sem alterar o banco
    saldo_atual = calcular_saldo_acumulado(estagiario_id, session)
    
    # Calcula o impacto
    impacto_faltas = dias_falta * meta_diaria
    impacto_total = impacto_faltas + horas_atraso
    
    saldo_projetado = saldo_atual - impacto_total
    
    return {
        "saldo_atual": saldo_atual,
        "saldo_projetado": saldo_projetado,
        "impacto_horas": -impacto_total
    }