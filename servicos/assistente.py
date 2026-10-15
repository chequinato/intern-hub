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
from datetime import date

from openai import OpenAI
from sqlalchemy.orm import Session

from modelos import Estagiario
from modelos.configuracao import LIMITE_ALERTA_NEGATIVO_PADRAO
from servicos.painel import resumo_estagiario
from servicos.saldo import calcular_saldo_acumulado, verificar_alerta
from servicos.simulador import simular_cenario

# Provedor da IA (Entrega 3, Miguel). A OpenAI nao tem cota gratuita na API
# (precisa de cartao e credito minimo), entao o padrao passou a ser o Groq,
# que tem plano gratuito e aceita a mesma biblioteca da OpenAI - so muda o
# endereco e o modelo. Para usar outro, basta trocar IA_PROVEDOR no .env.
PROVEDORES_IA = {
    # provedor: (endereco da API compativel com a OpenAI, modelo padrao)
    # No Groq, os modelos Llama sairam da lista em 2026; o gpt-oss-120b (modelo
    # aberto da OpenAI, rodando no Groq) respondeu melhor em portugues nos testes.
    "groq": ("https://api.groq.com/openai/v1", "openai/gpt-oss-120b"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-2.5-flash"),
    "openai": (None, "gpt-4o-mini"),  # None = endereco padrao da biblioteca
}
# Limite de tamanho da resposta. Era 300; subiu para 1000 porque o
# gpt-oss "pensa" antes de responder e esse raciocinio conta no limite -
# com 300, respostas mais longas vinham cortadas no meio. No Groq e gratuito.
MAX_TOKENS_RESPOSTA = 1000

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

    contexto += _contexto_do_painel(estagiario, session)

    if _pergunta_pede_simulacao(pergunta):
        contexto += _contexto_simulacao(pergunta, estagiario_id, session)

    return contexto


def _contexto_do_painel(estagiario: Estagiario, session: Session) -> str:
    """Semana, pendencias, pedidos e meses anteriores (Entrega 3, Miguel).

    Reaproveita o mesmo resumo do painel inicial (servicos/painel.py), entao
    o assistente responde com exatamente os numeros que a tela mostra - e
    passa a dar conta de perguntas como "tenho alguma pendencia?" ou "como
    foi meu mes passado?", que antes ficavam sem dado nenhum.
    """
    resumo = resumo_estagiario(estagiario, date.today(), session)

    texto = (
        f"- Horas nesta semana: {resumo['horas_semana']:.2f}h "
        f"(limite legal: {resumo['limite_maximo_semanal']:.0f}h por semana, "
        f"{resumo['limite_maximo_diario']:.0f}h por dia)\n"
        f"- Pedidos de ajuste esperando o gestor: {resumo['pedidos_pendentes']}\n"
    )

    if resumo["pendencias"]:
        dias = ", ".join(p["data"].strftime("%d/%m") for p in resumo["pendencias"])
        texto += f"- Dias com pendência de almoço (fora do saldo até corrigir): {dias}\n"
    else:
        texto += "- Nenhum dia com pendência de almoço\n"

    if resumo["aviso_vencimento"]:
        texto += f"- Aviso de vencimento: {resumo['aviso_vencimento']}\n"

    for mes in resumo["tendencia"][-3:]:
        texto += (
            f"- Mês {mes['mes']:02d}/{mes['ano']}: {mes['horas_trabalhadas']:.1f}h "
            f"em {mes['dias_completos']} dia(s) completos, saldo do mês "
            f"{mes['saldo_mes']:+.2f}h\n"
        )
    return texto


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


def configuracao_ia() -> tuple[str, str | None, str | None, str]:
    """Le do .env qual provedor usar: (provedor, chave, endereco, modelo).

    IA_PROVEDOR (groq, gemini ou openai) e IA_CHAVE escolhem o provedor;
    IA_MODELO troca o modelo se precisar. Quem ja tinha so OPENAI_API_KEY
    no .env (como na Entrega 2) continua funcionando com a OpenAI.
    """
    provedor = (os.getenv("IA_PROVEDOR") or "groq").strip().lower()
    chave = os.getenv("IA_CHAVE")
    if not chave and os.getenv("OPENAI_API_KEY"):
        provedor, chave = "openai", os.getenv("OPENAI_API_KEY")
    if provedor not in PROVEDORES_IA:
        provedor = "groq"
    endereco, modelo_padrao = PROVEDORES_IA[provedor]
    return provedor, chave, endereco, os.getenv("IA_MODELO") or modelo_padrao


def resposta_modo_demonstracao(contexto: str) -> str:
    """Resposta sem IA, para quando nao ha chave configurada.

    O enunciado pede um "modo de demonstracao" para quem avaliar o sistema
    sem a chave da API. Em vez de so avisar que falta a chave, o assistente
    devolve os mesmos numeros que mandaria para a IA - ja buscados no banco
    pelo _montar_contexto -, so que sem o texto em linguagem natural.
    """
    linhas = [
        linha.strip()
        for linha in contexto.splitlines()
        # A primeira linha ("Dados atuais de ...") e as instrucoes para a IA
        # entre parenteses nao interessam para quem le.
        if linha.strip() and not linha.startswith("Dados atuais") and not linha.strip().startswith("(")
    ]
    return (
        "Modo demonstração (sem IA configurada). Estes são os seus números agora:\n"
        + "\n".join(linhas)
        + "\n\nPara respostas em linguagem natural, coloque IA_CHAVE no .env (veja o .env.example)."
    )


def _perguntar_ia(pergunta: str, contexto: str) -> str:
    provedor, chave, endereco, modelo = configuracao_ia()
    if not chave:
        return resposta_modo_demonstracao(contexto)

    # Cliente instanciado aqui dentro (não no topo do módulo) pra não
    # quebrar o import se a chave ainda não estiver setada - por exemplo,
    # durante a coleta de testes do pytest.
    cliente = OpenAI(api_key=chave, base_url=endereco)

    prompt_sistema = (
        "Você é o assistente do InternHub, sistema de banco de horas de "
        "estágio. Responda em português, em poucas frases. Use SOMENTE "
        "os dados abaixo — nunca invente número. Se faltar informação "
        "pra responder, diga isso claramente. Escreva em texto simples, "
        "sem markdown (nada de asteriscos nem listas).\n\n" + contexto
    )

    try:
        resposta = cliente.chat.completions.create(
            model=modelo,
            max_tokens=MAX_TOKENS_RESPOSTA,
            temperature=0.3,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": pergunta},
            ],
        )
        return resposta.choices[0].message.content.strip()

    except Exception as erro:
        print(f"[assistente] erro ao chamar a IA ({provedor}): {erro}")
        return (
            "Não consegui falar com o assistente de IA agora — pode ser "
            "instabilidade da API ou de conexão. Seus dados de saldo "
            "continuam corretos no sistema; tente novamente em instantes."
        )
