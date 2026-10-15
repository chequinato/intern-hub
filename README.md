# InternHub — Banco de Horas do Estágio

Projeto da disciplina de Programação em Python, UniAnchieta 2026/2.
Biblioteca principal: **SQLAlchemy**.

## Propósito

O estagiário registra a entrada, o almoço e a saída, e o sistema calcula
sozinho se ele está devendo horas ou tem crédito em relação à meta
contratada: o banco de horas. Hoje esse controle costuma ser feito na mão,
em planilha ou de cabeça, e é fácil perder a conta quando há faltas, atrasos
ou compensações.

**Para quem:** o estagiário que precisa cumprir uma carga horária, e o
gestor que acompanha a equipe e aprova as correções de ponto.

**Como é por dentro:** uma API própria em **FastAPI** é o único lugar que
fala com o banco (SQLite, pelo SQLAlchemy). A interface em **React** só
conversa com essa API por HTTP.

## Funcionalidades

**Estagiário**
- Painel inicial: saldo do banco de horas, horas da semana em relação ao
  limite legal, pendências, pedidos em aberto, tendência mês a mês e os
  últimos dias.
- Ponto em um clique (entrada, almoço, retorno, saída) ou lançamento do dia
  inteiro; histórico por semana mostrando o almoço descontado e o total da
  semana em relação a 30h.
- Pedido de ajuste de ponto com aprovação do gestor e comprovante em PDF.
- Relatório mensal com calendário do mês, saldo dia a dia, tendência do
  semestre e exportação em PDF e Excel.
- Simulador "e se eu faltar / atrasar", assistente de IA e edição da meta e
  dos limites.

**Gestor**
- Visão da equipe: saldo de cada estagiário, quem está em alerta, quem
  passou do limite legal e quantos pedidos esperam decisão.
- Fila de aprovações, calendário de feriados e auditoria com filtros.

**Regras:** almoço mínimo de 1h; dia com almoço incompleto fica fora do
saldo até ser corrigido; alerta de saldo negativo (−5h); aviso de limite
legal do estágio (Lei 11.788/2008: 6h por dia, 30h por semana); aviso de
crédito antigo perto de vencer; feriado não conta como falta.

**Segurança da API:** token de acesso, limite de requisições por minuto,
validação de tudo o que entra e CORS só para o frontend.

## Requisitos

- **Python 3.10 ou mais novo** (o código usa a sintaxe `str | None`)
- **Node.js 20.19 ou mais novo** (exigência do Vite 8), com o `npm`

O banco é SQLite: não precisa instalar servidor de banco nenhum. O arquivo
`banco/dados.db` é criado sozinho na primeira vez que a API sobe.

## Como instalar e rodar

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
- O `.env` pode ficar com os campos vazios: sem `API_TOKEN` a API roda
  aberta, e sem `IA_CHAVE` o assistente funciona em modo demonstração (ver
  "Assistente de IA", abaixo).
- `popular_demo.py` só roda com o banco vazio. Sem ele, o sistema abre sem
  nenhum cadastro.

### 2. Frontend (React) — terminal 2

```
cd frontend
npm install
copy .env.example .env              # Linux/macOS: cp .env.example .env
npm run dev
```

Abre em `http://localhost:5173`. A fonte é a SF Pro em Mac e iPhone e a
Inter (a mais parecida com ela) no Windows; a Inter e os ícones
(lucide-react) vêm pelo `npm install`, sem depender de internet depois.

Se preencher `API_TOKEN` no `.env` da raiz, coloque o mesmo valor em
`VITE_API_TOKEN` no `frontend/.env`; senão a API responde 401.

A API só aceita chamadas do frontend em `localhost:5173` (CORS). Se o Vite
abrir em outra porta (ex: 5174, quando a 5173 está ocupada), coloque esse
endereço em `FRONTEND_URL` no `.env` da raiz e reinicie a API.

## Como usar

### Primeiro acesso

Na tela de entrada, escolha **Sou estagiário** ou **Sou gestor** e clique no
seu nome. Para se cadastrar, use **Cadastrar estagiário** (nome, meta por
dia, meta por semana e gestor responsável) ou **Cadastrar gestor**. Não há
senha: a escolha de perfil é uma decisão do projeto (ver "Limitações").

Com os dados de exemplo:

| Pessoa | Bom para ver |
|---|---|
| **Lucas Andrade** (estagiário) | Saldo positivo, dia com pendência de almoço, pedido na fila, aviso de crédito perto de vencer |
| **Beatriz Souza** (estagiária) | Saldo abaixo do limite de alerta |
| **Rafael Lima** (estagiário) | Dias acima do limite legal de 6h |
| **Carla Mendes** (gestora) | Equipe com os três, pedido para aprovar, histórico de pedidos |

### Estagiário

