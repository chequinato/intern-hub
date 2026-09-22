"""
servicos/assistente.py

Assistente de IA (funcionalidade 11 do README) - modulo dono: Arthur
Linhares (Desenvolvedor 5, secao 3.5).

Regra de ouro do projeto (README, secao 7 - "Sobre o assistente"): a IA
NUNCA calcula saldo ou simulacao sozinha. Esta funcao so busca numeros ja
calculados pelos servicos existentes - servicos/saldo.py e
servicos/simulador.py, chamados direto (nao via HTTP: dentro da propria
API, servico chama servico) - e pede pra OpenAI transformar isso em texto.
A IA e instruida a nunca inventar dado que nao esteja no contexto.

Assinaturas conferidas contra o codigo real (api/rotas/saldo.py,
api/rotas/simulacoes.py, api/rotas/relatorio.py e api/schemas.py):

  - calcular_saldo_acumulado(estagiario_id, session) -> float (horas;
    negativo = deficit). Confirmado em relatorio.py.
  - verificar_alerta(saldo_acumulado, limite_alerta_negativo) -> bool.
    Recebe DOIS argumentos. Confirmado em api/rotas/saldo.py.
  - simular_cenario(estagiario_id, dias_falta, horas_atraso, session) ->
    dict com "saldo_atual", "saldo_projetado" e "impacto_horas" (floats).
    Confirmado em api/rotas/simulacoes.py + SimulacaoResponse.

Nao vi servicos/saldo.py nem servicos/simulador.py em si (so quem os
chama), mas as assinaturas batem em varios lugares (rota + schema +
relatorio.py) - risco residual baixo.
"""

import os
import re

from openai import OpenAI
from sqlalchemy.orm import Session

from modelos import Estagiario
from modelos.configuracao import LIMITE_ALERTA_NEGATIVO_PADRAO
from servicos.saldo import calcular_saldo_acumulado, verificar_alerta
from servicos.simulador import simular_cenario

MODELO_OPENAI = "gpt-4o-mini"  # decisao fechada no README, secao 11
MAX_TOKENS_RESPOSTA = 300  # mantem contexto e custo baixos (README, secao 9 - riscos)

_PALAVRAS_FALTA = ("faltar", "falta", "faltas")
_PALAVRAS_ATRASO = ("atraso", "atrasar", "atrasado", "atrasada")
_PALAVRAS_CENARIO = _PALAVRAS_FALTA + _PALAVRAS_ATRASO + (
    "cenário", "cenario", "simular", "simulação", "simulacao", "e se",
)


def responder_pergunta(pergunta: str, estagiario_id: int, session: Session) -> str:
    """Ponto de entrada do assistente.

    A rota (api/rotas/assistente.py, ainda por vir) chama esta funcao
    direto - nunca faz um HTTP request pra outra rota da propria API por
    dentro.

    Segue o mesmo padrao de api/rotas/saldo.py e api/rotas/simulacoes.py:
    o ideal e a ROTA ja ter checado que o estagiario existe antes de
    chamar esta funcao. Mesmo assim ela se protege sozinha e levanta
    ValueError se o id nao existir, para o caso de ser chamada direto
    (ex: em teste) sem passar pela rota.
    """
    try:
        contexto = _montar_contexto(pergunta, estagiario_id, session)
    except ValueError:
        raise  # estagiario nao encontrado: quem decide o status HTTP e a rota
    except Exception as erro:
        print(f"[assistente] erro ao buscar dados do estagiario {estagiario_id}: {erro}")
        return (
            "Não consegui buscar seus dados agora pra responder com segurança. "
            "Tente de novo em instantes."
        )

    return _perguntar_ia(pergunta, contexto)


def _montar_contexto(pergunta: str, estagiario_id: int, session: Session) -> str:
    """Busca saldo (+ simulação, se pedido) e devolve tudo em texto pronto pra IA ler."""
    estagiario = session.query(Estagiario).filter_by(id=estagiario_id).first()
    if estagiario is None:
        raise ValueError(f"Estagiario {estagiario_id} nao encontrado.")

    limite = (
        estagiario.configuracao.limite_alerta_negativo
        if estagiario.configuracao is not None
        else LIMITE_ALERTA_NEGATIVO_PADRAO
    )

    saldo_atual = calcular_saldo_acumulado(estagiario_id, session)
    em_alerta = verificar_alerta(saldo_atual, limite)

    sinal = "positivo (crédito)" if saldo_atual >= 0 else "negativo (déficit)"
    situacao = "em alerta, abaixo do limite negativo" if em_alerta else "dentro do esperado"

    contexto = (
        f"Dados atuais de {estagiario.nome} (estagiario_id={estagiario_id}):\n"
        f"- Saldo acumulado de horas: {saldo_atual:.2f}h ({sinal})\n"
        f"- Situação do saldo: {situacao} (limite de alerta: {limite:.1f}h)\n"
    )

    if estagiario.configuracao is not None:
        contexto += (
            f"- Meta diária: {estagiario.configuracao.meta_horas_diaria:.1f}h | "
            f"Meta semanal: {estagiario.configuracao.meta_horas_semanal:.1f}h\n"
        )

    if _pergunta_pede_simulacao(pergunta):
        contexto += _contexto_simulacao(pergunta, estagiario_id, session)

    return contexto


