"""testes/test_novidades.py

Testes das funcionalidades novas da Entrega 3 (Miguel): chamados ao gestor,
agenda com a regra do dia de prova (Lei 11.788/2008, art. 10) e o cracha
virtual com verificacao publica pelo QR code.

Rodar com:
    pytest testes/test_novidades.py -v
"""

from datetime import date

import api.rotas.painel as rota_painel
from testes.conftest import entrar, novo_estagiario, novo_gestor, sair_da_conta


def _carla_e_lucas(cliente):
    """Carla e Lucas (na equipe dela). Termina logado como Lucas."""
    carla = novo_gestor(cliente, "Carla")
    lucas = novo_estagiario(cliente, "Lucas", carla["id"])
    return carla, lucas


def _dia(cliente, estagiario_id, data, saida="16:00", entrada="09:00"):
    return cliente.post("/registros", json={
        "estagiario_id": estagiario_id, "data": data, "entrada": entrada,
        "saida_almoco": "12:00", "retorno_almoco": "13:00", "saida": saida,
    }).json()


def _chamado(cliente, titulo="Sem acesso ao e-mail", prioridade="media"):
    return cliente.post("/chamados", json={
        "titulo": titulo, "categoria": "acesso", "prioridade": prioridade,
        "descricao": "Minha senha do e-mail corporativo foi bloqueada.",
    })


def _prova(cliente, data, titulo="Prova de Calculo"):
    return cliente.post("/agenda", json={"titulo": titulo, "tipo": "prova", "data": data})


# --- chamados -----------------------------------------------------------------


def test_chamado_vai_para_o_gestor_e_a_conversa_anda(cliente):
    """Abre -> gestor responde (vira "em andamento") -> resolvido -> fechado."""
    carla, _ = _carla_e_lucas(cliente)
    aberto = _chamado(cliente)
    assert aberto.status_code == 201
    chamado = aberto.json()
    assert chamado["status"] == "aberto"
    assert chamado["gestor_id"] == carla["id"]
    assert [m["autor"] for m in chamado["mensagens"]] == ["estagiario"]

    entrar(cliente, "carla@teste.dev")
    assert [c["id"] for c in cliente.get("/chamados").json()] == [chamado["id"]]
    resposta = cliente.post(f"/chamados/{chamado['id']}/mensagens",
                            json={"texto": "Pedi o desbloqueio para a TI."}).json()
    assert resposta["status"] == "em_andamento"
    assert resposta["ultima_mensagem_de"] == "gestor"

    resolvido = cliente.patch(f"/chamados/{chamado['id']}", json={"status": "resolvido"}).json()
    assert resolvido["status"] == "resolvido" and resolvido["resolvido_em"] is not None

    entrar(cliente, "lucas@teste.dev")
    fechado = cliente.post(f"/chamados/{chamado['id']}/mensagens", json={"texto": "Obrigado!"})
    assert fechado.status_code == 409


def test_andamento_do_chamado_so_vai_para_a_frente(cliente):
    _carla_e_lucas(cliente)
    chamado = _chamado(cliente).json()
    # O estagiario nao muda o andamento:
    assert cliente.patch(f"/chamados/{chamado['id']}", json={"status": "resolvido"}).status_code == 403

    entrar(cliente, "carla@teste.dev")
    assert cliente.patch(f"/chamados/{chamado['id']}", json={"status": "resolvido"}).status_code == 200
    assert cliente.patch(f"/chamados/{chamado['id']}", json={"status": "aberto"}).status_code == 409


def test_sem_gestor_nao_ha_quem_receba_o_chamado(cliente):
    novo_estagiario(cliente, "Lucas")
    resposta = _chamado(cliente)
    assert resposta.status_code == 409
    assert "gestor" in resposta.json()["detail"]


def test_fila_de_chamados_poe_prioridade_alta_primeiro(cliente):
    _carla_e_lucas(cliente)
    _chamado(cliente, "Mouse quebrado", "baixa")
    _chamado(cliente, "Sistema fora do ar", "alta")
    _chamado(cliente, "Duvida no contrato", "media")
    entrar(cliente, "carla@teste.dev")
    titulos = [c["titulo"] for c in cliente.get("/chamados").json()]
    assert titulos == ["Sistema fora do ar", "Duvida no contrato", "Mouse quebrado"]


