"""Bater o ponto na hora - um clique por marcacao.

Modulo dono: Miguel (Entrega 3).

O modelo RegistroPonto ja nasceu pensado para isto (ver o comentario em
modelos/registro_ponto.py): a entrada e obrigatoria e os outros horarios
"vao sendo preenchidos ao longo do dia". Ate a Entrega 2, porem, so dava
para lancar o dia inteiro de uma vez, no fim do expediente. Aqui o
estagiario marca cada momento quando ele acontece:

    1a marcacao do dia -> cria o registro com a entrada
    depois             -> saida_almoco, retorno_almoco e saida, nessa ordem

Regras:
- So preenche horario VAZIO. Corrigir um horario ja marcado continua sendo
  pedido de ajuste com aprovacao do gestor (servicos/solicitacao.py).
- Dia com saida marcada esta fechado: nao aceita mais marcacao.
- Da para pular o almoco e marcar a saida direto; o dia fecha como
  pendencia, igual a rota de registro completo faria.
- Toda marcacao passa por validar_ordem_dos_horarios (servicos/calculo.py),
  a mesma regra que barra um registro torto na rota de registro.
"""

from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from modelos import Estagiario, RegistroPonto
from servicos.calculo import validar_ordem_dos_horarios

# Ordem natural das marcacoes depois da entrada.
ORDEM_DAS_MARCACOES = ("saida_almoco", "retorno_almoco", "saida")


class ErroDePonto(Exception):
    """Marcacao impossivel (dia fechado, horario fora de ordem). Vira 409."""


def proxima_marcacao(registro: RegistroPonto | None) -> str | None:
    """Qual horario o proximo clique vai preencher (None = dia fechado)."""
    if registro is None:
        return "entrada"
    if registro.saida is not None:
        return None
    for campo in ORDEM_DAS_MARCACOES:
        if getattr(registro, campo) is None:
            return campo
    return None


def bater_ponto(
    estagiario_id: int,
    agora: datetime,
    session: Session,
    marcacao: str | None = None,
) -> tuple[RegistroPonto, str]:
    """Marca o horario `agora` no registro do dia e devolve (registro, campo).

    `marcacao` e opcional: sem ela, vale a proxima da ordem. Com ela, da
    para escolher - o caso de uso e "nao tirei almoco hoje, quero marcar a
    saida direto".
    """
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise LookupError(f"Estagiario {estagiario_id} nao encontrado.")

    hoje = agora.date()
    # Segundos zerados: o ponto e registrado em minutos, igual ao formulario.
    horario = agora.time().replace(second=0, microsecond=0)

    registro = (
        session.query(RegistroPonto)
        .filter_by(estagiario_id=estagiario_id, data=hoje)
        .first()
    )

    if registro is None:
        if marcacao not in (None, "entrada"):
            raise ErroDePonto("O primeiro ponto do dia precisa ser a entrada.")
        registro = RegistroPonto(estagiario_id=estagiario_id, data=hoje, entrada=horario)
        session.add(registro)
        _salvar(session)
        session.refresh(registro)
        return registro, "entrada"

    if registro.saida is not None:
        raise ErroDePonto(
            "O dia de hoje ja foi encerrado. Para corrigir algum horario, "
            "abra uma solicitacao de ajuste."
        )

    campo = marcacao or proxima_marcacao(registro)
    if campo not in ORDEM_DAS_MARCACOES:
        raise ErroDePonto(f"Marcacao invalida: {campo}.")
    if getattr(registro, campo) is not None:
        raise ErroDePonto(
            "Esse horario ja foi marcado hoje. Para corrigir, abra uma "
            "solicitacao de ajuste."
        )

    horarios = {
        "entrada": registro.entrada,
        "saida": registro.saida,
        "saida_almoco": registro.saida_almoco,
        "retorno_almoco": registro.retorno_almoco,
    }
    horarios[campo] = horario
    problema = validar_ordem_dos_horarios(**horarios)
    if problema is not None:
        raise ErroDePonto(f"Nao foi possivel marcar agora: {problema}.")

    setattr(registro, campo, horario)
    _salvar(session)
    session.refresh(registro)
    return registro, campo


def _salvar(session: Session) -> None:
    """commit() com rollback() no erro - mesmo padrao de servicos/solicitacao.py."""
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