def _contexto_simulacao(pergunta: str, estagiario_id: int, session: Session) -> str:
    """Bloco extra de contexto quando a pergunta parece pedir um cenário hipotético."""
    dias_falta = _extrair_dias_falta(pergunta)
    horas_atraso = _extrair_horas_atraso(pergunta)

    if dias_falta == 0 and horas_atraso == 0:
        return (
            "\n(A pergunta parece pedir uma simulação, mas sem dizer quantos "
            "dias de falta ou horas de atraso - peça pra pessoa detalhar o "
            "cenário, se fizer sentido.)\n"
        )

    try:
        projecao = simular_cenario(estagiario_id, dias_falta, horas_atraso, session)
        return (
            f"\nSimulação hipotética ({dias_falta} dia(s) de falta, "
            f"{horas_atraso:.1f}h de atraso somados - sem alterar o banco "
            "de verdade):\n"
            f"- Saldo atual considerado: {projecao['saldo_atual']:.2f}h\n"
            f"- Saldo projetado: {projecao['saldo_projetado']:.2f}h\n"
            f"- Impacto: {projecao['impacto_horas']:+.2f}h\n"
        )
    except Exception as erro:
        print(f"[assistente] simulação indisponível: {erro}")
        return "\n(Não foi possível simular o cenário pedido agora.)\n"


def _pergunta_pede_simulacao(pergunta: str) -> bool:
    pergunta_lower = pergunta.lower()
    return any(palavra in pergunta_lower for palavra in _PALAVRAS_CENARIO)


def _extrair_dias_falta(pergunta: str) -> int:
    """1 se falar em falta sem número junto; 0 se nem tocar no assunto."""
    pergunta_lower = pergunta.lower()
    numero = re.search(r"(\d+)\s*dia", pergunta_lower)
    if numero:
        return int(numero.group(1))
    return 1 if any(palavra in pergunta_lower for palavra in _PALAVRAS_FALTA) else 0


def _extrair_horas_atraso(pergunta: str) -> float:
    """1.0 se falar em atraso sem número junto; 0.0 se nem tocar no assunto."""
    pergunta_lower = pergunta.lower()
    numero = re.search(r"(\d+(?:[.,]\d+)?)\s*h", pergunta_lower)
    if numero:
        return float(numero.group(1).replace(",", "."))
    return 1.0 if any(palavra in pergunta_lower for palavra in _PALAVRAS_ATRASO) else 0.0


def _perguntar_ia(pergunta: str, contexto: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            "O assistente de IA não está configurado neste ambiente "
            "(falta OPENAI_API_KEY no .env)."
        )

    # Cliente instanciado aqui dentro (não no topo do módulo) pra não
    # quebrar o import se a chave ainda não estiver setada - por exemplo,
    # durante a coleta de testes do pytest.
    cliente = OpenAI(api_key=api_key)

    prompt_sistema = (
        "Você é o assistente do InternHub, sistema de banco de horas de "
        "estágio. Responda em português, em poucas frases. Use SOMENTE "
        "os dados abaixo — nunca invente número. Se faltar informação "
        "pra responder, diga isso claramente.\n\n" + contexto
    )

    try:
        resposta = cliente.chat.completions.create(
            model=MODELO_OPENAI,
            max_tokens=MAX_TOKENS_RESPOSTA,
            temperature=0.3,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": pergunta},
            ],
        )
        return resposta.choices[0].message.content.strip()

    except Exception as erro:
        print(f"[assistente] erro ao chamar a OpenAI: {erro}")
        return (
            "Não consegui falar com o assistente de IA agora — pode ser "
            "instabilidade da API ou de conexão. Seus dados de saldo "
            "continuam corretos no sistema; tente novamente em instantes."
        )
