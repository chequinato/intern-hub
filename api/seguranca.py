"""Seguranca da API - chave do aplicativo e rate limiting.

Modulo dono: Miguel (Gestor de projeto + Lider tecnico - fase final, itens
21 e 22 do README). Esta e a camada de protecao por cima de tudo que os
outros devs construiram.

Tres pecas, independentes umas das outras:

1) Chave da API (item 21): um header "X-API-Key" que precisa bater com
   API_TOKEN, do .env. Ela identifica o APLICATIVO (o nosso frontend), nao a
   pessoa. Sem chave configurada no .env, a API aceita qualquer cliente -
   isso evita travar quem ainda nao gerou o proprio .env.

   Ate a Entrega 3 essa chave ia no header "Authorization". Com o login
   (api/permissoes.py), o "Authorization" passou a levar o token de quem
   entrou - que identifica a PESSOA - e a chave do aplicativo mudou para o
   "X-API-Key". E exatamente a separacao que a Entrega 1 ja descrevia: a
   chave protege o acesso as rotas; o login diz quem esta usando.

2) Rate limiting (item 22): cada IP tem um limite de requisicoes por
   minuto (README, secao 11). Quem estourar recebe 429 Too Many Requests.

   Isto comecou usando a lib slowapi, mas ela ficou incompativel com a
   versao do Starlette usada pelo FastAPI atual: o middleware dela nunca
   reconhecia a rota (bug confirmado testando na mao - o rate limit nunca
   disparava, nem depois de 35 chamadas seguidas). Trocamos por um
   middleware proprio, simples: guarda em memoria o horario das ultimas
   requisicoes de cada IP e nega quando passa do limite na janela.

3) Limite proprio para tentativas de login (Entrega 3): 10 por minuto por
   IP. Com 120 por minuto, daria para testar 120 senhas por minuto; com 10,
   adivinhar a senha de alguem fica impraticavel.
"""

import os
import secrets
import time
from collections import defaultdict

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

TOKEN_ESPERADO = os.getenv("API_TOKEN", "")

# auto_error=False: quando o header nao vem, o FastAPI devolve None em vez
# de recusar sozinho com uma mensagem generica - assim verificar_chave_api()
# decide a mensagem certa (e pode liberar quando nao ha chave configurada).
_cabecalho_da_chave = APIKeyHeader(name="X-API-Key", auto_error=False)


def verificar_chave_api(chave: str | None = Security(_cabecalho_da_chave)) -> None:
    """Dependencia do FastAPI: barra a rota se a chave do aplicativo nao bater."""
    if not TOKEN_ESPERADO:
        return

    recebida = (chave or "").strip()
    # compare_digest em vez de "!=": o "!=" para no primeiro caractere
    # diferente, entao uma chave com o comeco certo demora um pouquinho mais
    # para ser recusada - medindo esse tempo, daria para descobrir a chave
    # aos poucos. compare_digest leva sempre o mesmo tempo.
    if not secrets.compare_digest(recebida.encode(), TOKEN_ESPERADO.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave da API invalida ou ausente (header X-API-Key).",
        )


# Comecou em 30 (o exemplo da secao 11 do README). Subiu para 120 depois do
# frontend em React: cada tela faz de 2 a 4 chamadas ao abrir, entao navegar
# rapido entre as abas estourava o limite e a tela mostrava erro 429 no meio
# do uso normal. 120/min ainda barra um loop descontrolado chamando a API.
LIMITE_REQUISICOES_POR_MINUTO = 120
LIMITE_TENTATIVAS_LOGIN_POR_MINUTO = 10
JANELA_EM_SEGUNDOS = 60
CAMINHO_DO_LOGIN = "/auth/entrar"

# Para cada IP, guarda o horario (timestamp) de cada requisicao recente.
# E um dicionario comum em memoria: reseta se a API reiniciar, e nao
# funcionaria se um dia o projeto rodasse em mais de um processo ao mesmo
# tempo - suficiente para o escopo deste projeto de faculdade.
_requisicoes_por_ip: dict[str, list[float]] = defaultdict(list)
_logins_por_ip: dict[str, list[float]] = defaultdict(list)


def _estourou(historico: list[float], limite: int, agora: float) -> bool:
    """Descarta o que saiu da janela e diz se o que sobrou ja bateu o limite."""
    inicio_da_janela = agora - JANELA_EM_SEGUNDOS
    historico[:] = [momento for momento in historico if momento > inicio_da_janela]
    if len(historico) >= limite:
        return True
    historico.append(agora)
    return False


class LimiteDeRequisicoes(BaseHTTPMiddleware):
    """Middleware do item 22: no maximo 120 requisicoes por IP a cada minuto,
    e no maximo 10 tentativas de login.

    Registrado em app_api.py com app.add_middleware(), entao vale para toda
    rota sem precisar decorar nenhuma.
    """

    async def dispatch(self, request: Request, chamar_proxima):
        ip = request.client.host if request.client else "desconhecido"
        agora = time.monotonic()

        if _estourou(_requisicoes_por_ip[ip], LIMITE_REQUISICOES_POR_MINUTO, agora):
            return _resposta_429(
                f"Limite de {LIMITE_REQUISICOES_POR_MINUTO} requisicoes por minuto "
                "excedido. Tente novamente em instantes."
            )

        eh_login = request.method == "POST" and request.url.path == CAMINHO_DO_LOGIN
        if eh_login and _estourou(_logins_por_ip[ip], LIMITE_TENTATIVAS_LOGIN_POR_MINUTO, agora):
            return _resposta_429(
                "Muitas tentativas de login. Espere um minuto e tente de novo."
            )

        return await chamar_proxima(request)


def _resposta_429(mensagem: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": mensagem}
    )
