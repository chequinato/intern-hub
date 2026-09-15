"""Calculo de horas trabalhadas em um dia.

Modulo dono: Gustavo Legieri (Desenvolvedor 2 - secao 3.2).

Aqui mora a regra do dia isolado: quantas horas a pessoa trabalhou num
registro, descontando o almoco (minimo 1h, README secao 11), e se aquele
registro esta com pendencia (esqueceu de marcar a saida ou o retorno do
almoco).

Estas funcoes NAO tocam no banco - recebem horarios (objetos datetime.time)
e devolvem numeros/booleanos. Quem le do banco e a camada de rotas; a soma
acumulada por periodo fica em servicos/saldo.py (que usa func.sum()).
"""

from datetime import time

# Intervalo minimo de almoco, em horas (README secao 11 - decisao fechada).
# Mesmo que a pessoa marque um almoco mais curto, descontamos pelo menos 1h:
# e o intervalo minimo obrigatorio.
ALMOCO_MINIMO_HORAS = 1.0


def _time_para_horas(momento: time) -> float:
    """Converte um datetime.time em horas decimais (08:30 -> 8.5)."""
    return momento.hour + momento.minute / 60 + momento.second / 3600


def _intervalo_em_horas(inicio: time, fim: time) -> float:
    """Diferenca fim - inicio em horas decimais.

    Assumimos que entrada e saida sao do mesmo dia (o README fixa o formato
    HH:MM e valida antes de salvar, secao 9). Se por algum motivo o fim vier
    antes do inicio, devolvemos 0 em vez de um numero negativo sem sentido.
    """
    diferenca = _time_para_horas(fim) - _time_para_horas(inicio)
    return max(diferenca, 0.0)


def _desconto_do_almoco(saida_almoco: time | None, retorno_almoco: time | None) -> float:
    """Quanto tempo de almoco descontar do dia, respeitando o minimo de 1h.

    - Almoco marcado por inteiro: desconta o maior valor entre o intervalo
      real e o minimo obrigatorio (1h).
    - Almoco sem marcacao completa: nao da para saber o intervalo real, entao
      aplicamos o minimo obrigatorio. (Esse dia, na pratica, vai cair como
      pendencia - ver verificar_pendencia_almoco.)
    """
    if saida_almoco is None or retorno_almoco is None:
        return ALMOCO_MINIMO_HORAS

    intervalo_real = _intervalo_em_horas(saida_almoco, retorno_almoco)
    return max(intervalo_real, ALMOCO_MINIMO_HORAS)


def calcular_horas_trabalhadas(
    entrada: time,
    saida: time | None,
    saida_almoco: time | None = None,
    retorno_almoco: time | None = None,
) -> float:
    """Horas efetivamente trabalhadas no dia, ja descontado o almoco.

    Formula: (saida - entrada) - almoco, com o almoco valendo no minimo 1h.

    Se ainda nao ha saida (dia em andamento), nao da para fechar a conta:
    devolvemos 0.0. Nunca devolvemos numero negativo.
    """
    if entrada is None or saida is None:
        return 0.0

    bruto = _intervalo_em_horas(entrada, saida)
    almoco = _desconto_do_almoco(saida_almoco, retorno_almoco)
    return round(max(bruto - almoco, 0.0), 2)


def validar_ordem_dos_horarios(
    entrada: time,
    saida: time | None = None,
    saida_almoco: time | None = None,
    retorno_almoco: time | None = None,
) -> str | None:
    """Confere se os horarios de um dia fazem sentido entre si.

    Devolve a mensagem do primeiro problema encontrado, ou None se estiver
    tudo certo. So compara os horarios que vieram preenchidos: um dia com
    almoco faltando (pendencia) continua sendo considerado valido.

    Esta funcao e usada em DOIS lugares, e por isso mora aqui e nao em cada
    um deles: o schema RegistroCreate (api/schemas.py) a chama para barrar um
    registro torto na entrada da API, e o servico de solicitacoes
    (servicos/solicitacao.py, Pedro Henrique) a chama antes de aprovar um
    ajuste - para que uma aprovacao nao deixe o registro em um estado que a
    propria API jamais teria aceitado.
    """
    if saida is not None and saida <= entrada:
        return "a saida precisa ser depois da entrada"

    if saida_almoco is not None and saida_almoco <= entrada:
        return "a saida para o almoco precisa ser depois da entrada"

    if saida_almoco is not None and saida is not None and saida_almoco >= saida:
        return "a saida para o almoco precisa ser antes da saida do expediente"

    if (
        saida_almoco is not None
        and retorno_almoco is not None
        and retorno_almoco <= saida_almoco
    ):
        return "o retorno do almoco precisa ser depois da saida para o almoco"

    if retorno_almoco is not None and saida is not None and retorno_almoco >= saida:
        return "o retorno do almoco precisa ser antes da saida do expediente"

    return None


def verificar_pendencia_almoco(registro) -> bool:
    """Diz se o registro esta pendente por falta de marcacao do almoco.

    Regra do README (secao 7): se, ao fim do expediente (ou seja, com a saida
    ja marcada), faltar a saida OU o retorno do almoco, o dia vira pendencia -
    o sistema sugere abrir uma solicitacao de ajuste em vez de ignorar.

    `registro` pode ser um modelo RegistroPonto ou qualquer objeto com os
    atributos saida, saida_almoco e retorno_almoco.
    """
    saida = getattr(registro, "saida", None)
    saida_almoco = getattr(registro, "saida_almoco", None)
    retorno_almoco = getattr(registro, "retorno_almoco", None)

    # Enquanto a saida nao foi marcada, o dia so esta em andamento - ainda
    # nao e pendencia.
    if saida is None:
        return False

    return saida_almoco is None or retorno_almoco is None
