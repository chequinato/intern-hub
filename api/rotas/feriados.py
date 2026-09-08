from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from banco.conexao import get_session
from modelos.feriado import Feriado
from api.schemas import FeriadoCreate, FeriadoResponse

router = APIRouter(prefix="/feriados", tags=["Feriados"])

@router.post("/", response_model=FeriadoResponse)
def cadastrar_feriado(feriado: FeriadoCreate, session: Session = Depends(get_session)):
    novo_feriado = Feriado(data=feriado.data, descricao=feriado.descricao)
    session.add(novo_feriado)
    session.commit()
    session.refresh(novo_feriado)
    return novo_feriado

@router.get("/", response_model=List[FeriadoResponse])
def listar_feriados(session: Session = Depends(get_session)):
    return session.query(Feriado).order_by(Feriado.data).all()