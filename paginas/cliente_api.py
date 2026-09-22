"""Cliente HTTP compartilhado pelas telas do Streamlit.

Modulo dono: Pedro Henrique (Desenvolvedor 4 - secao 3.4).

Por que existe: as telas do projeto sao clientes HTTP puros (decisao fechada
do README, secao 7) e todas repetem o mesmo ritual - montar a URL, chamar a
API, tratar "API fora do ar", tratar status code e so entao usar o JSON. As
tres telas do fluxo de solicitacoes fariam essa mesma ladainha nove vezes.
Aqui isso fica escrito uma vez so.

O contrato e sempre o mesmo, e as telas ficam de uma linha:

    dados, erro = cliente_api.get("/solicitacoes", {"estagiario_id": 1})
    if erro:
        st.error(erro)
        return

Em caso de sucesso, `erro` e None. Em caso de falha, `dados` e None e `erro`
ja vem em portugues, pronto para jogar em st.error().
"""

import os

import requests

# Endereco da API. Pode ser trocado pela variavel de ambiente sem mexer no
# codigo (util se alguem do grupo rodar a API em outra porta).
API_URL = os.getenv("INTERNHUB_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SEGUNDOS = 5

# Token da fase final de seguranca (Miguel, itens 21-22 do README). Sem
# API_TOKEN no .env, a API roda aberta e este header e ignorado por ela -
# ver api/seguranca.py.
API_TOKEN = os.getenv("API_TOKEN", "")

MSG_API_FORA = (
    f"Não consegui falar com a API em {API_URL}.\n\n"
    "Abra outro terminal, na pasta do projeto, e rode:\n\n"
    "`uvicorn api.app_api:app --reload`"
)


def get(caminho: str, parametros: dict | None = None):
    """GET em uma rota da API. Devolve (dados, erro)."""
    return _chamar("GET", caminho, parametros=parametros)


def post(caminho: str, payload: dict):
    """POST em uma rota da API. Devolve (dados, erro)."""
    return _chamar("POST", caminho, payload=payload)


def patch(caminho: str, payload: dict):
    """PATCH em uma rota da API. Devolve (dados, erro)."""
    return _chamar("PATCH", caminho, payload=payload)


def _chamar(verbo: str, caminho: str, payload: dict = None, parametros: dict = None):
    """Faz a requisicao e traduz qualquer falha em uma mensagem em portugues."""
    cabecalhos = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
    try:
        resposta = requests.request(
            verbo,
            f"{API_URL}{caminho}",
            json=payload,
            params=parametros,
            headers=cabecalhos,
            timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.exceptions.ConnectionError:
        return None, MSG_API_FORA
    except requests.exceptions.RequestException as erro:
        return None, f"Falha ao falar com a API: {erro}"

    if resposta.status_code in (200, 201):
        return resposta.json(), None

    return None, _mensagem_do_erro(resposta)


def _mensagem_do_erro(resposta) -> str:
    """Transforma a resposta de erro da API em uma frase legivel na tela.

    O FastAPI devolve o motivo dentro da chave "detail" - tanto no 404/409
    que as nossas rotas levantam quanto no 422 do Pydantic. Quando o corpo
    nao e JSON (ex: a API caiu no meio), caimos no texto cru.
    """
    try:
        detalhe = resposta.json().get("detail")
    except ValueError:
        return f"A API respondeu {resposta.status_code}: {resposta.text}"

    if isinstance(detalhe, str):
        return detalhe

    # 422 do Pydantic: uma lista com um item por campo invalido.
    if isinstance(detalhe, list):
        problemas = [item.get("msg", "campo inválido") for item in detalhe]
        return "Dados inválidos: " + "; ".join(problemas)

    return f"A API respondeu {resposta.status_code}."