def test_outro_estagiario_nao_ve_o_chamado(cliente):
    carla, _ = _carla_e_lucas(cliente)
    chamado = _chamado(cliente).json()
    entrar(cliente, "carla@teste.dev")
    novo_estagiario(cliente, "Beatriz", carla["id"])
    assert cliente.get(f"/chamados/{chamado['id']}").status_code == 403
    assert cliente.get("/chamados").json() == []


def test_painel_do_gestor_conta_os_chamados(cliente):
    carla, _ = _carla_e_lucas(cliente)
    _chamado(cliente)
    _chamado(cliente, "Outro problema")
    entrar(cliente, "carla@teste.dev")
    painel = cliente.get(f"/painel/gestor/{carla['id']}").json()
    assert painel["chamados_sem_resposta"] == 2


# --- agenda e dia de prova ------------------------------------------------------


def test_dia_de_prova_cobra_so_metade_da_meta(cliente):
    """Lei 11.788/2008, art. 10: em dia de prova a carga cai pela metade.

    Meta de 6h. Dia 13 (prova): 3h trabalhadas = saldo 0. Dia 14 (normal):
    3h trabalhadas = -3h. Sem a regra, o dia 13 tambem daria -3h.
    """
    _, lucas = _carla_e_lucas(cliente)
    assert _prova(cliente, "2026-10-13").status_code == 201
    _dia(cliente, lucas["id"], "2026-10-13", entrada="10:00", saida="14:00")  # 4h - 1h almoco
    _dia(cliente, lucas["id"], "2026-10-14", entrada="10:00", saida="14:00")

    assert cliente.get(f"/saldo/{lucas['id']}").json()["saldo_acumulado"] == -3.0

    relatorio = cliente.get(f"/relatorio/{lucas['id']}", params={"mes": 10, "ano": 2026}).json()
    dias = {d["data"]: d for d in relatorio["evolucao_diaria"]}
    assert dias["2026-10-13"]["saldo_do_dia"] == 0.0 and dias["2026-10-13"]["dia_de_prova"] is True
    assert dias["2026-10-14"]["saldo_do_dia"] == -3.0
    assert relatorio["datas_provas"] == ["2026-10-13"]
    # A tendencia (group_by no banco) faz a mesma conta.
    assert cliente.get(f"/relatorio/{lucas['id']}/tendencia").json()[-1]["saldo_acumulado"] == -3.0


def test_dia_de_prova_reduz_tambem_o_limite_legal(cliente):
    """Limite de 6h vira 3h na prova: 5h trabalhadas geram o aviso."""
    _, lucas = _carla_e_lucas(cliente)
    _prova(cliente, "2026-10-13")
    registro = _dia(cliente, lucas["id"], "2026-10-13", saida="15:00")  # 6h - 1h = 5h
    assert "3.0h por dia" in registro["aviso_limite_legal"]
    normal = _dia(cliente, lucas["id"], "2026-10-14", saida="15:00")
    assert normal["aviso_limite_legal"] is None


def test_compromisso_com_fim_antes_do_inicio_e_recusado(cliente):
    _carla_e_lucas(cliente)
    resposta = cliente.post("/agenda", json={
        "titulo": "Aula", "tipo": "aula", "data": "2026-10-13", "inicio": "19:00", "fim": "18:00",
    })
    assert resposta.status_code == 422


def test_agenda_exporta_ics_para_o_google_agenda(cliente):
    _, lucas = _carla_e_lucas(cliente)
    _prova(cliente, "2026-10-20", "Prova de Banco de Dados")
    cliente.post("/agenda", json={"titulo": "Reuniao de estagio", "tipo": "reuniao",
                                  "data": "2026-10-21", "inicio": "14:00", "fim": "15:00"})
    resposta = cliente.get(f"/agenda/{lucas['id']}/ics", params={"inicio": "2026-10-01"})
    assert resposta.status_code == 200
    assert "text/calendar" in resposta.headers["content-type"]
    texto = resposta.text
    assert texto.count("BEGIN:VEVENT") == 2
    assert "SUMMARY:[Prova] Prova de Banco de Dados" in texto
    assert "DTSTART;VALUE=DATE:20261020" in texto      # sem horario = dia inteiro
    assert "DTSTART:20261021T140000" in texto


