"""InternHub - dashboard do banco de horas (Streamlit).

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).

Esta tela e um CLIENTE HTTP PURO: ela nao importa modelos/, servicos/ nem
banco/. Tudo que precisa do banco passa por uma chamada a API (requests).
Quem alterar este arquivo deve manter essa regra - foi a decisao fechada da
secao 7 do README (API cobrindo todo o sistema, Escala 2).

Como rodar (a API precisa estar no ar antes):
    1) uvicorn api.app_api:app --reload
    2) streamlit run app.py
"""

import os

import requests
import streamlit as st

# Endereco da API. Pode ser trocado pela variavel de ambiente sem mexer no
# codigo (util se alguem do grupo rodar a API em outra porta).
API_URL = os.getenv("INTERNHUB_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SEGUNDOS = 5

MSG_API_FORA = (
    f"Nao consegui falar com a API em {API_URL}.\n\n"
    "Abra outro terminal, na pasta do projeto, e rode:\n\n"
    "`uvicorn api.app_api:app --reload`"
)

st.set_page_config(page_title="InternHub", page_icon=":clock3:", layout="centered")


# --- Conversa com a API ------------------------------------------------------


def listar_estagiarios():
    """GET /estagiarios. Devolve (lista, mensagem_de_erro)."""
    try:
        resposta = requests.get(f"{API_URL}/estagiarios", timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.ConnectionError:
        return None, MSG_API_FORA
    except requests.exceptions.RequestException as erro:
        return None, f"Falha ao consultar a API: {erro}"

    if resposta.status_code != 200:
        return None, f"A API respondeu {resposta.status_code}: {resposta.text}"
    return resposta.json(), None


def cadastrar_estagiario(nome, meta_diaria, meta_semanal):
    """POST /estagiarios. Devolve (estagiario_criado, mensagem_de_erro)."""
    payload = {
        "nome": nome,
        "meta_horas_diaria": meta_diaria,
        "meta_horas_semanal": meta_semanal,
    }
    try:
        resposta = requests.post(
            f"{API_URL}/estagiarios", json=payload, timeout=TIMEOUT_SEGUNDOS
        )
    except requests.exceptions.ConnectionError:
        return None, MSG_API_FORA
    except requests.exceptions.RequestException as erro:
        return None, f"Falha ao falar com a API: {erro}"

    if resposta.status_code == 201:
        return resposta.json(), None
    if resposta.status_code == 422:
        # 422 e o erro de validacao do Pydantic (ex: nome com 1 letra).
        return None, "Dados invalidos. Confira o nome e as metas de horas."
    return None, f"A API respondeu {resposta.status_code}: {resposta.text}"


# --- Telas -------------------------------------------------------------------


def formulario_cadastro(chave_do_form: str) -> None:
    """Formulario de cadastro, reaproveitado nos dois cenarios da tela."""
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
        enviou = st.form_submit_button("Cadastrar")

    if not enviou:
        return

    if len(nome.strip()) < 2:
        st.warning("Digite um nome com pelo menos 2 caracteres.")
        return

    criado, erro = cadastrar_estagiario(nome.strip(), meta_diaria, meta_semanal)
    if erro:
        st.error(erro)
        return

    # Ja deixa o recem-cadastrado selecionado, para o usuario nao ter que
    # procurar o proprio nome na lista logo depois de se cadastrar.
    st.session_state["estagiario_id"] = criado["id"]
    st.success(f"Estagiário {criado['nome']} cadastrado!")
    st.rerun()


def seletor_de_estagiario(estagiarios: list) -> None:
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

    with st.expander("Cadastrar novo estagiário"):
        formulario_cadastro("form_cadastro_extra")


def menu_principal() -> None:
    """Esqueleto do menu. Cada dev liga a sua pagina aqui quando terminar."""
    st.sidebar.title("Menu")
    st.sidebar.caption(f"Estagiário selecionado: #{st.session_state['estagiario_id']}")

    # Conforme cada PR for mergeado, troque o item por uma chamada a pagina:
    #   from paginas import registro; registro.mostrar(estagiario_id)
    paginas_futuras = {
        "Registrar ponto": "Gustavo (3.2) - paginas/registro.py",
        "Ver saldo": "Gustavo (3.2) - paginas/saldo.py",
        "Relatório mensal": "Pietro (3.3) - paginas/relatorio.py",
        "Simular cenário": "Pietro (3.3) - paginas/simulacao.py",
        "Solicitações": "Pedro Henrique (3.4) - paginas/solicitacoes.py",
        "Aprovações": "Pedro Henrique (3.4) - paginas/aprovacoes.py",
        "Auditoria": "Pedro Henrique (3.4) - paginas/auditoria.py",
        "Assistente": "Arthur (3.5) - paginas/assistente.py",
    }
    escolha = st.sidebar.radio("Ir para", ["Início", *paginas_futuras])

    if escolha == "Início":
        st.info(
            "Fundação no ar: cadastro e seleção de estagiários funcionando. "
            "As demais páginas entram conforme cada dev finalizar a sua parte."
        )
        return

    st.warning(f"Página ainda não implementada — responsável: {paginas_futuras[escolha]}")


# --- Fluxo principal ---------------------------------------------------------

st.title("InternHub — Banco de Horas do Estágio")

estagiarios, erro_api = listar_estagiarios()

if erro_api:
    st.error(erro_api)
elif not estagiarios:
    st.info("Nenhum estagiário cadastrado ainda. Faça o primeiro cadastro abaixo.")
    formulario_cadastro("form_cadastro_inicial")
else:
    seletor_de_estagiario(estagiarios)
    st.divider()
    menu_principal()
