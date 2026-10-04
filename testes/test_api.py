"""testes/test_api.py

Testes de ponta a ponta da API: fazem a requisicao HTTP de verdade (via
TestClient do FastAPI) e conferem o que volta, passando por rota, schema,
servico e banco.

Nao usam banco/dados.db: cada teste ganha um banco SQLite novo em memoria,
trocando a dependencia get_session da API por uma que abre sessao nesse
banco (app.dependency_overrides). Assim os testes nao apagam nem sujam os
dados de quem esta rodando o sistema.

Rodar com:
    pytest testes/test_api.py -v
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import modelos  # noqa: F401 - registra as tabelas em Base.metadata
import api.seguranca as seguranca
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


def _criar_estagiario_com_gestor(cliente):
    gestor = cliente.post("/gestores", json={"nome": "Carla"}).json()
    estagiario = cliente.post(
        "/estagiarios", json={"nome": "Lucas", "gestor_id": gestor["id"]}
    ).json()
    return gestor, estagiario


def test_registro_completo_entra_no_saldo(cliente):
    """6h trabalhadas com meta de 6h: saldo zero, um dia na conta."""
    _, estagiario = _criar_estagiario_com_gestor(cliente)

    resposta = cliente.post("/registros", json={
        "estagiario_id": estagiario["id"], "data": "2026-09-28",
        "entrada": "09:00", "saida_almoco": "12:00",
        "retorno_almoco": "13:00", "saida": "16:00",
    })
    assert resposta.status_code == 201
    assert resposta.json()["horas_trabalhadas"] == 6.0
    assert resposta.json()["pendencia"] is False

    saldo = cliente.get(f"/saldo/{estagiario['id']}").json()
    assert saldo["saldo_acumulado"] == 0.0
    assert saldo["dias_registrados"] == 1


def test_horario_fora_de_ordem_e_recusado_com_422(cliente):
    """Saida antes da entrada nem chega no banco: o schema recusa."""
    _, estagiario = _criar_estagiario_com_gestor(cliente)

    resposta = cliente.post("/registros", json={
        "estagiario_id": estagiario["id"], "data": "2026-09-28",
        "entrada": "10:00", "saida": "09:00",
    })
    assert resposta.status_code == 422


def test_ajuste_aprovado_corrige_registro_e_saldo(cliente):
    """Fluxo inteiro: dia com pendencia -> pedido -> gestor aprova -> saldo muda.

    O dia 29 fica sem retorno do almoco, entao nao entra no saldo. Depois
    que o gestor aprova o retorno as 13:00, o dia fecha com 7h (meta 6h) e
    o saldo passa a ser +1h.
    """
    gestor, estagiario = _criar_estagiario_com_gestor(cliente)
    registro = cliente.post("/registros", json={
        "estagiario_id": estagiario["id"], "data": "2026-09-29",
        "entrada": "09:00", "saida_almoco": "12:00", "saida": "17:00",
    }).json()
    assert registro["pendencia"] is True
    assert cliente.get(f"/saldo/{estagiario['id']}").json()["dias_registrados"] == 0

    pedido = cliente.post("/solicitacoes", json={
        "registro_id": registro["id"], "campo_alterado": "retorno_almoco",
        "horario_sugerido": "13:00", "justificativa": "Esqueci de bater o retorno",
    })
    assert pedido.status_code == 201

    fila = cliente.get("/solicitacoes/pendentes", params={"gestor_id": gestor["id"]})
    assert len(fila.json()) == 1

    decisao = cliente.patch(
        f"/solicitacoes/{pedido.json()['id']}",
        json={"status": "aprovado", "gestor_id": gestor["id"]},
    ).json()
    assert decisao["solicitacao"]["status"] == "aprovado"
    assert decisao["saldo_acumulado"] == 1.0


def test_relatorio_nao_conta_falta_antes_do_primeiro_ponto(cliente):
    """CASO QUE FALHOU E FOI CORRIGIDO (Entrega 2).

    Quem comecou a bater ponto no dia 28/09 aparecia com 20 faltas em
    setembro: o relatorio contava como falta todo dia util desde o dia 1,
    inclusive os dias antes de a pessoa comecar o estagio. Agora a conta
    so comeca no primeiro registro - 28, 29 e 30/09 sao dias uteis, os dois
    primeiros foram trabalhados, sobra 1 falta (dia 30).
    """
    _, estagiario = _criar_estagiario_com_gestor(cliente)
    for dia in ("2026-09-28", "2026-09-29"):
        cliente.post("/registros", json={
            "estagiario_id": estagiario["id"], "data": dia,
            "entrada": "09:00", "saida_almoco": "12:00",
            "retorno_almoco": "13:00", "saida": "16:00",
        })

    relatorio = cliente.get(
        f"/relatorio/{estagiario['id']}", params={"mes": 9, "ano": 2026}
    ).json()
    assert relatorio["faltas"] == 1
    assert relatorio["total_horas_trabalhadas"] == 12.0


def test_feriado_repetido_devolve_409(cliente):
    cliente.post("/feriados", json={"data": "2026-09-07", "descricao": "Independencia"})
    repetido = cliente.post("/feriados", json={"data": "2026-09-07", "descricao": "De novo"})
    assert repetido.status_code == 409


def test_exportacao_do_relatorio_gera_pdf_e_excel(cliente):
    _, estagiario = _criar_estagiario_com_gestor(cliente)
    for formato, tipo in (("pdf", "application/pdf"), ("excel", "spreadsheetml")):
        resposta = cliente.get(
            f"/relatorio/{estagiario['id']}/exportar",
            params={"mes": 9, "ano": 2026, "formato": formato},
        )
        assert resposta.status_code == 200
        assert tipo in resposta.headers["content-type"]


def test_rota_protegida_sem_token_devolve_401(cliente, monkeypatch):
    """Com API_TOKEN configurado, chamar sem o header certo da 401."""
    app.dependency_overrides.pop(verificar_token)
    monkeypatch.setattr(seguranca, "TOKEN_ESPERADO", "segredo-de-teste")

    assert cliente.get("/estagiarios").status_code == 401
    assert cliente.get(
        "/estagiarios", headers={"Authorization": "Bearer segredo-de-teste"}
    ).status_code == 200
