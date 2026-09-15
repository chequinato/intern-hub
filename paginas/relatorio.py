"""Tela do relatorio mensal, com grafico de evolucao e tendencia (Streamlit).

Modulo dono: Pietro Paruci (Desenvolvedor 3 - secao 3.3).

Cliente HTTP puro: chama GET /relatorio/{id}?mes=&ano= e desenha os dois
graficos com matplotlib - a evolucao diaria do mes escolhido (funcionalidade
6) e a tendencia dos ultimos seis meses (funcionalidade 19).
"""

from datetime import datetime

import matplotlib.pyplot as plt
import streamlit as st

from paginas import cliente_api


def mostrar(estagiario_id: int) -> None:
    """Renderiza o relatorio do estagiario selecionado."""
    st.header("Relatório mensal")

    hoje = datetime.now()
    coluna_a, coluna_b = st.columns(2)
    mes = coluna_a.selectbox("Mês", range(1, 13), index=hoje.month - 1)
    ano = coluna_b.selectbox("Ano", range(2023, 2030), index=hoje.year - 2023)

    if not st.button("Gerar relatório"):
        return

    dados, erro = cliente_api.get(
        f"/relatorio/{estagiario_id}", {"mes": mes, "ano": ano}
    )
    if erro:
        st.error(erro)
        return

    if dados.get("aviso_vencimento"):
        st.warning(dados["aviso_vencimento"])

    coluna_a, coluna_b, coluna_c, coluna_d = st.columns(4)
    coluna_a.metric("Horas no mês", f"{dados['total_horas_trabalhadas']:.2f} h")
    coluna_b.metric("Dias registrados", dados["dias_uteis_trabalhados"])
    coluna_c.metric("Faltas", dados["faltas"])
    coluna_d.metric("Saldo acumulado", f"{dados['saldo_acumulado']:+.2f} h")

    st.divider()
    _grafico_do_mes(dados, mes, ano)
    st.divider()
    _grafico_do_semestre(estagiario_id, mes, ano)


def _grafico_do_mes(dados: dict, mes: int, ano: int) -> None:
    """Linha com as horas de cada dia registrado no mes."""
    st.subheader("Evolução do mês")

    if not dados["evolucao_diaria"]:
        st.info("Nenhum registro de ponto encontrado para este mês.")
        return

    datas = [dia["data"] for dia in dados["evolucao_diaria"]]
    horas = [dia["horas_trabalhadas"] for dia in dados["evolucao_diaria"]]
    # A meta e a mesma para todos os dias do mes: horas - saldo do dia.
    meta = horas[0] - dados["evolucao_diaria"][0]["saldo_do_dia"]

    figura, eixo = plt.subplots(figsize=(10, 4))
    eixo.plot(datas, horas, marker="o", linestyle="-", color="#1f77b4")
    eixo.axhline(y=meta, color="r", linestyle="--", label=f"Meta ({meta:.1f}h)")
    eixo.set_title(f"Horas trabalhadas — {mes:02d}/{ano}")
    eixo.set_xlabel("Data")
    eixo.set_ylabel("Horas")
    eixo.legend()
    plt.xticks(rotation=45)

    st.pyplot(figura)


def _grafico_do_semestre(estagiario_id: int, mes: int, ano: int) -> None:
    """Barras com o total de horas de cada um dos ultimos seis meses."""
    st.subheader("Tendência do semestre")

    rotulos = []
    totais = []

    # Uma requisicao por mes: seis chamadas ao todo. E aceitavel aqui porque a
    # rota de relatorio ja entrega o total pronto - juntar tudo em uma unica
    # rota "do semestre" so valeria a pena se o volume crescesse muito.
    for passos_atras in range(5, -1, -1):
        mes_alvo = mes - passos_atras
        ano_alvo = ano
        if mes_alvo <= 0:
            mes_alvo += 12
            ano_alvo -= 1

        rotulos.append(f"{mes_alvo:02d}/{ano_alvo}")
        dados_do_mes, erro = cliente_api.get(
            f"/relatorio/{estagiario_id}", {"mes": mes_alvo, "ano": ano_alvo}
        )
        totais.append(0 if erro else dados_do_mes["total_horas_trabalhadas"])

    figura, eixo = plt.subplots(figsize=(10, 4))
    eixo.bar(rotulos, totais, color="#2ca02c")
    eixo.set_title("Total de horas trabalhadas (últimos 6 meses)")
    eixo.set_xlabel("Mês/ano")
    eixo.set_ylabel("Total de horas")

    st.pyplot(figura)
