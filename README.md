# InternHub — Banco de Horas do Estágio

Sistema para estagiários registrarem o ponto, acompanharem o saldo de
horas (banco de horas) e simularem cenários futuros. Projeto da disciplina
de Programação em Python, UniAnchieta 2026/2, construído em torno do
**SQLAlchemy** como biblioteca principal.

Arquitetura: uma API própria em **FastAPI** cobre todo o sistema (o único
lugar que fala com o banco) e um frontend em **React** consome essa API
por HTTP. Não existe acesso direto ao banco fora da API.

## Pré-requisitos

- **Python 3.10 ou mais novo** (o código usa a sintaxe `str | None`)
- **Node.js 20.19 ou mais novo** (exigência do Vite 8), com o `npm`

O banco é SQLite: não precisa instalar servidor de banco nenhum. O arquivo
`banco/dados.db` é criado sozinho na primeira vez que a API sobe.

## Como rodar

São dois processos, cada um no seu terminal: primeiro a API, depois o
frontend.

### 1. API (Python) — terminal 1

Na raiz do projeto:

```
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # Linux/macOS
pip install -r requirements.txt

copy .env.example .env              # Linux/macOS: cp .env.example .env
python popular_demo.py              # recomendado: dados de exemplo
uvicorn api.app_api:app --reload
```

- API em `http://localhost:8000`, documentação interativa em
  `http://localhost:8000/docs` (dá para testar todas as rotas por lá).
- O `.env` pode ficar com os dois campos vazios:
  - sem `API_TOKEN`, a API roda aberta, sem exigir token (ver
    `api/seguranca.py`);
  - sem `OPENAI_API_KEY`, o assistente de IA responde com um aviso e todo
    o resto funciona normalmente.
- `popular_demo.py` cria um gestor (Carla Mendes), dois estagiários e as
  últimas semanas de ponto do Lucas Andrade, com um dia pendente e um
  pedido de ajuste esperando aprovação. Só roda com o banco vazio — sem
  ele, o sistema abre sem nenhum cadastro.

### 2. Frontend (React) — terminal 2

```
cd frontend
npm install
copy .env.example .env              # Linux/macOS: cp .env.example .env
npm run dev
```

Abre em `http://localhost:5173`. Na tela inicial, escolha "estagiário"
(ex: Lucas Andrade) ou "gestor" (ex: Carla Mendes).

Se preencher `API_TOKEN` no `.env` da raiz, coloque o mesmo valor em
`VITE_API_TOKEN` no `frontend/.env` — senão a API responde 401.

## Testes

Na raiz do projeto, com o `.venv` ativado:

```
pytest -v
```

São 35 casos em dois arquivos:

- `testes/test_calculo.py` — regras do dia (horas trabalhadas, almoço
  mínimo de 1h, pendência, ordem dos horários, limite legal).
- `testes/test_api.py` — requisições de verdade na API, num banco em
  memória (não mexe no `dados.db`): registro e saldo, validação 422, fluxo
  completo de ajuste com aprovação do gestor, faltas do relatório,
  exportação PDF/Excel e o bloqueio 401 sem token.

## Estrutura

```
api/              # FastAPI: app, rotas por modulo, schemas Pydantic,
                  # autenticacao por token e rate limiting (seguranca.py)
banco/            # engine e sessao do SQLAlchemy (conexao.py) + dados.db
modelos/          # classes mapeadas: Estagiario, Gestor, Configuracao,
                  # RegistroPonto, SolicitacaoAjuste, Feriado
servicos/         # regras de negocio: calculo, saldo, simulador, vencimento,
                  # feriados, solicitacao, assistente, exportacoes
testes/           # pytest
frontend/         # interface em React (Vite), consome a API por HTTP
popular_demo.py   # carga de dados de exemplo
```

## Funcionalidades

Registro de ponto com controle de almoço, cálculo de saldo (banco de
horas), alerta de saldo negativo, aviso de limite legal de horas do
estágio (Lei 11.788/2008 — 6h/dia, 30h/semana), relatório mensal com
gráfico e exportação em PDF/Excel, simulador de cenários, solicitação de
ajuste de ponto com aprovação do gestor, auditoria, calendário de
feriados, múltiplos estagiários, assistente de IA para dúvidas sobre
saldo, autenticação por token e rate limiting na API.

A primeira interface foi feita em Streamlit e foi substituída pelo
frontend em React (o código antigo continua no histórico do Git).

Detalhes de escopo, decisões de arquitetura e divisão de responsabilidades
do grupo estão nos documentos de entrega da disciplina.
