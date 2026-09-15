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

from api.rotas import (
    estagiarios,
    feriados,
    gestores,
    registros,
    relatorio,
    saldo,
    simulacoes,
    solicitacoes,
)
from banco.conexao import criar_tabelas


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Roda uma vez na subida da API: garante que as tabelas existem."""
    criar_tabelas()
    yield


app = FastAPI(
    title="InternHub API",
    version="0.4.0",
    description=(
        "API do banco de horas de estagio. Cobre cadastro de estagiarios, "
        "registro de ponto, saldo, relatorio, simulacao, feriados e o fluxo "
        "de solicitacao de ajuste com aprovacao do gestor."
    ),
    lifespan=ciclo_de_vida,
)

# --- Rotas registradas -------------------------------------------------------
# Cada dev acrescenta a linha do seu modulo quando o PR dele e mergeado.
app.include_router(estagiarios.router)    # Pedro Ribeiro (3.1)  - /estagiarios
app.include_router(registros.router)      # Gustavo (3.2)        - /registros
app.include_router(saldo.router)          # Gustavo (3.2)        - /saldo/{id}
app.include_router(relatorio.router)      # Pietro (3.3)         - /relatorio/{id}
app.include_router(simulacoes.router)     # Pietro (3.3)         - /simulacoes
app.include_router(feriados.router)       # Pietro (3.3)         - /feriados
app.include_router(gestores.router)       # Pedro Henrique (3.4) - /gestores
app.include_router(solicitacoes.router)   # Pedro Henrique (3.4) - /solicitacoes

# Ainda por vir:
# app.include_router(assistente.router)   # Arthur (3.5) - POST /assistente/perguntar
# -----------------------------------------------------------------------------


@app.get("/", tags=["Saude"], summary="Confere se a API esta no ar")
def raiz() -> dict:
    """Usado pelo Streamlit para avisar quando a API nao esta rodando."""
    return {"servico": "InternHub API", "status": "no ar", "documentacao": "/docs"}