| Tela | Como usar |
|---|---|
| **Início** | Resumo do banco de horas. O botão do cartão "Ponto de hoje" marca a próxima marcação com a hora atual (entrada → almoço → retorno → saída). Dias com pendência têm atalho "Pedir ajuste". |
| **Ponto** | Mesmo botão de ponto, mais o formulário **Lançar um dia inteiro** (para dias que ficaram para trás) e o histórico do mês, agrupado por semana. Use as setas para trocar de mês. |
| **Solicitações** | Escolha o dia, o horário a corrigir, o horário certo e a justificativa. O pedido vai para o gestor; a lista mostra a resposta e o botão do comprovante em PDF. |
| **Relatório** | Horas, faltas e saldo do mês, calendário colorido, gráficos e os botões **PDF** e **Excel**. |
| **Simulação** | Arraste os controles de dias de falta e horas de atraso: o saldo projetado aparece na hora. Nada é gravado. |
| **Assistente** | Pergunte sobre saldo, semana, pendências, meses anteriores ou cenários ("E se eu faltar 2 dias?"). |
| **Configurações** | Meta por dia e por semana, limite legal, alerta de saldo, prazo de vencimento e gestor responsável. |

### Gestor

| Tela | Como usar |
|---|---|
| **Equipe** | Situação de cada estagiário: saldo, horas da semana, alertas e pedidos. |
| **Aprovações** | **Aprovar** aplica o horário no registro e recalcula o saldo; **Rejeitar** fecha o pedido sem mexer no registro. |
| **Feriados** | Cadastre um dia não útil ou use os atalhos dos feriados nacionais. Feriado não conta como falta para ninguém. |
| **Auditoria** | Todos os pedidos, com quem pediu, quem decidiu e quando. Filtre por situação, busque pelo nome e baixe o comprovante. |

O botão **Tema claro / Tema escuro** fica na barra lateral, e **Trocar
perfil** volta para a tela de entrada.

## Assistente de IA

O assistente responde dúvidas sobre o banco de horas **usando os dados de
quem pergunta**: antes de chamar a IA, `servicos/assistente.py` busca no
banco o saldo, a semana, as pendências, os pedidos, os últimos meses e, se
a pergunta pedir, a simulação. A IA só transforma esses números em texto e
é instruída a não inventar nada. Ela nunca calcula.

| Variável no `.env` | Para quê |
|---|---|
| `IA_PROVEDOR` | `groq` (padrão, gratuito), `gemini` (gratuito com limite) ou `openai` (pago) |
| `IA_CHAVE` | A chave do provedor. Groq: https://console.groq.com/keys |
| `IA_MODELO` | Opcional; vazio usa o padrão do provedor (no Groq, `openai/gpt-oss-120b`) |

**Modo demonstração:** sem `IA_CHAVE`, o assistente responde com os mesmos
números do banco, só que sem o texto em linguagem natural. Dá para avaliar
o sistema inteiro sem chave nenhuma.

A chave fica só no `.env` (ignorado pelo Git), nunca no `.env.example`.

## Testes

Na raiz do projeto, com o `.venv` ativado:

```
pytest -v
```

São 49 casos em três arquivos, todos num banco em memória (não mexem no
`dados.db`):

- `testes/test_calculo.py` — regras do dia (horas trabalhadas, almoço
  mínimo de 1h, pendência, ordem dos horários, limite legal).
- `testes/test_api.py` — requisições de verdade na API: registro e saldo,
  validação 422, fluxo completo de ajuste com aprovação do gestor, faltas do
  relatório, exportação PDF/Excel, aviso de limite legal semanal, bloqueio
  401 sem token e CORS restrito ao frontend.
- `testes/test_entrega3.py` — ponto rápido, edição da meta, tendência mês a
  mês, painéis do estagiário e do gestor, remoção de feriado, provedor de
  IA e modo demonstração do assistente.

Vários testes nasceram de defeitos encontrados e corrigidos (o docstring de
cada um conta o caso): faltas contadas antes do primeiro ponto, aviso de
limite semanal marcando a semana inteira, almoço curto com desconto de 1h.

## SQLAlchemy no projeto

**Por que ele:** o sistema gira em torno de registros que se acumulam e
precisam ser somados, filtrados e cruzados por pessoa e por período. Um ORM
dá tabelas, relacionamentos e consultas de verdade. A alternativa descartada
foi gravar em arquivos `.json`, que obrigaria a refazer na mão toda soma e
todo filtro.

**Onde ele fez o trabalho pesado:** o saldo do banco de horas é calculado
numa única consulta (`servicos/saldo.py`, `calcular_saldo_acumulado`). O
banco converte cada horário em segundos, desconta o almoço com o mínimo de
1h e soma todos os dias completos, sem trazer os registros para o Python. A
tendência mês a mês usa a mesma conta agrupada por mês (`saldo_por_mes`).

