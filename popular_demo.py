"""Popula o banco com dados de demonstracao.

Serve para quem abre o projeto pela primeira vez (ou para a apresentacao)
ver o sistema com dados, sem precisar cadastrar tudo na mao:

- 1 gestora (Carla Mendes) com 3 estagiarios:
  - Lucas Andrade: ~3 meses de ponto, saldo positivo, um dia com pendencia
    de almoco e um pedido de ajuste esperando a gestora;
  - Beatriz Souza: dias curtos, saldo abaixo do limite de alerta (-5h);
  - Rafael Lima: dias de 7h nos ultimos dias, acima do limite legal de 6h;
- os feriados nacionais do periodo;
- um pedido aprovado e um rejeitado, para a auditoria ter historico;
- (Entrega 3) contas de login, chamados ao gestor e a agenda do Lucas, com
  duas provas e uma aula.

Os dias sao contados a partir de hoje (as ultimas semanas uteis), entao a
demonstracao sempre parece recente, nao importa quando o script rodar.

Rodar uma vez, na raiz do projeto, com a API parada ou rodando:
    python popular_demo.py

Com o banco vazio, cria tudo. Com o banco ja preenchido (de antes do
login), nao mexe no que existe: so cria a conta de quem ainda nao tem e,
se ainda nao houver nenhum chamado nem compromisso, acrescenta os de
exemplo. Para comecar do zero, apague banco/dados.db e rode de novo.

Contas criadas (senha de todas: internhub123):
    carla@internhub.dev     gestora
    lucas@internhub.dev     estagiario
    beatriz@internhub.dev   estagiaria
    rafael@internhub.dev    estagiario

Usa o SQLAlchemy direto (sessao, add_all, commit), sem passar pela API -
e um script de carga, nao uma tela do sistema.
"""

from datetime import date, datetime, time, timedelta

import unicodedata

from banco.conexao import SessionLocal, criar_tabelas
from modelos import (
    Chamado,
    Compromisso,
    Configuracao,
    Estagiario,
    Feriado,
    Gestor,
    MensagemChamado,
    RegistroPonto,
    SolicitacaoAjuste,
    Usuario,
)
from modelos.usuario import PERFIL_ESTAGIARIO, PERFIL_GESTOR
from servicos.autenticacao import gerar_hash_senha

# Senha das contas de exemplo. So vale para a demonstracao: quem for usar de
# verdade cadastra a propria conta pela tela de entrada.
SENHA_DEMO = "internhub123"
DOMINIO_DEMO = "internhub.dev"

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


def _email_demo(nome: str, usados: set[str]) -> str:
    """'Lucas Andrade' -> 'lucas@internhub.dev' (sem acento, sem repetir)."""
    primeiro = nome.split()[0].lower()
    base = unicodedata.normalize("NFKD", primeiro).encode("ascii", "ignore").decode() or "pessoa"
    email, n = f"{base}@{DOMINIO_DEMO}", 2
    while email in usados:
        email, n = f"{base}{n}@{DOMINIO_DEMO}", n + 1
    usados.add(email)
    return email


def completar_contas(session) -> list[tuple[str, str]]:
    """Cria a conta de login de quem ainda nao tem (bancos de antes do login).

    Devolve [(nome, email)] das contas criadas, para mostrar no terminal.
    """
    usados = {email for (email,) in session.query(Usuario.email).all()}
    criadas = []
    for gestor in session.query(Gestor).order_by(Gestor.id).all():
        if gestor.usuario is None:
            email = _email_demo(gestor.nome, usados)
            gestor.usuario = Usuario(email=email, senha_hash=gerar_hash_senha(SENHA_DEMO), perfil=PERFIL_GESTOR)
            criadas.append((gestor.nome, email))
    for estagiario in session.query(Estagiario).order_by(Estagiario.id).all():
        if estagiario.usuario is None:
            email = _email_demo(estagiario.nome, usados)
            estagiario.usuario = Usuario(
                email=email, senha_hash=gerar_hash_senha(SENHA_DEMO), perfil=PERFIL_ESTAGIARIO
            )
            criadas.append((estagiario.nome, email))
    return criadas


def proximo_dia_util(a_partir_de: date, pular: int = 0) -> date:
    """O N-esimo dia util (seg-sex, sem feriado) depois de a_partir_de."""
    dia, achados = a_partir_de, -1
    while True:
        dia += timedelta(days=1)
        if dia.weekday() < 5 and dia not in FERIADOS_2026:
            achados += 1
            if achados == pular:
                return dia


