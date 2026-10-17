"""testes/test_login.py

Testes do login e das regras de acesso (Entrega 3, Miguel): senha em hash,
token que vence e que deixa de valer ao sair, e - o mais importante - cada
pessoa so ve e so faz o que e dela.

O teste test_toda_rota_de_dados_exige_login percorre TODAS as rotas da API
(pela documentacao OpenAPI que o FastAPI gera) e confere que, sem login,
cada uma responde 401 - menos a lista curta de rotas abertas de proposito.
Se alguem criar uma rota nova e esquecer o login, este teste falha.

Rodar com:
    pytest testes/test_login.py -v
"""

import re

from api.app_api import app
from banco.conexao import get_session
from modelos import Usuario
from testes.conftest import SENHA, entrar, novo_estagiario, novo_gestor, sair_da_conta

# Rotas que respondem sem login, e o motivo de cada uma.
ROTAS_ABERTAS = {
    ("GET", "/"),                            # saude: a API esta no ar?
    ("POST", "/auth/entrar"),                # o proprio login
    ("POST", "/estagiarios"),                # cadastro: quem se cadastra ainda nao tem conta
    ("GET", "/gestores"),                    # o cadastro escolhe o gestor nesta lista
    ("POST", "/gestores"),                   # aberto so para o PRIMEIRO gestor (testado abaixo)
    ("GET", "/cracha/verificar/{codigo}"),   # o QR code e lido por quem nao tem conta
}


def _equipe(cliente):
    """Carla com Lucas e Beatriz. Termina logado como Beatriz."""
    carla = novo_gestor(cliente, "Carla")
    lucas = novo_estagiario(cliente, "Lucas", carla["id"])
    beatriz = novo_estagiario(cliente, "Beatriz", carla["id"])
    return carla, lucas, beatriz


def _registro(cliente, estagiario_id, data="2026-10-13", **horarios):
    payload = {"estagiario_id": estagiario_id, "data": data, "entrada": "09:00",
               "saida_almoco": "12:00", "retorno_almoco": "13:00", "saida": "16:00"}
    payload.update(horarios)
    return cliente.post("/registros", json=payload)


# --- login e sessao ---------------------------------------------------------


def test_login_devolve_token_e_quem_esta_logado(cliente):
    carla = novo_gestor(cliente)
    sair_da_conta(cliente)

    corpo = entrar(cliente, "  CARLA@teste.dev ")  # e-mail sem diferenciar maiuscula
    assert corpo["usuario"]["perfil"] == "gestor"
    assert corpo["usuario"]["gestor_id"] == carla["id"]
    eu = cliente.get("/auth/eu").json()
    assert eu["nome"] == "Carla" and eu["email"] == "carla@teste.dev"


def test_senha_errada_e_email_que_nao_existe_dao_a_mesma_resposta(cliente):
    """A tela de login nao pode servir para descobrir quem tem conta."""
    novo_gestor(cliente)
    senha_errada = cliente.post("/auth/entrar", json={"email": "carla@teste.dev", "senha": "errada123"})
    sem_conta = cliente.post("/auth/entrar", json={"email": "ninguem@teste.dev", "senha": "errada123"})
    assert senha_errada.status_code == sem_conta.status_code == 401
    assert senha_errada.json() == sem_conta.json()


def test_senha_fica_gravada_so_em_hash(cliente):
    novo_gestor(cliente)
    session = next(app.dependency_overrides[get_session]())
    usuario = session.query(Usuario).filter_by(email="carla@teste.dev").one()
    assert SENHA not in usuario.senha_hash
    assert usuario.senha_hash.startswith("pbkdf2_sha256$")


def test_sair_invalida_o_token(cliente):
    novo_gestor(cliente)
    assert cliente.get("/auth/eu").status_code == 200
    assert cliente.post("/auth/sair").status_code == 204
    assert cliente.get("/auth/eu").status_code == 401


def test_trocar_senha_derruba_os_outros_logins(cliente):
    novo_gestor(cliente)
    token_antigo = cliente.headers["Authorization"]
    entrar(cliente, "carla@teste.dev")  # segundo login (outro aparelho)

    resposta = cliente.patch("/auth/senha", json={"senha_atual": SENHA, "senha_nova": "nova-senha-123"})
    assert resposta.status_code == 204
    assert cliente.get("/auth/eu").status_code == 200                      # quem trocou continua
    assert cliente.get("/auth/eu", headers={"Authorization": token_antigo}).status_code == 401
    sair_da_conta(cliente)
    entrar(cliente, "carla@teste.dev", "nova-senha-123")


def test_muitas_tentativas_de_login_sao_barradas_com_429(cliente):
    novo_gestor(cliente)
    respostas = [
        cliente.post("/auth/entrar", json={"email": "carla@teste.dev", "senha": f"chute-{n}"}).status_code
        for n in range(12)
    ]
    assert 429 in respostas


def test_email_repetido_devolve_409(cliente):
    novo_estagiario(cliente, "Lucas")
    repetido = cliente.post("/estagiarios", json={
        "nome": "Outro Lucas", "email": "LUCAS@teste.dev", "senha": SENHA,
    })
    assert repetido.status_code == 409


def test_senha_curta_e_recusada_com_422(cliente):
    resposta = cliente.post("/estagiarios", json={"nome": "Lucas", "email": "l@teste.dev", "senha": "123"})
    assert resposta.status_code == 422


# --- toda rota exige login --------------------------------------------------


