"""Fixtures e ajudantes compartilhados pelos testes de API.

O pytest carrega este arquivo sozinho: qualquer teste da pasta pode pedir
`cliente` como parametro. Ficava dentro de test_api.py; saiu para ca na
Entrega 3, quando os testes das rotas novas (test_entrega3.py) passaram a
precisar do mesmo banco em memoria.

Com o login (Entrega 3), quase toda rota pede o header Authorization. Os
ajudantes novo_gestor(), novo_estagiario() e entrar() cadastram a pessoa e
deixam o `cliente` logado como ela - o teste troca de "quem esta usando" so
chamando entrar() com outro e-mail, igual a uma pessoa trocando de conta.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import api.seguranca as seguranca
import modelos  # noqa: F401 - registra as tabelas em Base.metadata
import servicos.autenticacao as autenticacao
from api.app_api import app
from api.seguranca import verificar_chave_api
from banco.conexao import Base, get_session

SENHA = "senha-de-teste"


@pytest.fixture
def cliente(monkeypatch):
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
    # A chave do aplicativo e testada a parte (test_chave_da_api_...): aqui
    # ela fica desligada para os testes passarem com ou sem API_TOKEN no .env.
    app.dependency_overrides[verificar_chave_api] = lambda: None
    # Hash de senha com poucas iteracoes: o teste confere a regra, nao a
    # lentidao de proposito (200 mil iteracoes deixariam a suite lenta).
    monkeypatch.setattr(autenticacao, "ITERACOES", 1_000)
    # O limite de requisicoes guarda o historico em memoria, entre testes.
    seguranca._requisicoes_por_ip.clear()
    seguranca._logins_por_ip.clear()

    yield TestClient(app)
    app.dependency_overrides.clear()


def _email(nome: str) -> str:
    return f"{nome.split()[0].lower()}@teste.dev"


def entrar(cliente, email: str, senha: str = SENHA) -> dict:
    """Faz login e deixa o cliente mandando o token nas proximas chamadas."""
    resposta = cliente.post("/auth/entrar", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    cliente.headers["Authorization"] = f"Bearer {corpo['token']}"
    return corpo


def sair_da_conta(cliente) -> None:
    """Tira o token do cliente (como abrir o sistema sem estar logado)."""
    cliente.headers.pop("Authorization", None)


def novo_gestor(cliente, nome: str = "Carla", email: str | None = None) -> dict:
    """Cadastra um gestor e entra como ele.

    O primeiro gestor do banco se cadastra sem login; os seguintes precisam
    de um gestor logado - por isso, a partir do segundo, quem chama deve
    estar logado como gestor.
    """
    email = email or _email(nome)
    resposta = cliente.post("/gestores", json={"nome": nome, "email": email, "senha": SENHA})
    assert resposta.status_code == 201, resposta.text
    entrar(cliente, email)
    return resposta.json()


def novo_estagiario(
    cliente, nome: str = "Lucas", gestor_id: int | None = None, email: str | None = None
) -> dict:
    """Cadastra um estagiario (rota aberta) e entra como ele."""
    email = email or _email(nome)
    resposta = cliente.post("/estagiarios", json={
        "nome": nome, "gestor_id": gestor_id, "email": email, "senha": SENHA,
    })
    assert resposta.status_code == 201, resposta.text
    entrar(cliente, email)
    return resposta.json()
