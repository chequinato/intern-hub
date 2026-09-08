from sqlalchemy.orm import Session
from datetime import date
from dateutil.relativedelta import relativedelta
from modelos.registro_ponto import RegistroPonto

def verificar_vencimento(estagiario_id: int, session: Session) -> str:
    # A regra diz que saldo expira em 2 meses (prazo_vencimento_meses)
    # Aqui verificamos se há horas acumuladas positivas muito antigas
    hoje = date.today()
    limite_data = hoje - relativedelta(months=2)
    
    registros_antigos = session.query(RegistroPonto).filter(
        RegistroPonto.estagiario_id == estagiario_id,
        RegistroPonto.data <= limite_data
    ).all()
    
    # Simplificação: se há registros antigos sem compensação clara, avisar
    if registros_antigos:
        return "Atenção: Você possui horas positivas com mais de 2 meses que estão prestes a expirar."
    
    return None