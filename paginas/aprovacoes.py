"""Tela do gestor: aprovar ou rejeitar os pedidos de ajuste.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).

Cliente HTTP puro (paginas/cliente_api.py):

    GET   /solicitacoes/pendentes?gestor_id=  -> a fila deste gestor
    PATCH /solicitacoes/{id}                  -> a decisao

Aprovar devolve o saldo do estagiario ja recalculado, e a tela mostra esse
numero: o gestor ve na hora o efeito do que acabou de autorizar.
"""

import streamlit as st

from paginas import cliente_api
from paginas.solicitacoes import descrever_ajuste, formatar_data, formatar_data_hora


# Chave onde o resultado da ultima decisao fica guardado entre um rerun e
# outro. Sem isso a mensagem apareceria e sumiria no mesmo instante: logo
# depois de decidir, a tela recarrega para tirar o pedido da fila.
CHAVE_DA_MENSAGEM = "resultado_da_ultima_decisao"


def mostrar(gestor_id: int) -> None:
    """Renderiza a fila de aprovacoes do gestor selecionado."""
    st.header("Aprovações")
    st.caption("Pedidos de ajuste de ponto dos estagiários sob a sua gestão.")

    _mostrar_resultado_da_ultima_decisao()

    pendentes, erro = cliente_api.get(
        "/solicitacoes/pendentes", {"gestor_id": gestor_id}
    )
    if erro:
        st.error(erro)
        return

    if not pendentes:
        st.success("Nenhum pedido pendente. Sua fila está vazia.")
        return

    st.write(f"**{len(pendentes)} pedido(s) aguardando decisão.**")

    for solicitacao in pendentes:
        _cartao_do_pedido(solicitacao, gestor_id)


def _cartao_do_pedido(solicitacao: dict, gestor_id: int) -> None:
    """Um pedido com os dois botoes de decisao."""
    with st.container(border=True):
        st.markdown(
            f"**{solicitacao['estagiario_nome']}** — dia "
            f"{formatar_data(solicitacao['data_registro'])}"
        )
        st.write(descrever_ajuste(solicitacao))
        st.caption(f"Justificativa: {solicitacao['justificativa']}")
        st.caption(f"Pedido em {formatar_data_hora(solicitacao['data_solicitacao'])}")

        coluna_a, coluna_b = st.columns(2)
        # key precisa ser unica por pedido: sem isso o Streamlit trataria
        # todos os botoes "Aprovar" da lista como se fossem o mesmo botao.
        aprovar = coluna_a.button(
            "Aprovar", key=f"aprovar_{solicitacao['id']}", type="primary"
        )
        rejeitar = coluna_b.button("Rejeitar", key=f"rejeitar_{solicitacao['id']}")

    if not aprovar and not rejeitar:
        return

    decisao = "aprovado" if aprovar else "rejeitado"
    resultado, erro = cliente_api.patch(
        f"/solicitacoes/{solicitacao['id']}",
        {"status": decisao, "gestor_id": gestor_id},
    )
    if erro:
        st.error(erro)
        return

    if decisao == "aprovado":
        saldo = resultado["saldo_acumulado"]
        texto = (
            f"{resultado['mensagem']} Saldo de {solicitacao['estagiario_nome']} "
            f"agora: {saldo:+.2f} h."
        )
    else:
        texto = resultado["mensagem"]

    # Guarda a mensagem ANTES de recarregar; quem a exibe e a proxima rodada.
    st.session_state[CHAVE_DA_MENSAGEM] = (decisao, texto)
    # Recarrega a tela para o pedido sair da fila de pendentes.
    st.rerun()


def _mostrar_resultado_da_ultima_decisao() -> None:
    """Exibe (uma vez so) a mensagem da decisao tomada antes do rerun."""
    guardado = st.session_state.pop(CHAVE_DA_MENSAGEM, None)
    if guardado is None:
        return

    decisao, texto = guardado
    if decisao == "aprovado":
        st.success(texto)
    else:
        st.info(texto)
