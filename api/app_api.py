"""Aplicacao FastAPI do InternHub.

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).

Esta e a unica camada que fala com o banco. O Streamlit e cliente HTTP puro:
nenhuma pagina importa modelos/ ou servicos/ diretamente.

Como rodar:
    uvicorn api.app_api:app --reload
    Documentacao interativa em http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Le o .env (OPENAI_API_KEY, API_TOKEN) para o ambiente ANTES de qualquer
# outro import deste pacote - api/seguranca.py e servicos/assistente.py
# leem essas variaveis com os.getenv(), que so enxerga o que ja estiver
# no ambiente do processo.
load_dotenv()

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.rotas import (
    assistente,
    estagiarios,
    feriados,
    gestores,
    registros,
    relatorio,
    saldo,
    simulacoes,
    solicitacoes,
)
from api.seguranca import LimiteDeRequisicoes, verificar_token
from banco.conexao import criar_tabelas


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Roda uma vez na subida da API: garante que as tabelas existem."""
    criar_tabelas()
    yield


app = FastAPI(
    title="InternHub API",
    version="0.5.0",
    description=(
        "API do banco de horas de estagio. Cobre cadastro de estagiarios, "
        "registro de ponto, saldo, relatorio, simulacao, feriados, o fluxo "
        "de solicitacao de ajuste com aprovacao do gestor e o assistente de IA."
    ),
    lifespan=ciclo_de_vida,
)

# CORS: o frontend em React (frontend/) roda em outra origem (porta do Vite,
# ex: localhost:5173) e o navegador bloqueia chamadas entre origens
# diferentes por padrao. Como a API nao usa cookie de sessao (a autenticacao
# e so o header Authorization, ver api/seguranca.py), liberar geral e
# suficiente e mais simples do que listar cada origem de dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (item 22, fase final do Miguel): o middleware aplica o limite
# de 30 req/min por IP (ver api/seguranca.py) a toda rota, sem precisar
# decorar cada uma.
app.add_middleware(LimiteDeRequisicoes)

# --- Rotas registradas -------------------------------------------------------
# Cada dev acrescenta a linha do seu modulo quando o PR dele e mergeado.
# dependencies=[Depends(verificar_token)] (item 21, fase final do Miguel):
# toda rota de negocio passa a exigir o header Authorization com o token
# certo. So a rota de saude "/", declarada direto no app mais abaixo, fica
# de fora - e o que o Streamlit usa pra confirmar que a API esta no ar.
_protegida = [Depends(verificar_token)]
app.include_router(estagiarios.router, dependencies=_protegida)    # Pedro Ribeiro (3.1)  - /estagiarios
app.include_router(registros.router, dependencies=_protegida)      # Gustavo (3.2)        - /registros
app.include_router(saldo.router, dependencies=_protegida)          # Gustavo (3.2)        - /saldo/{id}
app.include_router(relatorio.router, dependencies=_protegida)      # Pietro (3.3)         - /relatorio/{id}
app.include_router(simulacoes.router, dependencies=_protegida)     # Pietro (3.3)         - /simulacoes
app.include_router(feriados.router, dependencies=_protegida)       # Pietro (3.3)         - /feriados
app.include_router(gestores.router, dependencies=_protegida)       # Pedro Henrique (3.4) - /gestores
app.include_router(solicitacoes.router, dependencies=_protegida)   # Pedro Henrique (3.4) - /solicitacoes
app.include_router(assistente.router, dependencies=_protegida)     # Arthur (3.5)         - /assistente/perguntar
# -----------------------------------------------------------------------------


@app.get("/", tags=["Saude"], summary="Confere se a API esta no ar")
def raiz() -> dict:
    """Usado pelo Streamlit para avisar quando a API nao esta rodando."""
    return {"servico": "InternHub API", "status": "no ar", "documentacao": "/docs"}
