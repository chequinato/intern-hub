"""testes/test_entrega3.py

Testes das rotas acrescentadas na Entrega 3: ponto rapido, configuracao,
paineis, tendencia mes a mes e remocao de feriado. Usam o mesmo fixture
`cliente` (banco em memoria) de testes/conftest.py.

A hora e o dia do servidor sao fixados com monkeypatch nas funcoes _agora()
e _hoje() das rotas - sem isso, o resultado dependeria do relogio de quem
roda o teste.

Rodar com:
    pytest testes/test_entrega3.py -v
"""

from datetime import date, datetime

import api.rotas.painel as rota_painel
import api.rotas.ponto as rota_ponto


def _relogio(monkeypatch, texto):
    """Fixa a hora que a rota de ponto enxerga ("2026-10-13 09:00")."""
    momento = datetime.strptime(texto, "%Y-%m-%d %H:%M")
    monkeypatch.setattr(rota_ponto, "_agora", lambda: momento)


def _estagiario(cliente, nome="Lucas", gestor_id=None):
    return cliente.post("/estagiarios", json={"nome": nome, "gestor_id": gestor_id}).json()


def _dia(cliente, estagiario_id, data, saida="16:00", almoco=True):
    payload = {"estagiario_id": estagiario_id, "data": data, "entrada": "09:00", "saida": saida}
    if almoco:
        payload.update(saida_almoco="12:00", retorno_almoco="13:00")
    return cliente.post("/registros", json=payload).json()


# --- ponto rapido -----------------------------------------------------------


def test_ponto_rapido_marca_os_quatro_horarios_na_ordem(cliente, monkeypatch):
    """Quatro cliques no mesmo dia viram entrada, almoco, retorno e saida."""
    estagiario = _estagiario(cliente)
    url = f"/ponto/{estagiario['id']}"

    esperado = [
        ("09:00", "entrada", "saida_almoco"),
        ("12:00", "saida_almoco", "retorno_almoco"),
        ("13:00", "retorno_almoco", "saida"),
        ("16:30", "saida", None),
    ]
    for hora, campo, proxima in esperado:
        _relogio(monkeypatch, f"2026-10-13 {hora}")
        resposta = cliente.post(url)
        assert resposta.status_code == 201, resposta.text
        corpo = resposta.json()
        assert corpo["campo_marcado"] == campo
        assert corpo["proxima_marcacao"] == proxima

    assert corpo["registro"]["horas_trabalhadas"] == 6.5
    assert corpo["registro"]["pendencia"] is False


def test_ponto_rapido_recusa_dia_fechado_com_409(cliente, monkeypatch):
    estagiario = _estagiario(cliente)
    url = f"/ponto/{estagiario['id']}"
    _relogio(monkeypatch, "2026-10-13 09:00")
    cliente.post(url)
    _relogio(monkeypatch, "2026-10-13 15:00")
    assert cliente.post(url, json={"marcacao": "saida"}).status_code == 201

    _relogio(monkeypatch, "2026-10-13 15:30")
    resposta = cliente.post(url)
    assert resposta.status_code == 409
    assert "encerrado" in resposta.json()["detail"]


def test_ponto_rapido_sem_almoco_fecha_o_dia_como_pendencia(cliente, monkeypatch):
    """Marcar a saida direto e permitido, mas o dia fica com pendencia."""
    estagiario = _estagiario(cliente)
    url = f"/ponto/{estagiario['id']}"
    _relogio(monkeypatch, "2026-10-13 09:00")
    cliente.post(url)
    _relogio(monkeypatch, "2026-10-13 15:00")
    corpo = cliente.post(url, json={"marcacao": "saida"}).json()
    assert corpo["registro"]["pendencia"] is True


def test_ponto_rapido_no_mesmo_minuto_da_entrada_e_recusado(cliente, monkeypatch):
    """Sair para o almoco no mesmo minuto da entrada quebra a ordem dos horarios."""
    estagiario = _estagiario(cliente)
    url = f"/ponto/{estagiario['id']}"
    _relogio(monkeypatch, "2026-10-13 09:00")
    cliente.post(url)
    resposta = cliente.post(url)
    assert resposta.status_code == 409
    assert "depois da entrada" in resposta.json()["detail"]


# --- configuracao -----------------------------------------------------------


