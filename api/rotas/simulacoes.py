from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from banco.conexao import get_session
from api.schemas import SimulacaoRequest, SimulacaoResponse
from servicos.simulador import simular_cenario

router = APIRouter(prefix="/simulacoes", tags=["Simulação"])

@router.post("/", response_model=SimulacaoResponse)
def simular(req: SimulacaoRequest, session: Session = Depends(get_session)):
    resultado = simular_cenario(req.estagiario_id, req.dias_falta, req.horas_atraso, session)
    return resultado