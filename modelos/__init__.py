"""Modelos (tabelas) do InternHub.

Importar este pacote registra todas as classes em Base.metadata - e por isso
que banco/conexao.py faz `import modelos` dentro de criar_tabelas().

Quem adicionar um modelo novo precisa importa-lo aqui tambem, senao a tabela
nao e criada.
"""

from modelos.chamado import Chamado, MensagemChamado
from modelos.compromisso import Compromisso
from modelos.configuracao import Configuracao
from modelos.cracha import Cracha
from modelos.estagiario import Estagiario
from modelos.feriado import Feriado
from modelos.gestor import Gestor
from modelos.registro_ponto import RegistroPonto
from modelos.solicitacao_ajuste import SolicitacaoAjuste
from modelos.usuario import SessaoLogin, Usuario

__all__ = [
    "Chamado",
    "Compromisso",
    "Configuracao",
    "Cracha",
    "Estagiario",
    "Feriado",
    "Gestor",
    "MensagemChamado",
    "RegistroPonto",
    "SessaoLogin",
    "SolicitacaoAjuste",
    "Usuario",
]