| # | Recurso | Para quê | Onde |
|---|---|---|---|
| 1 | `create_engine` + `event.listens_for` | Conexão com o SQLite e chave estrangeira ligada em cada conexão | `banco/conexao.py` |
| 2 | `declarative_base` | Classe `Base` de todos os modelos | `banco/conexao.py` → `modelos/` |
| 3 | `sessionmaker` / `Session` | Uma sessão por requisição (`Depends(get_session)`) | `banco/conexao.py`, todas as rotas |
| 4 | `Base.metadata.create_all` | Cria as tabelas quando a API sobe | `banco/conexao.py` |
| 5 | `Column` e tipos (`Integer`, `String`, `Float`, `Date`, `Time`, `DateTime`) com `nullable`, `unique`, `default` | As 6 tabelas | `modelos/` |
| 6 | `ForeignKey` (com `unique=True` no 1-para-1) | Registro → estagiário, configuração → estagiário, solicitação → registro/gestor | `modelos/` |
| 7 | `relationship` com `back_populates`, `uselist=False`, `cascade`, `order_by` | Navegar entre estagiário, configuração, registros e solicitações | `modelos/estagiario.py`, `gestor.py`, `registro_ponto.py` |
| 8 | `query().filter()` / `filter_by()` | Buscar por pessoa, data e status | rotas e serviços |
| 9 | `order_by()` e `.desc()` | Histórico em ordem; auditoria do mais recente para o mais antigo | `api/rotas/registros.py`, `servicos/solicitacao.py` |
| 10 | `join()` | Fila do gestor: só pedidos da equipe dele | `servicos/solicitacao.py` |
| 11 | `func.sum()` e `func.count()` | Soma das horas e contagem de dias no banco | `servicos/saldo.py`, `servicos/painel.py` |
| 12 | `case()`, `func.cast()`, `func.strftime()` | Horário em segundos e almoço mínimo de 1h dentro da consulta | `servicos/saldo.py` |
| 13 | `group_by()` | Saldo mês a mês (tendência) | `servicos/saldo.py` |
| 14 | `extract("month"/"year")` | Registros de um mês | `api/rotas/relatorio.py` |
| 15 | `func.min()` / `func.max()` + `scalar()` | Primeiro ponto (faltas) e último ponto (painel do gestor) | `api/rotas/relatorio.py`, `servicos/painel.py` |
| 16 | `is_not(None)` / `is_(None)` | Só dias completos no saldo; achar dias com pendência | `servicos/saldo.py`, `servicos/painel.py` |
| 17 | `limit()` | Os últimos dias do painel | `servicos/painel.py` |
| 18 | `add`, `add_all`, `delete`, `commit`, `rollback`, `refresh` + `SQLAlchemyError` | Gravar com integridade: ou grava tudo, ou nada | rotas de criação, `servicos/solicitacao.py`, `servicos/ponto.py`, `popular_demo.py` |

## Estrutura

```
api/              # FastAPI: app, rotas por modulo, schemas Pydantic,
                  # autenticacao por token e rate limiting (seguranca.py)
banco/            # engine e sessao do SQLAlchemy (conexao.py) + dados.db
modelos/          # classes mapeadas: Estagiario, Gestor, Configuracao,
                  # RegistroPonto, SolicitacaoAjuste, Feriado
servicos/         # regras de negocio: calculo, saldo, ponto, painel,
                  # simulador, vencimento, feriados, solicitacao,
                  # assistente, exportacoes
testes/           # pytest (conftest.py tem o banco em memoria dos testes)
frontend/         # interface em React (Vite), consome a API por HTTP
docs/             # registro das decisoes do grupo (decisoes.md)
popular_demo.py   # carga de dados de exemplo
```

Cada arquivo do backend começa dizendo quem é o dono do módulo e quais
recursos do SQLAlchemy ele usa.

## Limitações conhecidas

- **Sem login por pessoa.** Qualquer um escolhe o perfil e o nome na tela de
  entrada. Isso foi decidido na Entrega 1 e mantido; o token protege o
  acesso à API, mas não identifica a pessoa.
- **SQLite e um processo só.** O banco é um arquivo local e o limite de
  requisições fica em memória (zera quando a API reinicia). Basta para uma
  equipe pequena, não para muitos acessos ao mesmo tempo.
- **O vencimento só avisa.** O crédito antigo aparece como "perto de
  vencer", mas não é descontado do saldo automaticamente.
- **"Dias trabalhados" do relatório** conta todo dia com ponto, mesmo que
  caia num fim de semana.
- **O ponto rápido usa a hora do computador onde a API roda.** Se o relógio
  dele estiver errado, a marcação também fica.
- **O assistente depende de um serviço externo.** Sem internet ou sem cota,
  ele avisa e o resto continua; os modelos gratuitos podem mudar de nome
  (dá para trocar em `IA_MODELO`).
- **Testado no Chrome**, em tela de computador e de celular.

**Fora do escopo, de propósito:** integração com o sistema de ponto real
da empresa, mais de um contrato por estagiário, documento com valor legal
ou trabalhista, login com senha por pessoa e compensação de horas (folga
usando o crédito do banco).

## Histórico

A primeira interface foi feita em Streamlit e foi substituída pelo frontend
em React (o código antigo continua no histórico do Git). As decisões do
grupo, com data e motivo, estão em [`docs/decisoes.md`](docs/decisoes.md).
