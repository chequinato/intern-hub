"""Popula o banco com dados de demonstracao.

Serve para quem abre o projeto pela primeira vez (ou para a apresentacao)
ver o sistema com dados, sem precisar cadastrar tudo na mao: um gestor,
dois estagiarios e as ultimas semanas de ponto de um deles - incluindo um
dia com pendencia de almoco e um pedido de ajuste esperando o gestor.

Rodar uma vez, na raiz do projeto, com a API parada ou rodando:
    python popular_demo.py

So roda com o banco vazio: se ja existir algum estagiario, nao mexe em nada.
Para comecar do zero, apague banco/dados.db e rode de novo.

Usa o SQLAlchemy direto (sessao, add_all, commit), sem passar pela API -
e um script de carga, nao uma tela do sistema.
"""

from datetime import date, time, timedelta

from banco.conexao import SessionLocal, criar_tabelas
from modelos import (
    Configuracao,
    Estagiario,
    Feriado,
    Gestor,
    RegistroPonto,
    SolicitacaoAjuste,
)

# Horario de saida de cada dia, em sequencia. Entrada 09:00 e almoco
# 12:00-13:00 em todos: saida 16:00 da as 6h da meta, os outros dao
# credito ou debito - assim o saldo e o grafico nao ficam uma linha reta.
SAIDAS = [
    time(16, 0), time(16, 30), time(15, 30), time(16, 0), time(17, 0),
    time(16, 0), time(15, 0), time(16, 0), time(16, 20), time(16, 0),
    time(15, 40), time(16, 0), time(16, 0), time(16, 30), time(16, 0),
]


def ultimos_dias_uteis(quantidade: int) -> list[date]:
    """Os N dias de semana (seg a sex) anteriores a hoje, do mais antigo ao mais novo."""
    dias = []
    dia = date.today() - timedelta(days=1)
    while len(dias) < quantidade:
        if dia.weekday() < 5:
            dias.append(dia)
        dia = dia - timedelta(days=1)
    dias.reverse()
    return dias


def main() -> None:
    criar_tabelas()
    session = SessionLocal()

    if session.query(Estagiario).count() > 0:
        print("O banco ja tem estagiarios cadastrados - nada foi alterado.")
        session.close()
        return

    gestor = Gestor(nome="Carla Mendes")
    lucas = Estagiario(nome="Lucas Andrade", gestor=gestor)
    lucas.configuracao = Configuracao(meta_horas_diaria=6.0, meta_horas_semanal=30.0)
    beatriz = Estagiario(nome="Beatriz Souza", gestor=gestor)
    beatriz.configuracao = Configuracao(meta_horas_diaria=6.0, meta_horas_semanal=30.0)
    session.add_all([gestor, lucas, beatriz])

    dias = ultimos_dias_uteis(len(SAIDAS) + 1)

    # Um dos dias vira feriado, para o relatorio nao conta-lo como falta.
    session.add(Feriado(data=dias[5], descricao="Feriado de demonstracao"))

    for dia, saida in zip(dias[:-1], SAIDAS):
        if dia == dias[5]:
            continue
        session.add(RegistroPonto(
            estagiario=lucas, data=dia, entrada=time(9, 0),
            saida_almoco=time(12, 0), retorno_almoco=time(13, 0), saida=saida,
        ))

    # Ultimo dia: esqueceu o retorno do almoco (pendencia) e pediu ajuste.
    dia_pendente = RegistroPonto(
        estagiario=lucas, data=dias[-1], entrada=time(8, 30),
        saida_almoco=time(12, 0), retorno_almoco=None, saida=time(16, 30),
    )
    session.add(dia_pendente)
    session.add(SolicitacaoAjuste(
        registro=dia_pendente, estagiario=lucas,
        campo_alterado="retorno_almoco", horario_sugerido=time(13, 0),
        justificativa="Esqueci de bater o retorno do almoco.",
    ))

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print("Dados de demonstracao criados:")
    print("  gestor: Carla Mendes")
    print("  estagiarios: Lucas Andrade (com ponto) e Beatriz Souza (sem ponto)")
    print("  1 pedido de ajuste pendente na fila da Carla")


if __name__ == "__main__":
    main()
