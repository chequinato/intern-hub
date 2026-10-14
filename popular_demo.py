"""Popula o banco com dados de demonstracao.

Serve para quem abre o projeto pela primeira vez (ou para a apresentacao)
ver o sistema com dados, sem precisar cadastrar tudo na mao:

- 1 gestora (Carla Mendes) com 3 estagiarios:
  - Lucas Andrade: ~3 meses de ponto, saldo positivo, um dia com pendencia
    de almoco e um pedido de ajuste esperando a gestora;
  - Beatriz Souza: dias curtos, saldo abaixo do limite de alerta (-5h);
  - Rafael Lima: dias de 7h nos ultimos dias, acima do limite legal de 6h;
- os feriados nacionais do periodo;
- um pedido aprovado e um rejeitado, para a auditoria ter historico.

Os dias sao contados a partir de hoje (as ultimas semanas uteis), entao a
demonstracao sempre parece recente, nao importa quando o script rodar.

Rodar uma vez, na raiz do projeto, com a API parada ou rodando:
    python popular_demo.py

So roda com o banco vazio: se ja existir algum estagiario, nao mexe em nada.
Para comecar do zero, apague banco/dados.db e rode de novo.

Usa o SQLAlchemy direto (sessao, add_all, commit), sem passar pela API -
e um script de carga, nao uma tela do sistema.
"""

from datetime import date, datetime, time, timedelta

from banco.conexao import SessionLocal, criar_tabelas
from modelos import (
    Configuracao,
    Estagiario,
    Feriado,
    Gestor,
    RegistroPonto,
    SolicitacaoAjuste,
)

# Feriados nacionais de 2026 que podem cair dentro do periodo da demonstracao.
FERIADOS_2026 = {
    date(2026, 4, 21): "Tiradentes",
    date(2026, 5, 1): "Dia do Trabalho",
    date(2026, 6, 4): "Corpus Christi",
    date(2026, 9, 7): "Independência do Brasil",
    date(2026, 10, 12): "Nossa Senhora Aparecida",
    date(2026, 11, 2): "Finados",
    date(2026, 11, 15): "Proclamação da República",
    date(2026, 11, 20): "Dia da Consciência Negra",
    date(2026, 12, 25): "Natal",
}

# Horario de saida de cada dia, em sequencia (entrada 09:00, almoco 12h-13h).
# Saida 16:00 da as 6h da meta; os outros dao credito ou debito - assim o
# saldo e os graficos nao ficam uma linha reta. A lista se repete.
SAIDAS_LUCAS = [
    time(16, 0), time(16, 30), time(15, 30), time(16, 0), time(17, 0),
    time(16, 0), time(15, 40), time(16, 20), time(16, 0), time(16, 30),
    time(15, 0), time(16, 10), time(16, 0), time(16, 40), time(15, 50),
]
SAIDAS_BEATRIZ = [time(15, 30), time(16, 0), time(15, 0), time(15, 40), time(15, 50)]


def ultimos_dias_uteis(quantidade: int) -> list[date]:
    """Os N dias de semana anteriores a hoje (sem feriado), do mais antigo ao mais novo."""
    dias = []
    dia = date.today() - timedelta(days=1)
    while len(dias) < quantidade:
        if dia.weekday() < 5 and dia not in FERIADOS_2026:
            dias.append(dia)
        dia = dia - timedelta(days=1)
    dias.reverse()
    return dias


def dia_completo(estagiario, dia, saida, entrada=time(9, 0)):
    return RegistroPonto(
        estagiario=estagiario, data=dia, entrada=entrada,
        saida_almoco=time(12, 0), retorno_almoco=time(13, 0), saida=saida,
    )


def main() -> None:
    criar_tabelas()
    session = SessionLocal()

    if session.query(Estagiario).count() > 0:
        print("O banco ja tem estagiarios cadastrados - nada foi alterado.")
        session.close()
        return

    carla = Gestor(nome="Carla Mendes")
    lucas = Estagiario(nome="Lucas Andrade", gestor=carla)
    beatriz = Estagiario(nome="Beatriz Souza", gestor=carla)
    rafael = Estagiario(nome="Rafael Lima", gestor=carla)
    for pessoa in (lucas, beatriz, rafael):
        pessoa.configuracao = Configuracao(meta_horas_diaria=6.0, meta_horas_semanal=30.0)
    session.add_all([carla, lucas, beatriz, rafael])

    dias_lucas = ultimos_dias_uteis(60)
    inicio = dias_lucas[0]
    for dia, nome in FERIADOS_2026.items():
        if inicio <= dia < date.today():
            session.add(Feriado(data=dia, descricao=nome))

    # Lucas: ~3 meses. O ultimo dia fica com pendencia (esqueceu o retorno).
    for indice, dia in enumerate(dias_lucas[:-1]):
        session.add(dia_completo(lucas, dia, SAIDAS_LUCAS[indice % len(SAIDAS_LUCAS)]))
    dia_pendente = RegistroPonto(
        estagiario=lucas, data=dias_lucas[-1], entrada=time(8, 30),
        saida_almoco=time(12, 0), retorno_almoco=None, saida=time(16, 30),
    )
    session.add(dia_pendente)
    session.add(SolicitacaoAjuste(
        registro=dia_pendente, estagiario=lucas,
        campo_alterado="retorno_almoco", horario_sugerido=time(13, 0),
        justificativa="Esqueci de bater o retorno do almoço.",
    ))

    # Beatriz: um mes de dias curtos - o saldo cai abaixo do alerta de -5h.
    for indice, dia in enumerate(ultimos_dias_uteis(18)):
        session.add(dia_completo(beatriz, dia, SAIDAS_BEATRIZ[indice % len(SAIDAS_BEATRIZ)]))

    # Rafael: dois meses normais e os ultimos 5 dias com 7h (acima das 6h/dia).
    dias_rafael = ultimos_dias_uteis(40)
    for dia in dias_rafael[:-5]:
        session.add(dia_completo(rafael, dia, time(16, 0)))
    ajustado = None
    for dia in dias_rafael[-5:]:
        registro = dia_completo(rafael, dia, time(17, 0), entrada=time(9, 0))
        session.add(registro)
        ajustado = ajustado or registro

    # Historico para a auditoria: um pedido aprovado e um rejeitado.
    session.flush()
    resposta = datetime.combine(dias_rafael[-3], time(10, 0))
    session.add(SolicitacaoAjuste(
        registro=ajustado, estagiario=rafael, campo_alterado="entrada",
        horario_sugerido=time(9, 0), justificativa="O leitor de crachá estava fora do ar.",
        status="aprovado", data_solicitacao=resposta - timedelta(hours=20),
        data_resposta=resposta, gestor=carla,
    ))
    registro_beatriz = session.query(RegistroPonto).filter_by(estagiario=beatriz).first()
    session.add(SolicitacaoAjuste(
        registro=registro_beatriz, estagiario=beatriz, campo_alterado="saida",
        horario_sugerido=time(16, 0), justificativa="Fiquei até mais tarde na reunião.",
        status="rejeitado", data_solicitacao=resposta - timedelta(days=9),
        data_resposta=resposta - timedelta(days=8), gestor=carla,
    ))

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print("Dados de demonstracao criados:")
    print("  gestora: Carla Mendes")
    print("  estagiarios: Lucas Andrade (saldo positivo, 1 pendencia),")
    print("               Beatriz Souza (em alerta) e Rafael Lima (acima do limite legal)")
    print("  1 pedido de ajuste pendente na fila da Carla")


if __name__ == "__main__":
    main()
