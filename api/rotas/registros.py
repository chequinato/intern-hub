"""Rotas de /registros - registro de ponto e historico.

Modulo dono: Gustavo Legieri (Desenvolvedor 2 - secao 3.2).

Segue o molde da fundacao (api/rotas/estagiarios.py): APIRouter com prefix,
sessao via Depends(get_session), schema Pydantic na entrada, commit dentro de
try com rollback no except, e status code explicito.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.schemas import RegistroCreate, RegistroResponse
from banco.conexao import get_session
from modelos import Estagiario, RegistroPonto
from servicos.calculo import calcular_horas_trabalhadas, verificar_pendencia_almoco

router = APIRouter(prefix="/registros", tags=["Registros"])

AVISO_PENDENCIA = (
    "Registro salvo com pendencia: faltou marcar a saida ou o retorno do "
    "almoco. Abra uma solicitacao de ajuste para corrigir."
)


def _montar_resposta(registro: RegistroPonto) -> RegistroResponse:
    """Converte um RegistroPonto do banco em RegistroResponse.

    Aqui e onde o calculo do dia (servicos/calculo.py) se junta aos dados
    crus do banco: horas trabalhadas e a marca de pendencia.
    """
    pendencia = verificar_pendencia_almoco(registro)
    horas = calcular_horas_trabalhadas(
        registro.entrada,
        registro.saida,
        registro.saida_almoco,
        registro.retorno_almoco,
    )
    return RegistroResponse(
        id=registro.id,
        estagiario_id=registro.estagiario_id,
        data=registro.data,
        entrada=registro.entrada,
        saida=registro.saida,
        saida_almoco=registro.saida_almoco,
        retorno_almoco=registro.retorno_almoco,
        horas_trabalhadas=horas,
        pendencia=pendencia,
        aviso=AVISO_PENDENCIA if pendencia else None,
    )


@router.post(
    "",
    response_model=RegistroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra o ponto de um dia",
)
def criar_registro(
    dados: RegistroCreate, session: Session = Depends(get_session)
) -> RegistroResponse:
    """Salva o ponto do dia e devolve o registro ja com horas e pendencia.

    Um dia com almoco incompleto NAO e recusado: ele e salvo e volta com
    pendencia=True e um aviso, como manda o README (secao 7).
    """
    estagiario = (
        session.query(Estagiario).filter_by(id=dados.estagiario_id).first()
    )
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {dados.estagiario_id} nao encontrado.",
        )

    ja_existe = (
        session.query(RegistroPonto)
        .filter_by(estagiario_id=dados.estagiario_id, data=dados.data)
        .first()
    )
    if ja_existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ja existe um registro para {dados.data.isoformat()}.",
        )

    registro = RegistroPonto(
        estagiario_id=dados.estagiario_id,
        data=dados.data,
        entrada=dados.entrada,
        saida=dados.saida,
        saida_almoco=dados.saida_almoco,
        retorno_almoco=dados.retorno_almoco,
    )

    session.add(registro)
    try:
        session.commit()
    except SQLAlchemyError as erro:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o registro.",
        ) from erro

    session.refresh(registro)
    return _montar_resposta(registro)


@router.get(
    "/{estagiario_id}",
    response_model=list[RegistroResponse],
    summary="Lista o historico de registros de um estagiario",
)
def listar_registros(
    estagiario_id: int,
    session: Session = Depends(get_session),
    inicio: date | None = Query(
        default=None, description="Filtra registros a partir desta data (inclusive)."
    ),
    fim: date | None = Query(
        default=None, description="Filtra registros ate esta data (inclusive)."
    ),
) -> list[RegistroResponse]:
    """Historico em ordem cronologica, com filtro opcional por periodo."""
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estagiario {estagiario_id} nao encontrado.",
        )

    consulta = session.query(RegistroPonto).filter_by(estagiario_id=estagiario_id)
    if inicio is not None:
        consulta = consulta.filter(RegistroPonto.data >= inicio)
    if fim is not None:
        consulta = consulta.filter(RegistroPonto.data <= fim)

    registros = consulta.order_by(RegistroPonto.data).all()
    return [_montar_resposta(registro) for registro in registros]
