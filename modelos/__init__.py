"""Modelos (tabelas) do InternHub.

Importar este pacote registra todas as classes em Base.metadata - e por isso
que banco/conexao.py faz `import modelos` dentro de criar_tabelas().

Quem adicionar um modelo novo (feriado.py, solicitacao_ajuste.py) precisa
importa-lo aqui tambem, senao a tabela nao e criada.
"""

from modelos.configuracao import Configuracao
from modelos.estagiario import Estagiario
from modelos.gestor import Gestor
from modelos.registro_ponto import RegistroPonto

# Pietro (3.3):          from modelos.feriado import Feriado
# Pedro Henrique (3.4):  from modelos.solicitacao_ajuste import SolicitacaoAjuste

__all__ = ["Configuracao", "Estagiario", "Gestor", "RegistroPonto"]
