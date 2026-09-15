"""Tela do simulador "e se eu faltar / chegar atrasado" (Streamlit).

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Cliente HTTP puro: monta o cenario, chama POST /simulacoes e mostra a
projecao. Nada e gravado - a rota so le o banco.
"""

import streamlit as st

from paginas import cliente_api


def mostrar(estagiario_id: int) -> None:
    """Renderiza o simulador para o estagiario selecionado."""
    st.header("Simulador de cenários")
    st.write(
        "Veja como faltas ou atrasos impactam seu banco de horas atual, "
        "sem alterar nada no sistema."
    )

    coluna_a, coluna_b = st.columns(2)
    dias_falta = coluna_a.number_input(
        "Dias de falta inteiros", min_value=0, value=0, step=1
    )
    horas_atraso = coluna_b.number_input(
        "Horas de atraso/saída antecipada", min_value=0.0, value=0.0, step=0.5
    )

    if not st.button("Simular cenário"):
        return

    payload = {
        "estagiario_id": estagiario_id,
        "dias_falta": dias_falta,
        "horas_atraso": horas_atraso,
    }
    dados, erro = cliente_api.post("/simulacoes", payload)
    if erro:
        st.error(erro)
        return

    st.divider()
    st.subheader("Resultado da projeção")

    coluna_a, coluna_b, coluna_c = st.columns(3)
    coluna_a.metric("Saldo atual", f"{dados['saldo_atual']:+.2f} h")
    coluna_b.metric("Impacto do cenário", f"{dados['impacto_horas']:+.2f} h")
    coluna_c.metric(
        "Saldo projetado",
        f"{dados['saldo_projetado']:+.2f} h",
        delta=f"{dados['impacto_horas']:+.2f} h",
    )

    if dados["saldo_projetado"] < 0:
        st.warning("Nesse cenário você ficaria devendo horas.")
    else:
        st.success("Mesmo nesse cenário você continuaria com crédito de horas.")
