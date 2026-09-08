from sqlalchemy.orm import Session
from datetime import date
from modelos.feriado import Feriado

def eh_dia_util(data: date, session: Session) -> bool:
    # 0 = Segunda, 4 = Sexta, 5 = Sábado, 6 = Domingo
    if data.weekday() > 4:
        return False
    
    # Verifica se a data está cadastrada como feriado
    feriado = session.query(Feriado).filter(Feriado.data == data).first()
    if feriado:
        return False
        
    return True