"""InternHub - dashboard do banco de horas (Streamlit).

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).
Seletor de perfil e menu do gestor: Pedro Henrique (secao 3.4).

Esta tela e um CLIENTE HTTP PURO: ela nao importa modelos/, servicos/ nem
banco/. Tudo que precisa do banco passa por uma chamada a API (paginas/
cliente_api.py). Quem alterar este arquivo deve manter essa regra - foi a
decisao fechada da secao 7 do README (API cobrindo todo o sistema, Escala 2).

O arquivo tem duas metades, uma por perfil:

    "Sou estagiario" -> escolhe uma pessoa e abre as telas dela (ponto,
                        saldo, relatorio, simulacao, solicitacoes, auditoria)
    "Sou gestor"     -> escolhe um gestor e abre a fila de aprovacoes dele

O seletor de perfil NAO e seguranca: ele so decide qual menu aparece. Quem
protege a API de verdade e a autenticacao por token da fase final do Miguel
(itens 21 e 22 do README).

Como rodar (a API precisa estar no ar antes):
    1) uvicorn api.app_api:app --reload
    2) streamlit run app.py
"""

import streamlit as st

from paginas import (
    aprovacoes,
    assistente,
    auditoria,
    cliente_api,
    registro,
    relatorio,
    saldo,
    simulacao,
    solicitacoes,
)

st.set_page_config(page_title="InternHub", page_icon=":clock3:", layout="centered")


# --- Telas do perfil estagiario ----------------------------------------------


def formulario_cadastro(chave_do_form: str, gestores: list) -> None:
    """Formulario de cadastro de estagiario, reaproveitado nos dois cenarios."""
    opcoes_gestor = [None] + [gestor["id"] for gestor in gestores]
    nome_do_gestor = {gestor["id"]: gestor["nome"] for gestor in gestores}

    with st.form(chave_do_form):
        nome = st.text_input("Nome do estagiário", max_chars=120)
        coluna_a, coluna_b = st.columns(2)
        meta_diaria = coluna_a.number_input(
            "Meta de horas por dia", min_value=1.0, max_value=24.0, value=6.0, step=0.5
        )
        meta_semanal = coluna_b.number_input(
            "Meta de horas por semana",
            min_value=1.0,
            max_value=168.0,
            value=30.0,
            step=1.0,
        )
        gestor_id = st.selectbox(
            "Gestor responsável",
            options=opcoes_gestor,
            format_func=lambda id_: (
                "Sem gestor por enquanto" if id_ is None else nome_do_gestor[id_]
            ),
            help="É o gestor escolhido aqui que vai receber os seus pedidos de ajuste.",
        )
        enviou = st.form_submit_button("Cadastrar")

    if not enviou:
        return

    if len(nome.strip()) < 2:
        st.warning("Digite um nome com pelo menos 2 caracteres.")
        return

    payload = {
        "nome": nome.strip(),
        "meta_horas_diaria": meta_diaria,
        "meta_horas_semanal": meta_semanal,
        "gestor_id": gestor_id,
    }
    criado, erro = cliente_api.post("/estagiarios", payload)
    if erro:
        st.error(erro)
        return

    # Ja deixa o recem-cadastrado selecionado, para o usuario nao ter que
    # procurar o proprio nome na lista logo depois de se cadastrar.
    st.session_state["estagiario_id"] = criado["id"]
    st.success(f"Estagiário {criado['nome']} cadastrado!")
    st.rerun()


def seletor_de_estagiario(estagiarios: list, gestores: list) -> None:
    """Dropdown 'Selecione seu nome' - o coracao do multiusuario."""
    ids = [pessoa["id"] for pessoa in estagiarios]
    por_id = {pessoa["id"]: pessoa for pessoa in estagiarios}

    # Mantem a selecao anterior se ela ainda existir no banco.
    salvo = st.session_state.get("estagiario_id")
    indice = ids.index(salvo) if salvo in ids else 0

    escolhido = st.selectbox(
        "Selecione seu nome",
        options=ids,
        index=indice,
        format_func=lambda id_: por_id[id_]["nome"],
    )
    st.session_state["estagiario_id"] = escolhido

    pessoa = por_id[escolhido]
    configuracao = pessoa.get("configuracao") or {}
    coluna_a, coluna_b = st.columns(2)
    coluna_a.metric("Meta diária", f"{configuracao.get('meta_horas_diaria', 0):.1f} h")
    coluna_b.metric("Meta semanal", f"{configuracao.get('meta_horas_semanal', 0):.1f} h")

    _aviso_e_troca_de_gestor(pessoa, gestores)

    with st.expander("Cadastrar novo estagiário"):
        formulario_cadastro("form_cadastro_extra", gestores)


def _aviso_e_troca_de_gestor(pessoa: dict, gestores: list) -> None:
    """Mostra o gestor responsavel e permite trocar (PATCH /estagiarios/{id}).

    Acrescentado por Pedro Henrique (secao 3.4): sem gestor vinculado, os
    pedidos de ajuste desta pessoa nao cairiam na fila de ninguem.
    """
    if not gestores:
        st.info(
            "Nenhum gestor cadastrado ainda. Entre no perfil **Sou gestor** "
            "para cadastrar um — sem gestor, ninguém aprova os ajustes de ponto."
        )
        return

    nome_do_gestor = {gestor["id"]: gestor["nome"] for gestor in gestores}
    atual = pessoa.get("gestor_id")

    if atual is None:
        st.warning(
            "Você ainda não tem gestor responsável. Escolha um abaixo para "
            "poder pedir ajustes de ponto."
        )

    with st.expander(f"Gestor responsável: {nome_do_gestor.get(atual, 'nenhum')}"):
        opcoes = [None] + list(nome_do_gestor)
        escolhido = st.selectbox(
            "Trocar gestor",
            options=opcoes,
            index=opcoes.index(atual) if atual in opcoes else 0,
            format_func=lambda id_: (
                "Sem gestor" if id_ is None else nome_do_gestor[id_]
            ),
            key="troca_de_gestor",
        )
        if st.button("Salvar gestor", key="botao_troca_gestor"):
            _, erro = cliente_api.patch(
                f"/estagiarios/{pessoa['id']}", {"gestor_id": escolhido}
            )
            if erro:
                st.error(erro)
            else:
                st.success("Gestor atualizado.")
                st.rerun()


