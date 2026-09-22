"""Seguranca da API - autenticacao por token e rate limiting.

Modulo dono: Miguel (Gestor de projeto + Lider tecnico - fase final, itens
21 e 22 do README). Esta e a ultima camada, por cima de tudo que os outros
devs ja construiram - nenhuma rota nova nasce aqui, so protecao.

Duas pecas, independentes uma da outra:

1) Autenticacao por token (item 21): um header "Authorization" com uma
   chave que precisa bater com API_TOKEN, do .env. Sem token configurado
   no .env, a API roda aberta - isso evita travar quem ainda nao gerou o
   proprio .env (ex: um colega clonando o projeto pela primeira vez).

2) Rate limiting (item 22): cada IP tem um limite de requisicoes por
   minuto (README, secao 11). Quem estourar recebe 429 Too Many Requests.

   Isto comecou usando a lib slowapi, mas ela ficou incompativel com a
   versao do Starlette usada pelo FastAPI atual: o middleware dela nunca
   reconhecia a rota (bug confirmado testando na mao - o rate limit nunca
   disparava, nem depois de 35 chamadas seguidas). Trocamos por um
   middleware proprio, simples: guarda em memoria o horario das ultimas
   requisicoes de cada IP e nega quando passa do limite na janela.
"""

import os
import time
from collections import defaultdict

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

TOKEN_ESPERADO = os.getenv("API_TOKEN", "")

# auto_error=False: quando o header nao vem, o FastAPI devolve None em vez
# de recusar sozinho com uma mensagem generica - assim verificar_token()
# decide a mensagem certa (e pode liberar quando nao ha token configurado).
_cabecalho_do_token = APIKeyHeader(name="Authorization", auto_error=False)


def verificar_token(token: str | None = Security(_cabecalho_do_token)) -> None:
    """Dependencia do FastAPI: barra a rota se o token nao bater.

    Aceita tanto o token puro ("abc123") quanto o formato "Bearer abc123"
    no header, para o cliente (Streamlit hoje, React depois) poder usar
    qualquer um dos dois sem quebrar.
    """
    if not TOKEN_ESPERADO:
        return

    recebido = (token or "").removeprefix("Bearer ").strip()
    if recebido != TOKEN_ESPERADO:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao invalido ou ausente.",
        )


LIMITE_REQUISICOES_POR_MINUTO = 30
JANELA_EM_SEGUNDOS = 60

# Para cada IP, guarda o horario (timestamp) de cada requisicao recente.
# E um dicionario comum em memoria: reseta se a API reiniciar, e nao
# funcionaria se um dia o projeto rodasse em mais de um processo ao mesmo
# tempo - suficiente para o escopo deste projeto de faculdade.
_requisicoes_por_ip: dict[str, list[float]] = defaultdict(list)


class LimiteDeRequisicoes(BaseHTTPMiddleware):
    """Middleware do item 22: no maximo 30 requisicoes por IP a cada minuto.

    A cada requisicao, descarta do historico do IP tudo que saiu da janela
    dos ultimos 60s e confere se o que sobrou ja bateu o limite. Registrado
    em app_api.py com app.add_middleware(), entao vale para toda rota sem
    precisar decorar nenhuma - a mesma ideia do middleware global de
    autenticacao, so que aqui conta requisicoes em vez de checar token.
    """

    async def dispatch(self, request: Request, chamar_proxima):
        ip = request.client.host if request.client else "desconhecido"
        agora = time.monotonic()

        historico = _requisicoes_por_ip[ip]
        inicio_da_janela = agora - JANELA_EM_SEGUNDOS
        historico[:] = [momento for momento in historico if momento > inicio_da_janela]

        if len(historico) >= LIMITE_REQUISICOES_POR_MINUTO:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": (
                        f"Limite de {LIMITE_REQUISICOES_POR_MINUTO} requisicoes "
                        "por minuto excedido. Tente novamente em instantes."
                    )
                },
            )

        historico.append(agora)
        return await chamar_proxima(request)
