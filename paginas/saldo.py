"""Tela do saldo acumulado (Streamlit).

Modulo dono: Gustavo Legieri (Desenvolvedor 2 - secao 3.2).

Cliente HTTP puro: chama GET /saldo/{id} e mostra o resultado com st.metric().
Se a API sinalizar alerta (saldo <= -5h), destaca na tela.
"""

import os

import requests
import streamlit as st

API_URL = os.getenv("INTERNHUB_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SEGUNDOS = 5

MSG_API_FORA = (
    f"Nao consegui falar com a API em {API_URL}.\n\n"
    "Abra outro terminal, na pasta do projeto, e rode:\n\n"
    "`uvicorn api.app_api:app --reload`"
)


def _buscar_saldo(estagiario_id: int):
    """GET /saldo/{id}. Devolve (dados, erro)."""
    try:
        resposta = requests.get(
            f"{API_URL}/saldo/{estagiario_id}", timeout=TIMEOUT_SEGUNDOS
        )
    except requests.exceptions.ConnectionError:
        return None, MSG_API_FORA
    except requests.exceptions.RequestException as erro:
        return None, f"Falha ao consultar a API: {erro}"

    if resposta.status_code == 200:
        return resposta.json(), None
    if resposta.status_code == 404:
        return None, "Estagiario nao encontrado."
    return None, f"A API respondeu {resposta.status_code}: {resposta.text}"


def mostrar(estagiario_id: int) -> None:
    """Renderiza o saldo do banco de horas do estagiario selecionado."""
    st.header("Saldo (banco de horas)")

    dados, erro = _buscar_saldo(estagiario_id)
    if erro:
        st.error(erro)
        return

    saldo = dados["saldo_acumulado"]
    # O sinal ja vem no numero; o delta colore de verde (credito) ou vermelho
    # (devendo) automaticamente no st.metric.
    st.metric(
        label="Saldo acumulado",
        value=f"{saldo:+.2f} h",
        delta=f"{saldo:+.2f} h em relacao a meta",
    )
    st.caption(f"Baseado em {dados['dias_registrados']} dia(s) completo(s) registrado(s).")

    if dados["em_alerta"]:
        st.error(
            f"Alerta: seu saldo atingiu o limite de {dados['limite_alerta']:.0f} h. "
            "Vale conversar com o gestor para compensar as horas."
        )
    elif saldo < 0:
        st.warning("Voce esta devendo horas, mas ainda dentro do limite.")
    else:
        st.success("Voce esta com credito de horas. Bom trabalho!")