def test_toda_rota_de_dados_exige_login(cliente):
    """Sem token, toda rota fora de ROTAS_ABERTAS responde 401."""
    sair_da_conta(cliente)
    sem_protecao = []
    for caminho, operacoes in app.openapi()["paths"].items():
        for metodo in operacoes:
            metodo = metodo.upper()
            if (metodo, caminho) in ROTAS_ABERTAS:
                continue
            url = re.sub(r"\{[^}]+\}", "1", caminho)
            resposta = cliente.request(metodo, url, json={})
            if resposta.status_code != 401:
                sem_protecao.append(f"{metodo} {caminho} -> {resposta.status_code}")
    assert sem_protecao == []


# --- cada um ve o que e seu -------------------------------------------------


def test_estagiario_nao_ve_os_dados_de_outro_estagiario(cliente):
    _, lucas, _ = _equipe(cliente)  # logado como Beatriz
    for url in (f"/saldo/{lucas['id']}", f"/registros/{lucas['id']}",
                f"/painel/estagiario/{lucas['id']}", f"/estagiarios/{lucas['id']}",
                f"/agenda/{lucas['id']}", f"/cracha/{lucas['id']}"):
        assert cliente.get(url).status_code == 403, url
    assert [e["nome"] for e in cliente.get("/estagiarios").json()] == ["Beatriz"]


def test_gestor_ve_so_a_propria_equipe(cliente):
    carla, lucas, _ = _equipe(cliente)
    entrar(cliente, "carla@teste.dev")
    marcos = novo_gestor(cliente, "Marcos")  # Carla cadastra o Marcos; logado como Marcos

    assert cliente.get(f"/saldo/{lucas['id']}").status_code == 403
    assert cliente.get(f"/painel/gestor/{carla['id']}").status_code == 403
    assert cliente.get("/estagiarios").json() == []
    assert cliente.get(f"/painel/gestor/{marcos['id']}").status_code == 200

    entrar(cliente, "carla@teste.dev")
    assert {e["nome"] for e in cliente.get("/estagiarios").json()} == {"Lucas", "Beatriz"}
    assert cliente.get(f"/saldo/{lucas['id']}").status_code == 200


def test_gestor_nao_bate_ponto_nem_registra_no_lugar_do_estagiario(cliente):
    _, lucas, _ = _equipe(cliente)
    entrar(cliente, "carla@teste.dev")
    assert cliente.post(f"/ponto/{lucas['id']}").status_code == 403
    assert _registro(cliente, lucas["id"]).status_code == 403


def test_so_o_dono_do_registro_pede_ajuste(cliente):
    _, lucas, _ = _equipe(cliente)
    entrar(cliente, "lucas@teste.dev")
    registro = _registro(cliente, lucas["id"], retorno_almoco=None).json()
    pedido = {"registro_id": registro["id"], "campo_alterado": "retorno_almoco",
              "horario_sugerido": "13:00", "justificativa": "Esqueci de marcar"}

    entrar(cliente, "beatriz@teste.dev")
    assert cliente.post("/solicitacoes", json=pedido).status_code == 403
    entrar(cliente, "carla@teste.dev")
    assert cliente.post("/solicitacoes", json=pedido).status_code == 403
    entrar(cliente, "lucas@teste.dev")
    assert cliente.post("/solicitacoes", json=pedido).status_code == 201


def test_gestor_so_decide_com_o_proprio_id(cliente):
    """Antes do login, qualquer um mandava o gestor_id de qualquer gestor."""
    carla, lucas, _ = _equipe(cliente)
    entrar(cliente, "lucas@teste.dev")
    registro = _registro(cliente, lucas["id"], retorno_almoco=None).json()
    pedido = cliente.post("/solicitacoes", json={
        "registro_id": registro["id"], "campo_alterado": "retorno_almoco",
        "horario_sugerido": "13:00", "justificativa": "Esqueci de marcar",
    }).json()

    decisao = {"status": "aprovado", "gestor_id": carla["id"]}
    # O proprio Lucas tentando aprovar o pedido dele:
    assert cliente.patch(f"/solicitacoes/{pedido['id']}", json=decisao).status_code == 403
    entrar(cliente, "carla@teste.dev")
    assert cliente.patch(f"/solicitacoes/{pedido['id']}", json=decisao).status_code == 200


def test_so_o_gestor_responsavel_altera_a_meta(cliente):
    """Se o estagiario pudesse baixar a propria meta, ganharia saldo sem trabalhar."""
    _, lucas, _ = _equipe(cliente)
    entrar(cliente, "lucas@teste.dev")
    url = f"/estagiarios/{lucas['id']}/configuracao"
    assert cliente.patch(url, json={"meta_horas_diaria": 1}).status_code == 403
    entrar(cliente, "carla@teste.dev")
    assert cliente.patch(url, json={"meta_horas_diaria": 5}).status_code == 200


def test_so_o_primeiro_gestor_se_cadastra_sozinho(cliente):
    """Depois do primeiro, so um gestor logado cadastra outro - senao um
    estagiario criaria um "gestor" para aprovar os proprios ajustes."""
    novo_gestor(cliente, "Carla")
    novo_estagiario(cliente, "Lucas")
    falso = {"nome": "Amigo do Lucas", "email": "amigo@teste.dev", "senha": SENHA}
    assert cliente.post("/gestores", json=falso).status_code == 403   # logado como estagiario
    sair_da_conta(cliente)
    assert cliente.post("/gestores", json=falso).status_code == 403   # sem login
    entrar(cliente, "carla@teste.dev")
    assert cliente.post("/gestores", json=falso).status_code == 201   # gestora logada


def test_estagiario_nao_troca_o_proprio_gestor(cliente):
    carla, lucas, _ = _equipe(cliente)
    entrar(cliente, "lucas@teste.dev")
    assert cliente.patch(f"/estagiarios/{lucas['id']}", json={"gestor_id": None}).status_code == 403