def test_alterar_meta_muda_o_saldo_na_hora(cliente):
    """Com meta de 6h, um dia de 6h da saldo zero; com meta de 5h, +1h."""
    estagiario = _estagiario(cliente)
    _dia(cliente, estagiario["id"], "2026-10-12")
    assert cliente.get(f"/saldo/{estagiario['id']}").json()["saldo_acumulado"] == 0.0

    resposta = cliente.patch(
        f"/estagiarios/{estagiario['id']}/configuracao", json={"meta_horas_diaria": 5}
    )
    assert resposta.status_code == 200
    assert resposta.json()["meta_horas_diaria"] == 5
    # So o campo enviado mudou: o limite legal continua no padrao.
    assert resposta.json()["limite_maximo_diario"] == 6
    assert cliente.get(f"/saldo/{estagiario['id']}").json()["saldo_acumulado"] == 1.0


def test_configuracao_recusa_meta_negativa_com_422(cliente):
    estagiario = _estagiario(cliente)
    resposta = cliente.patch(
        f"/estagiarios/{estagiario['id']}/configuracao", json={"meta_horas_diaria": -2}
    )
    assert resposta.status_code == 422


# --- tendencia e paineis ----------------------------------------------------


def test_tendencia_agrupa_por_mes_e_acumula(cliente):
    """Setembro: 2 dias de 7h (+2h). Outubro: 1 dia de 5h (-1h). Acumulado: +1h."""
    estagiario = _estagiario(cliente)
    _dia(cliente, estagiario["id"], "2026-09-28", saida="17:00")
    _dia(cliente, estagiario["id"], "2026-09-29", saida="17:00")
    _dia(cliente, estagiario["id"], "2026-10-01", saida="15:00")

    tendencia = cliente.get(f"/relatorio/{estagiario['id']}/tendencia").json()
    assert [(m["mes"], m["saldo_mes"], m["saldo_acumulado"]) for m in tendencia] == [
        (9, 2.0, 2.0),
        (10, -1.0, 1.0),
    ]
    # O ultimo acumulado bate com o saldo do banco de horas.
    assert cliente.get(f"/saldo/{estagiario['id']}").json()["saldo_acumulado"] == 1.0


def test_painel_do_estagiario_mostra_semana_e_pendencias(cliente, monkeypatch):
    monkeypatch.setattr(rota_painel, "_hoje", lambda: date(2026, 10, 14))
    estagiario = _estagiario(cliente)
    _dia(cliente, estagiario["id"], "2026-10-12")                # segunda, 6h
    _dia(cliente, estagiario["id"], "2026-10-13", almoco=False)  # terca, pendencia

    painel = cliente.get(f"/painel/estagiario/{estagiario['id']}").json()
    assert painel["horas_semana"] == 12.0      # 6h + 6h (sem almoco marcado, desconta 1h)
    assert painel["limite_maximo_semanal"] == 30
    assert [p["data"] for p in painel["pendencias"]] == ["2026-10-13"]
    assert painel["pendencias"][0]["campos_faltando"] == ["saida_almoco", "retorno_almoco"]
    assert painel["proxima_marcacao"] == "entrada"  # ainda nao bateu ponto no dia 14


def test_painel_do_gestor_mostra_quem_esta_em_alerta(cliente, monkeypatch):
    """Beatriz com -6h (alerta em -5h) e Lucas com saldo zero."""
    monkeypatch.setattr(rota_painel, "_hoje", lambda: date(2026, 10, 14))
    gestor = cliente.post("/gestores", json={"nome": "Carla"}).json()
    lucas = _estagiario(cliente, "Lucas", gestor["id"])
    beatriz = _estagiario(cliente, "Beatriz", gestor["id"])
    _dia(cliente, lucas["id"], "2026-10-12")
    for dia in ("2026-10-05", "2026-10-06", "2026-10-07"):
        _dia(cliente, beatriz["id"], dia, saida="14:00")  # 4h por dia: -2h cada

    painel = cliente.get(f"/painel/gestor/{gestor['id']}").json()
    assert painel["total_estagiarios"] == 2
    assert painel["em_alerta"] == 1
    linhas = {l["nome"]: l for l in painel["equipe"]}
    assert linhas["Beatriz"]["em_alerta"] is True
    assert linhas["Beatriz"]["saldo_acumulado"] == -6.0
    assert linhas["Lucas"]["em_alerta"] is False


# --- feriados ---------------------------------------------------------------


def test_remover_feriado_devolve_204_e_some_da_lista(cliente):
    feriado = cliente.post("/feriados", json={"data": "2026-10-12", "descricao": "Nossa Senhora"}).json()
    assert cliente.delete(f"/feriados/{feriado['id']}").status_code == 204
    assert cliente.get("/feriados").json() == []
    assert cliente.delete(f"/feriados/{feriado['id']}").status_code == 404
