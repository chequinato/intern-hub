import streamlit as st
import requests

def renderizar():
    st.title("Simulador de Cenários")
    st.write("Veja como faltas ou atrasos impactam seu banco de horas atual, sem alterar nada no sistema.")

    estagiario_id = st.session_state.get("estagiario_id")
    if not estagiario_id:
        st.warning("Selecione um estagiário no menu principal primeiro.")
        return

    col1, col2 = st.columns(2)
    with col1:
        dias_falta = st.number_input("Dias de falta inteiros", min_value=0, value=0, step=1)
    with col2:
        horas_atraso = st.number_input("Horas de atraso/saída antecipada", min_value=0.0, value=0.0, step=0.5)

    if st.button("Simular Cenário"):
        payload = {
            "estagiario_id": estagiario_id,
            "dias_falta": dias_falta,
            "horas_atraso": horas_atraso
        }
        
        # A porta 8000 é padrão do FastAPI
        resposta = requests.post("http://localhost:8000/simulacoes/", json=payload)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            st.divider()
            st.subheader("Resultado da Projeção")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Saldo Atual", f"{dados['saldo_atual']}h")
            c2.metric("Impacto (Horas descontadas)", f"{dados['impacto_horas']}h")
            c3.metric("Saldo Projetado", f"{dados['saldo_projetado']}h", 
                      delta=dados['impacto_horas'], delta_color="normal")
        else:
            st.error("Erro ao comunicar com a API. Verifique se o Uvicorn está rodando.")