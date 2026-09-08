import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime

def renderizar():
    st.title("Relatório Mensal")

    estagiario_id = st.session_state.get("estagiario_id")
    if not estagiario_id:
        st.warning("Selecione um estagiário no menu principal primeiro.")
        return

    hoje = datetime.now()
    col1, col2 = st.columns(2)
    with col1:
        mes = st.selectbox("Mês", range(1, 13), index=hoje.month - 1)
    with col2:
        ano = st.selectbox("Ano", range(2023, 2030), index=hoje.year - 2023)

    if st.button("Gerar Relatório"):
        # 1. Busca os dados do mês atual selecionado
        resposta = requests.get(f"http://localhost:8000/relatorio/{estagiario_id}?mes={mes}&ano={ano}")
        
        if resposta.status_code == 200:
            dados = resposta.json()
            
            if dados.get("aviso_vencimento"):
                st.warning(dados["aviso_vencimento"])
                
            # Métricas em formato de cartões
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Horas no Mês", f"{dados['total_horas_trabalhadas']}h")
            col2.metric("Dias Úteis", dados['dias_uteis_trabalhados'])
            col3.metric("Faltas", dados['faltas'])
            col4.metric("Saldo Acumulado", f"{dados['saldo_acumulado']}h")
            
            st.divider()

            # 2. GRÁFICO 1: Evolução do Mês (Diário)
            st.subheader("Evolução do Mês")
            if dados['evolucao_diaria']:
                datas = [d['data'] for d in dados['evolucao_diaria']]
                horas = [d['horas_trabalhadas'] for d in dados['evolucao_diaria']]
                
                fig1, ax1 = plt.subplots(figsize=(10, 4))
                ax1.plot(datas, horas, marker='o', linestyle='-', color='#1f77b4')
                ax1.axhline(y=6, color='r', linestyle='--', label='Meta (ex: 6h)')
                ax1.set_title(f"Horas Trabalhadas (Mês {mes}/{ano})")
                ax1.set_xlabel("Data")
                ax1.set_ylabel("Horas")
                ax1.legend()
                plt.xticks(rotation=45)
                
                st.pyplot(fig1)
            else:
                st.info("Nenhum registro de ponto encontrado para este mês.")

            st.divider()

            # 3. GRÁFICO 2: Tendência do Semestre
            st.subheader("Tendência do Semestre")
            
            meses_labels = []
            horas_semestre = []
            
            # Laço para calcular os últimos 5 meses + o mês atual
            for i in range(5, -1, -1):
                mes_alvo = mes - i
                ano_alvo = ano
                if mes_alvo <= 0:
                    mes_alvo += 12
                    ano_alvo -= 1
                    
                meses_labels.append(f"{mes_alvo:02d}/{ano_alvo}")
                
                # Faz a requisição para cada mês passado
                resp_semestre = requests.get(f"http://localhost:8000/relatorio/{estagiario_id}?mes={mes_alvo}&ano={ano_alvo}")
                if resp_semestre.status_code == 200:
                    dados_semestre = resp_semestre.json()
                    horas_semestre.append(dados_semestre['total_horas_trabalhadas'])
                else:
                    horas_semestre.append(0) # Zera se der erro ou não achar

            fig2, ax2 = plt.subplots(figsize=(10, 4))
            # Gráfico de barras para a tendência mensal
            ax2.bar(meses_labels, horas_semestre, color='#2ca02c')
            ax2.set_title("Total de Horas Trabalhadas (Últimos 6 Meses)")
            ax2.set_xlabel("Mês/Ano")
            ax2.set_ylabel("Total de Horas")
            
            st.pyplot(fig2)

        else:
            st.error("Erro ao buscar dados do relatório.")