"""Tela de chat com o assistente de IA (funcionalidade 11 do README).

Modulo dono: Arthur Linhares (Desenvolvedor 5 - secao 3.5).

Cliente HTTP puro, como todas as paginas/ (README, secao 7): fala com a
API so via paginas/cliente_api.py, nunca importa modelos/ nem servicos/.
"""

import streamlit as st

from paginas import cliente_api

_CHAVE_HISTORICO = "historico_assistente"


def mostrar(estagiario_id: int) -> None:
    """Chat do assistente. Mesmo contrato das demais telas (README, secao 7):
    uma funcao mostrar(estagiario_id) chamada pelo menu de app.py.
    """
    st.subheader("Assistente de IA")
    st.caption(
        "Pergunte sobre o seu saldo de horas ou peça uma simulação "
        '(ex: "e se eu faltar 2 dias?"). As respostas usam só os seus '
        "dados reais - a IA não inventa número."
    )

    historico = _historico_de(estagiario_id)

    if historico and st.button("Limpar conversa"):
        historico.clear()
        st.rerun()

    for mensagem in historico:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta = st.chat_input("Digite sua pergunta...")
    if not pergunta:
        return

    historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando seus dados..."):
            payload = {"estagiario_id": estagiario_id, "pergunta": pergunta}
            resultado, erro = cliente_api.post("/assistente/perguntar", payload)

        if erro:
            st.error(erro)
            return  # nao registra no historico: nao houve resposta de verdade

        texto_resposta = resultado["resposta"]
        st.markdown(texto_resposta)

    historico.append({"role": "assistant", "content": texto_resposta})


def _historico_de(estagiario_id: int) -> list[dict]:
    """Um histórico por estagiário, pra não misturar conversa de pessoas
    diferentes quando alguém troca de seleção no seletor do app.py.
    """
    todos = st.session_state.setdefault(_CHAVE_HISTORICO, {})
    return todos.setdefault(estagiario_id, [])
