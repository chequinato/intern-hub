"""Aplicacao FastAPI do InternHub.

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).

Esta e a unica camada que fala com o banco. O Streamlit e cliente HTTP puro:
nenhuma pagina importa modelos/ ou servicos/ diretamente.

Como rodar:
    uvicorn api.app_api:app --reload
    Documentacao interativa em http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.rotas import estagiarios, registros, saldo, feriados, simulacoes, relatorio
from banco.conexao import criar_tabelas

# Os proximos devs importam o router deles aqui:
# from api.rotas import feriados, relatorio, simulacoes      # Pietro (3.3) feito!
# from api.rotas import solicitacoes                         # Pedro Henrique (3.4)
# from api.rotas import assistente                           # Arthur (3.5)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Roda uma vez na subida da API: garante que as tabelas existem."""
    criar_tabelas()
    yield


app = FastAPI(
    title="InternHub API",
    version="0.1.0",
    description=(
        "API do banco de horas de estagio. Nesta fase (fundacao) so as rotas "
        "de /estagiarios estao no ar."
    ),
    lifespan=ciclo_de_vida,
)

app.include_router(estagiarios.router)
app.include_router(registros.router)  # Gustavo (3.2) - POST/GET /registros
app.include_router(saldo.router)  # Gustavo (3.2) - GET /saldo/{id}
app.include_router(feriados.router) # Pietro (3.3) - POST/GET /feriados
app.include_router(simulacoes.router) # Pietro (3.3) - POST /simulacoes
app.include_router(relatorio.router) # Pietro (3.3) - GET /relatorio/{id}

# --- Rotas dos proximos devs -------------------------------------------------
# Descomente a linha correspondente quando o PR daquele modulo for mergeado.
# app.include_router(relatorio.router)      # Pietro  (3.3)  - GET  /relatorio/{id}
# app.include_router(simulacoes.router)     # Pietro  (3.3)  - POST /simulacoes
# app.include_router(feriados.router)       # Pietro  (3.3)  - POST/GET /feriados
# app.include_router(solicitacoes.router)   # P.Henrique(3.4)- /solicitacoes
# app.include_router(assistente.router)     # Arthur  (3.5)  - POST /assistente/perguntar
# -----------------------------------------------------------------------------


@app.get("/", tags=["Saude"], summary="Confere se a API esta no ar")
def raiz() -> dict:
    """Usado pelo Streamlit para avisar quando a API nao esta rodando."""
    return {"servico": "InternHub API", "status": "no ar", "documentacao": "/docs"}