def completar_novidades(session) -> bool:
    """Chamados e agenda de exemplo (Entrega 3), se ainda nao houver nenhum."""
    if session.query(Chamado).first() is not None or session.query(Compromisso).first() is not None:
        return False
    pessoas = {e.nome.split()[0]: e for e in session.query(Estagiario).all()}
    lucas, beatriz, rafael = pessoas.get("Lucas"), pessoas.get("Beatriz"), pessoas.get("Rafael")
    if lucas is None or lucas.gestor_id is None:
        return False

    hoje = date.today()
    agora = datetime.now()

    # Agenda do Lucas: duas provas (a meta desses dias cai pela metade) e
    # uma aula e uma reuniao, para o painel e o Google Agenda terem o que mostrar.
    session.add_all([
        Compromisso(estagiario=lucas, titulo="Prova de Banco de Dados", tipo="prova",
                    data=proximo_dia_util(hoje, 1), inicio=time(19, 0), fim=time(21, 0),
                    local="UniAnchieta - bloco B"),
        Compromisso(estagiario=lucas, titulo="Prova de Programação em Python", tipo="prova",
                    data=proximo_dia_util(hoje, 6), local="UniAnchieta"),
        Compromisso(estagiario=lucas, titulo="Aula de Estatística", tipo="aula",
                    data=proximo_dia_util(hoje, 0), inicio=time(19, 0), fim=time(22, 30)),
        Compromisso(estagiario=lucas, titulo="Reunião de acompanhamento com a Carla", tipo="reuniao",
                    data=proximo_dia_util(hoje, 2), inicio=time(14, 0), fim=time(14, 30),
                    observacao="Revisar o banco de horas do mês."),
    ])

    # Chamados: um em andamento com conversa, um aberto e um resolvido.
    vpn = Chamado(estagiario=lucas, gestor_id=lucas.gestor_id, titulo="Sem acesso à VPN da empresa",
                  categoria="acesso", prioridade="alta", status="em_andamento",
                  aberto_em=agora - timedelta(days=1, hours=3), atualizado_em=agora - timedelta(hours=20))
    vpn.mensagens = [
        MensagemChamado(autor="estagiario", enviada_em=agora - timedelta(days=1, hours=3),
                        texto="Desde ontem a VPN recusa meu usuário e não consigo acessar o repositório."),
        MensagemChamado(autor="gestor", enviada_em=agora - timedelta(hours=20),
                        texto="Abri o pedido com a TI. Eles vão liberar seu acesso até amanhã."),
    ]
    session.add(vpn)
    if beatriz is not None and beatriz.gestor_id is not None:
        notebook = Chamado(estagiario=beatriz, gestor_id=beatriz.gestor_id,
                           titulo="Notebook sem carregador", categoria="equipamento", prioridade="media",
                           aberto_em=agora - timedelta(hours=4), atualizado_em=agora - timedelta(hours=4))
        notebook.mensagens = [MensagemChamado(
            autor="estagiario", enviada_em=agora - timedelta(hours=4),
            texto="O carregador do notebook da empresa parou de funcionar. Tem algum reserva?")]
        session.add(notebook)
    if rafael is not None and rafael.gestor_id is not None:
        termo = Chamado(estagiario=rafael, gestor_id=rafael.gestor_id,
                        titulo="Dúvida sobre o termo de compromisso", categoria="documentacao",
                        prioridade="baixa", status="resolvido",
                        aberto_em=agora - timedelta(days=6), atualizado_em=agora - timedelta(days=5),
                        resolvido_em=agora - timedelta(days=5))
        termo.mensagens = [
            MensagemChamado(autor="estagiario", enviada_em=agora - timedelta(days=6),
                            texto="O termo diz 30h semanais, mas no mês de provas posso reduzir?"),
            MensagemChamado(autor="gestor", enviada_em=agora - timedelta(days=5),
                            texto="Pode sim: em dia de prova a carga cai pela metade. Cadastre a prova na agenda."),
        ]
        session.add(termo)
    return True


def main() -> None:
    criar_tabelas()
    session = SessionLocal()

    if session.query(Estagiario).count() > 0:
        # Banco de antes do login: completa sem apagar nada.
        try:
            contas = completar_contas(session)
            novidades = completar_novidades(session)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        if not contas and not novidades:
            print("O banco ja tem estagiarios cadastrados - nada foi alterado.")
            return
        for nome, email in contas:
            print(f"  conta criada: {email:<28} ({nome})")
        if contas:
            print(f"  senha de todas as contas criadas: {SENHA_DEMO}")
        if novidades:
            print("  chamados e agenda de exemplo acrescentados.")
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
        session.flush()
        contas = completar_contas(session)
        completar_novidades(session)
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
    print("  1 pedido de ajuste pendente na fila da Carla, 3 chamados e a agenda do Lucas")
    print("  contas (senha de todas: %s):" % SENHA_DEMO)
    for nome, email in contas:
        print(f"    {email:<28} {nome}")


if __name__ == "__main__":
    main()
