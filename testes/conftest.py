"""Fixtures compartilhadas pelos testes de API.

O pytest carrega este arquivo sozinho: qualquer teste da pasta pode pedir
`cliente` como parametro. Ficava dentro de test_api.py; saiu para ca na
Entrega 3, quando os testes das rotas novas (test_entrega3.py) passaram a
precisar do mesmo banco em memoria.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import modelos  # noqa: F401 - registra as tabelas em Base.metadata
from api.app_api import app
from api.seguranca import verificar_token
from banco.conexao import Base, get_session


@pytest.fixture
def cliente():
    """Cliente HTTP falando com a API em cima de um banco em memoria."""
    # StaticPool: o banco em memoria vive dentro de UMA conexao. Sem isso,
    # cada sessao abriria uma conexao nova e veria um banco vazio.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessaoDeTeste = sessionmaker(bind=engine, expire_on_commit=False)

    def sessao_de_teste():
        session = SessaoDeTeste()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = sessao_de_teste
    # O token e testado a parte (test_rota_protegida_sem_token_devolve_401):
    # aqui ele fica desligado para os testes passarem com ou sem API_TOKEN
    # no .env de quem roda.
    app.dependency_overrides[verificar_token] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()