def test_gestor_ve_a_agenda_mas_nao_cadastra_nem_apaga(cliente):
    _, lucas = _carla_e_lucas(cliente)
    prova = _prova(cliente, "2026-10-20").json()
    entrar(cliente, "carla@teste.dev")
    assert len(cliente.get(f"/agenda/{lucas['id']}").json()) == 1
    assert _prova(cliente, "2026-10-21").status_code == 403
    assert cliente.delete(f"/agenda/{prova['id']}").status_code == 403
    entrar(cliente, "lucas@teste.dev")
    assert cliente.delete(f"/agenda/{prova['id']}").status_code == 204


def test_painel_mostra_a_agenda_de_hoje_e_a_meta_reduzida(cliente, monkeypatch):
    monkeypatch.setattr(rota_painel, "_hoje", lambda: date(2026, 10, 13))
    _, lucas = _carla_e_lucas(cliente)
    _prova(cliente, "2026-10-13")
    cliente.post("/agenda", json={"titulo": "Entrega do TCC", "tipo": "entrega", "data": "2026-10-16"})

    painel = cliente.get(f"/painel/estagiario/{lucas['id']}").json()
    assert painel["dia_de_prova_hoje"] is True
    assert painel["meta_hoje"] == 3.0
    assert [c["titulo"] for c in painel["compromissos_hoje"]] == ["Prova de Calculo"]
    assert [c["titulo"] for c in painel["proximos_compromissos"]] == ["Entrega do TCC"]


# --- cracha virtual ---------------------------------------------------------------


def test_cracha_e_verificado_sem_login_e_sem_expor_o_banco_de_horas(cliente):
    _, lucas = _carla_e_lucas(cliente)
    cracha = cliente.get(f"/cracha/{lucas['id']}").json()
    assert cracha["ativo"] is True
    assert cracha["url_verificacao"].endswith(f"/verificar/{cracha['codigo']}")

    sair_da_conta(cliente)  # quem le o QR code na portaria nao tem conta
    verificacao = cliente.get(f"/cracha/verificar/{cracha['codigo']}")
    assert verificacao.status_code == 200
    corpo = verificacao.json()
    assert corpo["nome"] == "Lucas" and corpo["gestor_nome"] == "Carla" and corpo["ativo"] is True
    assert not any("saldo" in chave for chave in corpo)


def test_reemitir_o_cracha_invalida_o_codigo_antigo(cliente):
    _, lucas = _carla_e_lucas(cliente)
    antigo = cliente.get(f"/cracha/{lucas['id']}").json()["codigo"]
    novo = cliente.post(f"/cracha/{lucas['id']}/reemitir").json()["codigo"]
    assert novo != antigo
    assert cliente.get(f"/cracha/verificar/{antigo}").status_code == 404
    assert cliente.get(f"/cracha/verificar/{novo}").status_code == 200


def test_so_o_gestor_desativa_o_cracha(cliente):
    _, lucas = _carla_e_lucas(cliente)
    codigo = cliente.get(f"/cracha/{lucas['id']}").json()["codigo"]
    assert cliente.patch(f"/cracha/{lucas['id']}", json={"ativo": False}).status_code == 403

    entrar(cliente, "carla@teste.dev")
    assert cliente.patch(f"/cracha/{lucas['id']}", json={"ativo": False}).json()["ativo"] is False
    assert cliente.get(f"/cracha/verificar/{codigo}").json()["ativo"] is False


def test_qrcode_do_cracha_e_um_svg(cliente):
    _, lucas = _carla_e_lucas(cliente)
    resposta = cliente.get(f"/cracha/{lucas['id']}/qrcode.svg")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/svg+xml")
    assert resposta.text.lstrip().startswith("<svg") or "<svg" in resposta.text[:200]
