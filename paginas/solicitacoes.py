"""Tela do estagiario: pedir ajuste de ponto e acompanhar os pedidos.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).

Cliente HTTP puro (paginas/cliente_api.py). O caminho da tela e:

    GET /registros/{id}  -> monta a lista de dias, ja marcando as pendencias
    POST /solicitacoes   -> abre o pedido de correcao
    GET /solicitacoes    -> mostra o que a pessoa ja pediu e como ficou

As funcoes de formatacao do topo sao importadas tambem por
paginas/aprovacoes.py e paginas/auditoria.py: as tres telas falam do mesmo
assunto e precisam escrever "de 13:00 para 14:00" do mesmo jeito.
"""

from datetime import datetime, time

import streamlit as st

from paginas import cliente_api

# Nome tecnico do campo -> como ele aparece para o usuario. Os nomes tecnicos
# sao os mesmos de CAMPOS_AJUSTAVEIS (modelos/solicitacao_ajuste.py).
ROTULOS_DOS_CAMPOS = {
    "entrada": "Entrada",
    "saida": "Saída",
    "saida_almoco": "Saída para o almoço",
    "retorno_almoco": "Retorno do almoço",
}

CORES_DO_STATUS = {
    "pendente": "🟡 pendente",
    "aprovado": "🟢 aprovado",
    "rejeitado": "🔴 rejeitado",
}


def formatar_data(texto_iso: str) -> str:
    """'2026-09-15' vira '15/09/2026'."""
    return datetime.fromisoformat(texto_iso).strftime("%d/%m/%Y")


def formatar_data_hora(texto_iso: str | None) -> str:
    """'2026-09-15T14:03:27' vira '15/09/2026 14:03'. Vazio vira travessao."""
    if not texto_iso:
        return "—"
    return datetime.fromisoformat(texto_iso).strftime("%d/%m/%Y %H:%M")


def formatar_hora(texto_iso: str | None) -> str:
    """'13:00:00' vira '13:00'. Horario nao preenchido vira 'não marcado'.

    O corte em cinco caracteres so pode acontecer DEPOIS de checar o None -
    aplicado ao texto de fallback, ele deixaria "não m" na tela.
    """
    if not texto_iso:
        return "não marcado"
    return texto_iso[:5]


def descrever_ajuste(solicitacao: dict) -> str:
    """Frase curta do tipo 'Retorno do almoço: de 13:00 para 14:00'."""
    rotulo = ROTULOS_DOS_CAMPOS.get(
        solicitacao["campo_alterado"], solicitacao["campo_alterado"]
    )
    return (
        f"{rotulo}: de {formatar_hora(solicitacao['horario_atual'])} "
        f"para {formatar_hora(solicitacao['horario_sugerido'])}"
    )


def mostrar(estagiario_id: int) -> None:
    """Renderiza a tela de solicitacoes do estagiario selecionado."""
    st.header("Solicitações de ajuste")
    st.caption(
        "Esqueceu de marcar um horário? Peça a correção aqui. "
        "Quem decide é o gestor responsável por você."
    )

    registros, erro = cliente_api.get(f"/registros/{estagiario_id}")
    if erro:
        st.error(erro)
        return

    if not registros:
        st.info("Você ainda não tem nenhum ponto registrado para corrigir.")
        return

    # Funcionalidade 13 do README: o proprio sistema puxa o assunto quando ve
    # um dia incompleto, em vez de esperar o estagiario notar sozinho.
    pendentes = [registro for registro in registros if registro["pendencia"]]
    if pendentes:
        dias = ", ".join(formatar_data(registro["data"]) for registro in pendentes)
        st.warning(
            f"Você tem {len(pendentes)} dia(s) com marcação de almoço faltando: "
            f"{dias}. Abra um pedido de ajuste para cada um."
        )

    _formulario_de_pedido(registros)
    st.divider()
    _meus_pedidos(estagiario_id)


def _formulario_de_pedido(registros: list) -> None:
    """Formulario que monta o payload de POST /solicitacoes."""
    st.subheader("Pedir uma correção")

    # Os dias mais recentes primeiro: e quase sempre um deles que precisa de
    # ajuste. A API devolve em ordem cronologica crescente.
    opcoes = list(reversed(registros))
    por_id = {registro["id"]: registro for registro in opcoes}

    with st.form("form_solicitacao"):
        registro_id = st.selectbox(
            "Dia a corrigir",
            options=[registro["id"] for registro in opcoes],
            format_func=lambda id_: (
                formatar_data(por_id[id_]["data"])
                + (" — com pendência" if por_id[id_]["pendencia"] else "")
            ),
        )

        campo = st.selectbox(
            "Qual horário está errado",
            options=list(ROTULOS_DOS_CAMPOS),
            format_func=lambda nome: ROTULOS_DOS_CAMPOS[nome],
        )
        horario = st.time_input("Horário correto", value=time(13, 0))
        justificativa = st.text_area(
            "Justificativa",
            max_chars=300,
            placeholder="Ex: voltei do almoço às 13h mas esqueci de marcar no sistema.",
        )
        enviou = st.form_submit_button("Enviar pedido")

    if not enviou:
        return

    if len(justificativa.strip()) < 5:
        st.warning("Escreva uma justificativa — o gestor precisa dela para decidir.")
        return

    # O horario que ESTA no registro hoje, para mostrar na confirmacao.
    atual = por_id[registro_id][campo]

    payload = {
        "registro_id": registro_id,
        "campo_alterado": campo,
        "horario_sugerido": horario.strftime("%H:%M"),
        "justificativa": justificativa.strip(),
    }
    criada, erro = cliente_api.post("/solicitacoes", payload)
    if erro:
        st.error(erro)
        return

    st.success(
        f"Pedido #{criada['id']} enviado: {ROTULOS_DOS_CAMPOS[campo]} de "
        f"{formatar_hora(atual)} para {horario.strftime('%H:%M')}. "
        "Agora é aguardar a decisão do gestor."
    )


def _meus_pedidos(estagiario_id: int) -> None:
    """Lista os pedidos do proprio estagiario, do mais novo para o mais antigo."""
    st.subheader("Meus pedidos")

    solicitacoes, erro = cliente_api.get(
        "/solicitacoes", {"estagiario_id": estagiario_id}
    )
    if erro:
        st.error(erro)
        return

    if not solicitacoes:
        st.caption("Você ainda não abriu nenhum pedido.")
        return

    for solicitacao in solicitacoes:
        rotulo = (
            f"{CORES_DO_STATUS.get(solicitacao['status'], solicitacao['status'])} — "
            f"dia {formatar_data(solicitacao['data_registro'])} — "
            f"{descrever_ajuste(solicitacao)}"
        )
        with st.expander(rotulo):
            st.write(f"**Justificativa:** {solicitacao['justificativa']}")
            st.caption(
                f"Pedido em {formatar_data_hora(solicitacao['data_solicitacao'])} · "
                f"resposta em {formatar_data_hora(solicitacao['data_resposta'])} · "
                f"gestor: {solicitacao['gestor_nome'] or '—'}"
            )
            if solicitacao["status"] == "aprovado":
                st.success("Aprovado — o horário já foi corrigido no seu registro.")
            elif solicitacao["status"] == "rejeitado":
                st.error("Rejeitado — o registro continua como estava.")
