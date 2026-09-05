"""Tela de registro de ponto (Streamlit).

Modulo dono: Gustavo Legieri (Desenvolvedor 2 - secao 3.2).

Cliente HTTP puro: monta o payload a partir do formulario e chama
POST /registros. Trata os status code que a rota pode devolver (201 sucesso,
201 com pendencia, 409 dia repetido, 422 validacao, API fora do ar).
"""

import os
from datetime import date, time

import requests
import streamlit as st

API_URL = os.getenv("INTERNHUB_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SEGUNDOS = 5

MSG_API_FORA = (
    f"Nao consegui falar com a API em {API_URL}.\n\n"
    "Abra outro terminal, na pasta do projeto, e rode:\n\n"
    "`uvicorn api.app_api:app --reload`"
)


def _hora_ou_none(marcado: bool, valor: time):
    """Devolve o horario em 'HH:MM' so quando o usuario marcou o campo.

    O almoco e opcional na tela: se a pessoa nao marcou, mandamos None e o
    dia vira pendencia do lado da API.
    """
    return valor.strftime("%H:%M") if marcado else None


def _enviar_registro(payload: dict):
    """POST /registros. Devolve (dados, erro, status_code)."""
    try:
        resposta = requests.post(
            f"{API_URL}/registros", json=payload, timeout=TIMEOUT_SEGUNDOS
        )
    except requests.exceptions.ConnectionError:
        return None, MSG_API_FORA, None
    except requests.exceptions.RequestException as erro:
        return None, f"Falha ao falar com a API: {erro}", None

    if resposta.status_code == 201:
        return resposta.json(), None, 201
    if resposta.status_code == 409:
        return None, "Ja existe um registro para essa data.", 409
    if resposta.status_code == 422:
        return None, "Horarios invalidos. Confira a ordem de entrada/saida.", 422
    return None, f"A API respondeu {resposta.status_code}: {resposta.text}", resposta.status_code


def mostrar(estagiario_id: int) -> None:
    """Renderiza a tela de registro para o estagiario selecionado."""
    st.header("Registrar ponto")
    st.caption("Marque o almoco so quando tiver saido e voltado. Se faltar, o dia entra como pendencia.")

    with st.form("form_registro"):
        dia = st.date_input("Data", value=date.today())

        coluna_a, coluna_b = st.columns(2)
        entrada = coluna_a.time_input("Entrada", value=time(8, 0))
        saida = coluna_b.time_input("Saida", value=time(17, 0))

        marcou_almoco = st.checkbox("Registrei a saida e o retorno do almoco", value=True)
        coluna_c, coluna_d = st.columns(2)
        saida_almoco = coluna_c.time_input("Saida para o almoco", value=time(12, 0))
        retorno_almoco = coluna_d.time_input("Retorno do almoco", value=time(13, 0))

        enviou = st.form_submit_button("Salvar registro")

    if not enviou:
        return

    payload = {
        "estagiario_id": estagiario_id,
        "data": dia.isoformat(),
        "entrada": entrada.strftime("%H:%M"),
        "saida": saida.strftime("%H:%M"),
        "saida_almoco": _hora_ou_none(marcou_almoco, saida_almoco),
        "retorno_almoco": _hora_ou_none(marcou_almoco, retorno_almoco),
    }

    dados, erro, _ = _enviar_registro(payload)
    if erro:
        st.error(erro)
        return

    horas = dados["horas_trabalhadas"]
    if dados["pendencia"]:
        st.warning(dados.get("aviso") or "Registro salvo com pendencia de almoco.")
    else:
        st.success(f"Registro salvo! Horas trabalhadas no dia: {horas:.2f} h.")
        st.info("Veja o impacto no seu banco de horas na tela **Ver saldo**.")