def menu_do_estagiario(estagiario_id: int) -> None:
    """Menu lateral do perfil estagiario."""
    st.sidebar.caption(f"Estagiário selecionado: #{estagiario_id}")

    # Cada pagina expoe mostrar(estagiario_id) - esse e o contrato entre o
    # menu e as telas, e e o que permite listar tudo em um dicionario.
    paginas = {
        "Registrar ponto": registro.mostrar,
        "Ver saldo": saldo.mostrar,
        "Relatório mensal": relatorio.mostrar,
        "Simular cenário": simulacao.mostrar,
        "Solicitações": solicitacoes.mostrar,
        "Auditoria": auditoria.mostrar,
        "Assistente de IA": assistente.mostrar,
    }

    escolha = st.sidebar.radio("Ir para", ["Início", *paginas])
    if escolha == "Início":
        st.info("Escolha uma tela no menu à esquerda.")
        return

    paginas[escolha](estagiario_id)


# --- Telas do perfil gestor --------------------------------------------------


def perfil_gestor() -> None:
    """Metade da tela dedicada ao gestor: escolher quem e, e abrir a fila.

    Modulo dono: Pedro Henrique (secao 3.4).
    """
    gestores, erro = cliente_api.get("/gestores")
    if erro:
        st.error(erro)
        return

    if not gestores:
        st.info("Nenhum gestor cadastrado ainda. Faça o primeiro cadastro abaixo.")
        _formulario_cadastro_gestor("form_gestor_inicial")
        return

    ids = [gestor["id"] for gestor in gestores]
    por_id = {gestor["id"]: gestor for gestor in gestores}
    salvo = st.session_state.get("gestor_id")
    indice = ids.index(salvo) if salvo in ids else 0

    escolhido = st.selectbox(
        "Selecione seu nome",
        options=ids,
        index=indice,
        format_func=lambda id_: por_id[id_]["nome"],
    )
    st.session_state["gestor_id"] = escolhido

    equipe, erro = cliente_api.get("/estagiarios")
    if erro:
        st.error(erro)
        return

    sob_gestao = [pessoa for pessoa in equipe if pessoa.get("gestor_id") == escolhido]
    st.metric("Estagiários sob sua gestão", len(sob_gestao))
    if not sob_gestao:
        st.warning(
            "Nenhum estagiário está vinculado a você. Peça para eles se "
            "vincularem no perfil **Sou estagiário**, ou cadastre-os já com "
            "o seu nome como gestor responsável."
        )

    with st.expander("Cadastrar novo gestor"):
        _formulario_cadastro_gestor("form_gestor_extra")

    st.divider()

    st.sidebar.caption(f"Gestor selecionado: #{escolhido}")
    escolha = st.sidebar.radio("Ir para", ["Aprovações", "Auditoria"])
    if escolha == "Aprovações":
        aprovacoes.mostrar(escolhido)
    else:
        # Sem estagiario_id: o gestor ve o historico de todo mundo.
        auditoria.mostrar()


def _formulario_cadastro_gestor(chave_do_form: str) -> None:
    """Formulario de POST /gestores."""
    with st.form(chave_do_form):
        nome = st.text_input("Nome do gestor", max_chars=120)
        enviou = st.form_submit_button("Cadastrar gestor")

    if not enviou:
        return

    if len(nome.strip()) < 2:
        st.warning("Digite um nome com pelo menos 2 caracteres.")
        return

    criado, erro = cliente_api.post("/gestores", {"nome": nome.strip()})
    if erro:
        st.error(erro)
        return

    st.session_state["gestor_id"] = criado["id"]
    st.success(f"Gestor {criado['nome']} cadastrado!")
    st.rerun()


# --- Fluxo principal ---------------------------------------------------------

st.title("InternHub — Banco de Horas do Estágio")

# Seletor de perfil (Pedro Henrique, secao 3.4). Fica na barra lateral para
# nao competir com o conteudo da tela escolhida.
perfil = st.sidebar.radio("Perfil", ["Sou estagiário", "Sou gestor"])
st.sidebar.divider()

if perfil == "Sou gestor":
    perfil_gestor()
else:
    estagiarios, erro_api = cliente_api.get("/estagiarios")
    lista_de_gestores, _ = cliente_api.get("/gestores")
    lista_de_gestores = lista_de_gestores or []

    if erro_api:
        st.error(erro_api)
    elif not estagiarios:
        st.info("Nenhum estagiário cadastrado ainda. Faça o primeiro cadastro abaixo.")
        formulario_cadastro("form_cadastro_inicial", lista_de_gestores)
    else:
        seletor_de_estagiario(estagiarios, lista_de_gestores)
        st.divider()
        menu_do_estagiario(st.session_state["estagiario_id"])
