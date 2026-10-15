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
  - sem `IA_CHAVE`, o assistente de IA responde com um aviso e todo o
    resto funciona normalmente. O provedor padrão é o **Groq**, que é
    gratuito: crie uma chave em https://console.groq.com/keys e cole em
    `IA_CHAVE`. Também funciona com Gemini ou OpenAI, trocando
    `IA_PROVEDOR` (ver `.env.example`).
- `popular_demo.py` cria a gestora Carla Mendes e três estagiários com
  cerca de três meses de ponto: Lucas Andrade (saldo positivo, um dia
  pendente e um pedido esperando aprovação), Beatriz Souza (saldo em
  alerta) e Rafael Lima (dias acima do limite legal), além dos feriados
  nacionais do período e um histórico de pedidos aprovados e rejeitados.
  Só roda com o banco vazio — sem ele, o sistema abre sem nenhum cadastro.

### 2. Frontend (React) — terminal 2

```
cd frontend
npm install
copy .env.example .env              # Linux/macOS: cp .env.example .env
npm run dev
```

Abre em `http://localhost:5173`. Na tela inicial, escolha "Sou estagiário"
(ex: Lucas Andrade) ou "Sou gestor" (ex: Carla Mendes). As fontes (Geist) e
os ícones (lucide-react) vêm pelo `npm install`, sem depender de internet
depois disso.

Se preencher `API_TOKEN` no `.env` da raiz, coloque o mesmo valor em
`VITE_API_TOKEN` no `frontend/.env` — senão a API responde 401.

A API só aceita chamadas do frontend em `localhost:5173` (CORS). Se o Vite
abrir em outra porta (ex: 5174, quando a 5173 está ocupada), coloque esse
endereço em `FRONTEND_URL` no `.env` da raiz e reinicie a API.

## Testes

Na raiz do projeto, com o `.venv` ativado:

```
pytest -v
```

São 48 casos em três arquivos:

- `testes/test_calculo.py` — regras do dia (horas trabalhadas, almoço
  mínimo de 1h, pendência, ordem dos horários, limite legal).
- `testes/test_api.py` — requisições de verdade na API, num banco em
  memória (não mexe no `dados.db`): registro e saldo, validação 422, fluxo
  completo de ajuste com aprovação do gestor, faltas do relatório,
  exportação PDF/Excel, aviso de limite legal semanal, o bloqueio 401 sem
  token e o CORS restrito ao frontend.
- `testes/test_entrega3.py` — as rotas da Entrega 3: ponto rápido (ordem
  das marcações, dia encerrado, sem almoço), edição da meta, tendência mês
  a mês, painéis do estagiário e do gestor e remoção de feriado.

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
frontend/         # interface em React (Vite), consome a API por HTTP:
                  #   src/paginas/estagiario/  painel, ponto, solicitacoes,
                  #                            relatorio, simulacao, assistente,
                  #                            configuracoes
                  #   src/paginas/gestor/      equipe, aprovacoes, feriados,
                  #                            auditoria
                  #   src/components/          estrutura, graficos, cartao de ponto
                  #   src/estilos/             tema (claro/escuro) e telas
popular_demo.py   # carga de dados de exemplo
```

## Funcionalidades

**Estagiário**
- Painel inicial: saldo do banco de horas, horas da semana em relação ao
  limite legal, pendências, pedidos em aberto, tendência mês a mês e os
  últimos dias.
- Ponto em um clique (entrada, almoço, retorno, saída) ou lançamento do dia
  inteiro; histórico por semana mostrando o almoço descontado e o total da
  semana em relação a 30h.
- Pedido de ajuste com aprovação do gestor e comprovante em PDF.
- Relatório mensal com calendário do mês, saldo dia a dia, tendência do
  semestre e exportação em PDF/Excel.
- Simulador "e se eu faltar / atrasar", assistente de IA e edição da meta e
  dos limites.

**Gestor**
- Visão da equipe: saldo de cada estagiário, quem está em alerta, quem
  passou do limite legal e quantos pedidos esperam decisão.
- Fila de aprovações, calendário de feriados e auditoria com filtros.

**Regras e segurança**: almoço mínimo de 1h, alerta de saldo negativo,
aviso de limite legal do estágio (Lei 11.788/2008 — 6h/dia, 30h/semana),
vencimento do crédito antigo, autenticação por token e limite de
requisições na API.

**Interface**: tema claro e escuro, layout para celular, telas carregadas
sob demanda e textos em português com datas no formato dd/mm/aaaa.

A primeira interface foi feita em Streamlit e foi substituída pelo
frontend em React (o código antigo continua no histórico do Git).

Detalhes de escopo, decisões de arquitetura e divisão de responsabilidades
do grupo estão nos documentos de entrega da disciplina.
