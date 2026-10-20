"""testes/test_estagio.py

Testes do contrato de estagio (Entrega 3, Miguel), as tres regras da Lei
11.788/2008 que o sistema passou a controlar:

- termo de compromisso: no maximo 2 anos (art. 11) e aviso de fim de contrato;
- recesso: 2,5 dias por mes completo (art. 13), pedido e aprovacao, e dia de
  recesso aprovado nao conta como falta;
- relatorio de atividades do semestre (art. 9o, VII): o estagiario registra,
  o gestor avalia e valida, o estagiario da ciencia, e o semestre fecha.

O "hoje" das rotas e fixado com monkeypatch, como em test_entrega3.py.

Rodar com:
    pytest testes/test_estagio.py -v
"""

from datetime import date

import api.rotas.estagio as rota_estagio
import api.rotas.painel as rota_painel
from testes.conftest import entrar, novo_estagiario, novo_gestor


def _hoje(monkeypatch, texto):
    dia = date.fromisoformat(texto)
    monkeypatch.setattr(rota_estagio, "_hoje", lambda: dia)
    monkeypatch.setattr(rota_painel, "_hoje", lambda: dia)


def _carla_e_lucas(cliente, inicio="2026-01-10", fim="2026-12-20"):
    """Carla cadastra o termo do Lucas. Termina logado como Lucas."""
    carla = novo_gestor(cliente, "Carla")
    lucas = novo_estagiario(cliente, "Lucas", carla["id"])
    entrar(cliente, "carla@teste.dev")
    resposta = cliente.put(f"/estagio/{lucas['id']}/termo", json={
        "data_inicio": inicio, "data_fim": fim, "instituicao_ensino": "UniAnchieta",
        "curso": "Ciência da Computação",
    })
    assert resposta.status_code == 200, resposta.text
    entrar(cliente, "lucas@teste.dev")
    return carla, lucas


# --- termo de compromisso (art. 11) -------------------------------------------------


def test_termo_nao_passa_de_dois_anos_salvo_pessoa_com_deficiencia(cliente):
    carla = novo_gestor(cliente)
    lucas = novo_estagiario(cliente, "Lucas", carla["id"])
    url = f"/estagio/{lucas['id']}/termo"
    termo = {"data_inicio": "2026-01-10", "data_fim": "2028-03-01"}

    assert cliente.put(url, json=termo).status_code == 403  # o estagiario nao edita o proprio termo
    entrar(cliente, "carla@teste.dev")
    recusado = cliente.put(url, json=termo)
    assert recusado.status_code == 409 and "2 anos" in recusado.json()["detail"]
    assert cliente.put(url, json={**termo, "pessoa_com_deficiencia": True}).status_code == 200


def test_painel_do_gestor_avisa_contrato_perto_do_fim(cliente, monkeypatch):
    _hoje(monkeypatch, "2026-12-01")
    carla, lucas = _carla_e_lucas(cliente, fim="2026-12-20")
    assert cliente.get(f"/estagio/{lucas['id']}").json()["contrato"]["vencendo"] is True

    entrar(cliente, "carla@teste.dev")
    painel = cliente.get(f"/painel/gestor/{carla['id']}").json()
    assert painel["contratos_vencendo"] == 1
    assert painel["equipe"][0]["dias_para_fim_contrato"] == 19


# --- recesso (art. 13) -------------------------------------------------------------


def test_recesso_e_proporcional_aos_meses_de_estagio(cliente, monkeypatch):
    """De 10/01 a 20/10: 9 meses completos x 2,5 = 22 dias (arredonda para baixo)."""
    _hoje(monkeypatch, "2026-10-20")
    _, lucas = _carla_e_lucas(cliente)
    recesso = cliente.get(f"/estagio/{lucas['id']}").json()["recesso"]
    assert recesso["meses_completos"] == 9
    assert recesso["direito"] == 22
    assert recesso["disponiveis"] == 22


def test_pedido_de_recesso_respeita_saldo_datas_e_choque(cliente, monkeypatch):
    _hoje(monkeypatch, "2026-10-20")
    _, lucas = _carla_e_lucas(cliente)

    def pedir(inicio, fim):
        return cliente.post("/estagio/recessos", json={"data_inicio": inicio, "data_fim": fim})

    assert pedir("2026-11-01", "2026-11-30").status_code == 409   # 30 dias > 22 disponiveis
    assert pedir("2026-10-01", "2026-10-05").status_code == 409   # no passado
    assert pedir("2026-11-10", "2026-11-14").status_code == 201   # 5 dias
    choque = pedir("2026-11-14", "2026-11-16")
    assert choque.status_code == 409 and "periodo" in choque.json()["detail"]

    recesso = cliente.get(f"/estagio/{lucas['id']}").json()["recesso"]
    assert recesso["pendentes"] == 5 and recesso["disponiveis"] == 17


