"""Conexao com o banco de dados via SQLAlchemy.

Modulo dono: Pedro Ribeiro (Desenvolvedor 1 - fundacao).

Este e o unico lugar do projeto que cria o engine e a fabrica de sessoes.
Nenhum outro modulo deve chamar create_engine() por conta propria: todos
pedem uma sessao aqui, atraves de get_session().

Recursos do SQLAlchemy usados aqui: create_engine, declarative_base,
sessionmaker/Session.
"""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

# O banco fica ao lado deste arquivo (banco/dados.db). Usar caminho absoluto
# derivado do __file__ garante que a API e o Streamlit apontem para o mesmo
# arquivo, nao importa de qual pasta cada processo foi iniciado.
PASTA_BANCO = Path(__file__).resolve().parent
CAMINHO_BANCO = PASTA_BANCO / "dados.db"
URL_BANCO = f"sqlite:///{CAMINHO_BANCO}"

engine = create_engine(
    URL_BANCO,
    echo=False,
    # O Uvicorn atende requisicoes em threads diferentes; sem isso o SQLite
    # recusa a conexao criada em outra thread.
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _ativar_chaves_estrangeiras(conexao, _registro):
    """Liga a checagem de ForeignKey no SQLite.

    Por padrao o SQLite ACEITA um estagiario_id que nao existe. Sem este
    PRAGMA, os ForeignKey dos modelos seriam so documentacao.
    """
    cursor = conexao.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Classe base da qual todos os modelos de modelos/ herdam.
Base = declarative_base()

# Fabrica de sessoes. expire_on_commit=False mantem os objetos utilizaveis
# depois do commit (a rota precisa ler estagiario.id para montar a resposta).
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def criar_tabelas() -> None:
    """Cria no banco todas as tabelas mapeadas que ainda nao existem."""
    # Import local, e nao no topo do arquivo: modelos/ importa Base daqui,
    # entao importar modelos aqui em cima criaria um ciclo. O import so
    # precisa acontecer para que as classes se registrem em Base.metadata.
    import modelos  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session():
    """Abre uma sessao, entrega para quem pediu e garante o fechamento.

    Usado como dependencia do FastAPI: `session: Session = Depends(get_session)`.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
