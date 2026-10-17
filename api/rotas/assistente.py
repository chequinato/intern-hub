"""Rota de /assistente - o assistente de IA que responde duvidas sobre saldo e cenarios.

Modulo dono: Arthur Linhares (Desenvolvedor 5 - secao 3.5).

Rota fina, igual as demais (README, secao 7): valida que o estagiario
existe (mesmo molde de api/rotas/saldo.py e api/rotas/simulacoes.py) e
delega toda a logica pra servicos/assistente.py. Nao faz HTTP pra
nenhuma outra rota - servico chama servico direto.

Entrega 3 (login, Miguel): so o proprio estagiario conversa com o
assistente sobre os dados dele.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.permissoes import exigir_o_proprio_estagiario, usuario_logado
from api.schemas import AssistentePerguntaRequest, AssistentePerguntaResponse
from banco.conexao import get_session
from modelos import Usuario
from servicos.assistente import responder_pergunta

router = APIRouter(prefix="/assistente", tags=["Assistente"])


@router.post(
    "/perguntar",
    response_model=AssistentePerguntaResponse,
    summary="Pergunta ao assistente de IA sobre saldo e cenarios hipoteticos",
)
def perguntar(
    dados: AssistentePerguntaRequest,
    usuario: Usuario = Depends(usuario_logado),
    session: Session = Depends(get_session),
) -> AssistentePerguntaResponse:
    """Recebe a pergunta, chama o servico e devolve a resposta pronta.

    responder_pergunta nunca levanta excecao por causa da OpenAI - ela
    trata erro de API sozinha e devolve uma mensagem de aviso como
    resposta normal. O unico jeito de dar erro aqui e o estagiario nao
    existir, e essa checagem ja acontece antes de chamar o servico.
    """
    exigir_o_proprio_estagiario(dados.estagiario_id, usuario, session)

    resposta = responder_pergunta(dados.pergunta, dados.estagiario_id, session)
    return AssistentePerguntaResponse(resposta=resposta)
