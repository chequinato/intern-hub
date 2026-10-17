"""Agenda do estagiario e a regra do dia de prova.

Modulo dono: Miguel (Entrega 3).

A regra (Lei 11.788/2008, art. 10, paragrafo 2o): nos periodos de
avaliacao, a carga horaria do estagio cai pelo menos pela metade. No
sistema, um compromisso do tipo "prova" faz a META daquele dia valer a
metade - quem tem meta de 6h precisa cumprir 3h, e o saldo do dia e
calculado em cima das 3h. O limite legal diario cai na mesma proporcao.

Onde a regra e aplicada (todos chamam as funcoes daqui):
    servicos/saldo.py      - saldo acumulado e tendencia (no SQL)
    api/rotas/relatorio.py - saldo de cada dia do mes
    api/rotas/registros.py - aviso de limite legal do dia
    servicos/vencimento.py - credito antigo
    servicos/painel.py     - meta de hoje no painel

A integracao com o Google Agenda nao usa a API do Google (que exigiria
login com conta Google e chave de projeto - o professor nao conseguiria
testar). Usamos os dois caminhos abertos que o proprio Google aceita:
    - gerar_ics(): arquivo .ics (padrao iCalendar, RFC 5545), que Google
      Agenda, Outlook e o calendario do celular importam;
    - o link "adicionar ao Google Agenda" de cada compromisso, montado no
      frontend com o endereco publico calendar.google.com/calendar/render.

Recursos do SQLAlchemy usados aqui: select() como subconsulta (usada dentro
de um IN no calculo do saldo), query().filter(), order_by().
"""

from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from modelos import Compromisso
from modelos.compromisso import TIPO_PROVA

# Fator da meta em dia de prova: a lei diz "pelo menos a metade".
FATOR_META_DIA_DE_PROVA = 0.5


def subconsulta_dias_de_prova(estagiario_id: int):
    """SELECT das datas de prova do estagiario, para usar dentro de um IN.

    Fica como subconsulta (e nao como lista Python) para o saldo continuar
    sendo somado inteiro no banco: RegistroPonto.data.in_(esta_consulta).
    """
    return select(Compromisso.data).where(
        Compromisso.estagiario_id == estagiario_id,
        Compromisso.tipo == TIPO_PROVA,
    )


def datas_de_prova(
    estagiario_id: int,
    session: Session,
    inicio: date | None = None,
    fim: date | None = None,
) -> set[date]:
    """As datas de prova como conjunto, para as contas feitas em Python."""
    consulta = session.query(Compromisso.data).filter(
        Compromisso.estagiario_id == estagiario_id,
        Compromisso.tipo == TIPO_PROVA,
    )
    if inicio is not None:
        consulta = consulta.filter(Compromisso.data >= inicio)
    if fim is not None:
        consulta = consulta.filter(Compromisso.data <= fim)
    return {linha.data for linha in consulta.all()}


def meta_do_dia(meta_diaria: float, data: date, dias_de_prova: set[date]) -> float:
    """A meta daquele dia: a metade em dia de prova, a meta cheia nos outros."""
    if data in dias_de_prova:
        return meta_diaria * FATOR_META_DIA_DE_PROVA
    return meta_diaria


def listar_compromissos(
    estagiario_id: int,
    session: Session,
    inicio: date | None = None,
    fim: date | None = None,
) -> list[Compromisso]:
    """A agenda em ordem de data e hora (sem hora vem primeiro no dia)."""
    consulta = session.query(Compromisso).filter(Compromisso.estagiario_id == estagiario_id)
    if inicio is not None:
        consulta = consulta.filter(Compromisso.data >= inicio)
    if fim is not None:
        consulta = consulta.filter(Compromisso.data <= fim)
    return consulta.order_by(Compromisso.data, Compromisso.inicio).all()


# --- Exportacao .ics ----------------------------------------------------------


def _escapar(texto: str) -> str:
    """Escapa o que o formato iCalendar trata como especial."""
    return (
        texto.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _data_hora(dia: date, hora: time) -> str:
    return datetime.combine(dia, hora).strftime("%Y%m%dT%H%M%S")


def gerar_ics(compromissos: list[Compromisso], nome_estagiario: str) -> str:
    """Monta o arquivo .ics com os compromissos (um VEVENT por compromisso).

    Compromisso sem horario vira evento de dia inteiro (DTSTART;VALUE=DATE).
    O UID fixo por compromisso faz o Google Agenda atualizar o evento, em
    vez de duplicar, quando a pessoa importa o arquivo de novo.
    """
    agora = datetime.now().strftime("%Y%m%dT%H%M%S")
    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//InternHub//Agenda do estagio//PT-BR",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_escapar('InternHub - ' + nome_estagiario)}",
    ]
    for c in compromissos:
        linhas += [
            "BEGIN:VEVENT",
            f"UID:internhub-compromisso-{c.id}@internhub",
            f"DTSTAMP:{agora}",
        ]
        if c.inicio is None:
            linhas.append(f"DTSTART;VALUE=DATE:{c.data.strftime('%Y%m%d')}")
        else:
            linhas.append(f"DTSTART:{_data_hora(c.data, c.inicio)}")
            fim = c.fim or c.inicio
            linhas.append(f"DTEND:{_data_hora(c.data, fim)}")
        resumo = f"[Prova] {c.titulo}" if c.tipo == TIPO_PROVA else c.titulo
        linhas.append(f"SUMMARY:{_escapar(resumo)}")
        if c.local:
            linhas.append(f"LOCATION:{_escapar(c.local)}")
        if c.observacao:
            linhas.append(f"DESCRIPTION:{_escapar(c.observacao)}")
        linhas.append("END:VEVENT")
    linhas.append("END:VCALENDAR")
    # O padrao pede quebra de linha CRLF.
    return "\r\n".join(linhas) + "\r\n"