def test_so_o_gestor_responsavel_decide_o_recesso(cliente, monkeypatch):
    _hoje(monkeypatch, "2026-10-20")
    _carla_e_lucas(cliente)
    pedido = cliente.post("/estagio/recessos", json={"data_inicio": "2026-11-10", "data_fim": "2026-11-12"}).json()
    url = f"/estagio/recessos/{pedido['id']}"

    assert cliente.patch(url, json={"status": "aprovado"}).status_code == 403  # o proprio Lucas
    entrar(cliente, "carla@teste.dev")
    novo_gestor(cliente, "Marcos")
    assert cliente.patch(url, json={"status": "aprovado"}).status_code == 403  # gestor de outra equipe

    entrar(cliente, "carla@teste.dev")
    assert [p["id"] for p in cliente.get("/estagio/recessos/pendentes").json()] == [pedido["id"]]
    aprovado = cliente.patch(url, json={"status": "aprovado"})
    assert aprovado.status_code == 200 and aprovado.json()["gestor_nome"] == "Carla"
    assert cliente.patch(url, json={"status": "rejeitado"}).status_code == 409  # ja respondido


def test_recesso_aprovado_nao_conta_como_falta(cliente, monkeypatch):
    """Setembro/2026 tem 22 dias uteis. O Lucas trabalhou no dia 1 e tirou
    recesso de 14 a 18 (5 dias uteis): sobram 16 faltas, e nao 21."""
    _hoje(monkeypatch, "2026-08-20")
    _, lucas = _carla_e_lucas(cliente, inicio="2026-01-05")
    cliente.post("/registros", json={
        "estagiario_id": lucas["id"], "data": "2026-09-01", "entrada": "09:00",
        "saida_almoco": "12:00", "retorno_almoco": "13:00", "saida": "16:00",
    })
    pedido = cliente.post("/estagio/recessos", json={"data_inicio": "2026-09-14", "data_fim": "2026-09-18"}).json()
    entrar(cliente, "carla@teste.dev")
    cliente.patch(f"/estagio/recessos/{pedido['id']}", json={"status": "aprovado"})

    relatorio = cliente.get(f"/relatorio/{lucas['id']}", params={"mes": 9, "ano": 2026}).json()
    assert relatorio["faltas"] == 16
    assert len(relatorio["datas_recesso"]) == 5


# --- relatorio de atividades (art. 9o, VII) -------------------------------------------


def test_relatorio_semestral_avaliado_validado_e_com_ciencia(cliente, monkeypatch):
    _hoje(monkeypatch, "2026-10-20")
    _, lucas = _carla_e_lucas(cliente)
    cliente.post("/registros", json={
        "estagiario_id": lucas["id"], "data": "2026-10-05", "entrada": "09:00",
        "saida_almoco": "12:00", "retorno_almoco": "13:00", "saida": "16:00",
    })
    assert cliente.post("/estagio/atividades", json={"data": "2026-10-05", "descricao": "Modelagem do banco de horas"}).status_code == 201
    assert cliente.post("/estagio/atividades", json={"data": "2026-10-30", "descricao": "Atividade no futuro"}).status_code == 409
    url = f"/estagio/{lucas['id']}/semestre/2026/2"
    assert cliente.post(f"{url}/ciencia").status_code == 409  # ainda nao validado
    assert cliente.put(url, json={"avaliacao": "Bom", "validar": True}).status_code == 403  # estagiario

    entrar(cliente, "carla@teste.dev")
    assert cliente.put(url, json={"avaliacao": "", "validar": True}).status_code == 409  # sem avaliacao
    validado = cliente.put(url, json={"avaliacao": "Entregou tudo no prazo.", "validar": True}).json()
    assert validado["status"] == "validado" and validado["gestor_nome"] == "Carla"
    assert validado["horas_trabalhadas"] == 6.0 and len(validado["atividades"]) == 1

    entrar(cliente, "lucas@teste.dev")
    fechado = cliente.post("/estagio/atividades", json={"data": "2026-10-06", "descricao": "Depois de fechar"})
    assert fechado.status_code == 409  # semestre validado esta fechado
    ciente = cliente.post(f"{url}/ciencia").json()
    assert ciente["ciente_em"] is not None

    pdf = cliente.get(f"{url}/pdf")
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"


def test_semestre_sem_atividade_nao_pode_ser_validado(cliente, monkeypatch):
    _hoje(monkeypatch, "2026-10-20")
    _, lucas = _carla_e_lucas(cliente)
    entrar(cliente, "carla@teste.dev")
    resposta = cliente.put(f"/estagio/{lucas['id']}/semestre/2026/2", json={"avaliacao": "Ok", "validar": True})
    assert resposta.status_code == 409
