"""Tela de auditoria: o historico completo dos pedidos de ajuste.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).

Funcionalidade 17 do README. Nao existe tabela de auditoria: a propria
SolicitacaoAjuste ja guarda quem pediu, quando, quem respondeu e quando - a
tela so precisa ler tudo isso com GET /solicitacoes e mostrar em tabela.

A mesma tela serve aos dois perfis. O gestor ve o historico inteiro; o
estagiario ve so os proprios pedidos, porque a chamada vai com o filtro
estagiario_id.
"""

import streamlit as st

from paginas import cliente_api
from paginas.solicitacoes import (
    ROTULOS_DOS_CAMPOS,
    formatar_data,
    formatar_data_hora,
    formatar_hora,
)

STATUS_POSSIVEIS = ["pendente", "aprovado", "rejeitado"]


def mostrar(estagiario_id: int | None = None) -> None:
    """Renderiza o historico.

    Com estagiario_id, mostra so os pedidos daquela pessoa (visao do
    estagiario). Sem ele, mostra o historico de todo mundo (visao do gestor).
    """
    st.header("Auditoria")

    if estagiario_id is None:
        st.caption("Histórico de todos os pedidos de ajuste do sistema.")
    else:
        st.caption("Histórico dos seus pedidos de ajuste.")

    filtro_status = st.selectbox(
        "Filtrar por situação", options=["todos", *STATUS_POSSIVEIS]
    )

    parametros = {}
    if estagiario_id is not None:
        parametros["estagiario_id"] = estagiario_id
    if filtro_status != "todos":
        parametros["status"] = filtro_status

    solicitacoes, erro = cliente_api.get("/solicitacoes", parametros)
    if erro:
        st.error(erro)
        return

    if not solicitacoes:
        st.info("Nenhum pedido encontrado com esse filtro.")
        return

    # st.dataframe espera uma lista de dicionarios com as mesmas chaves - e
    # sao essas chaves que viram os titulos das colunas na tela.
    linhas = [
        {
            "#": solicitacao["id"],
            "Estagiário": solicitacao["estagiario_nome"],
            "Dia do ponto": formatar_data(solicitacao["data_registro"]),
            "Campo": ROTULOS_DOS_CAMPOS.get(
                solicitacao["campo_alterado"], solicitacao["campo_alterado"]
            ),
            "Sugerido": formatar_hora(solicitacao["horario_sugerido"]),
            "Justificativa": solicitacao["justificativa"],
            "Situação": solicitacao["status"],
            "Pedido em": formatar_data_hora(solicitacao["data_solicitacao"]),
            "Respondido em": formatar_data_hora(solicitacao["data_resposta"]),
            "Gestor": solicitacao["gestor_nome"] or "—",
        }
        for solicitacao in solicitacoes
    ]

    st.dataframe(linhas, use_container_width=True, hide_index=True)

    total = len(solicitacoes)
    aprovados = len([s for s in solicitacoes if s["status"] == "aprovado"])
    rejeitados = len([s for s in solicitacoes if s["status"] == "rejeitado"])
    coluna_a, coluna_b, coluna_c = st.columns(3)
    coluna_a.metric("Pedidos no filtro", total)
    coluna_b.metric("Aprovados", aprovados)
    coluna_c.metric("Rejeitados", rejeitados)
