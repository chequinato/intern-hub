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
- Login com e-mail e senha; cada pessoa vê só os próprios dados.
- Painel inicial: saldo do banco de horas, horas da semana em relação ao
  limite legal, pendências, pedidos, agenda do dia, chamados em aberto,
  tendência mês a mês e os últimos dias.
- Ponto em um clique (entrada, almoço, retorno, saída) ou lançamento do dia
  inteiro; histórico por semana mostrando o almoço descontado e o total da
  semana em relação a 30h.
- **Agenda** com aulas, reuniões e **provas**: em dia de prova a meta cai
  pela metade (Lei 11.788/2008, art. 10). Cada compromisso vai para o
  **Google Agenda** com um clique, ou todos de uma vez num arquivo `.ics`.
- Pedido de ajuste de ponto com aprovação do gestor e comprovante em PDF.
- **Chamados ao gestor** para o que não é ponto (acesso, equipamento,
  sistema, documentos), com conversa e andamento.
- **Crachá virtual** com QR code: quem lê o código vê se o vínculo está
  ativo, sem ver o banco de horas.
- **Contrato e recesso:** o termo de compromisso (dias até o fim) e o
  **recesso remunerado** de 30 dias por ano, proporcional: 2,5 dias por mês
  completo (Lei 11.788/2008, art. 13). O estagiário pede, o gestor aprova, e
  dia de recesso não conta como falta.
- **Atividades e relatório semestral:** diário do que foi feito no estágio,
  avaliado e validado pelo gestor, com ciência do estagiário e PDF para a
  faculdade (art. 9º, VII).
- Relatório mensal com calendário do mês (dias de prova marcados), saldo dia
  a dia, tendência do semestre e exportação em PDF e Excel.
- Simulador "e se eu faltar / atrasar" e assistente de IA.

**Gestor**
- Visão da equipe: saldo de cada estagiário, quem está em alerta, quem
  passou do limite legal, pedidos e chamados esperando resposta.
- Por estagiário: termo de compromisso (no máximo 2 anos, art. 11), meta e
  limites, próximas provas e o crachá (desativar no fim do estágio).
- Aviso de contrato terminando em até 30 dias.
- Fila de aprovações (ajustes de ponto e recesso), fila de chamados
  (prioridade alta primeiro), relatórios semestrais da equipe, calendário de
  feriados, auditoria e cadastro de outros gestores.

**Regras:** almoço mínimo de 1h; dia com almoço incompleto fica fora do
saldo até ser corrigido; alerta de saldo negativo (−5h); aviso de limite
legal do estágio (Lei 11.788/2008: 6h por dia, 30h por semana); em dia de
prova a meta e o limite do dia caem pela metade; aviso de crédito antigo
perto de vencer; feriado e recesso aprovado não contam como falta; contrato
de no máximo 2 anos; semestre validado pelo gestor fica fechado.

**Segurança:** login com senha guardada em hash (PBKDF2), sessão com prazo
de 12h, regras de acesso por perfil em toda rota, limite de tentativas de
login, chave do aplicativo, limite de requisições por minuto, validação de
tudo o que entra e CORS só para o frontend.

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
python popular_demo.py              # cria os dados e as contas de exemplo
uvicorn api.app_api:app --reload
```

- API em `http://localhost:8000`, documentação interativa em
  `http://localhost:8000/docs`. Para testar rotas que pedem login por lá:
  chame `POST /auth/entrar`, copie o `token` e cole no botão **Authorize**.
- O `.env` pode ficar com os campos vazios: sem `API_TOKEN` a API aceita
  qualquer cliente, e sem `IA_CHAVE` o assistente funciona em modo
  demonstração (ver "Assistente de IA", abaixo).
- `popular_demo.py` com o banco vazio cria tudo. Num banco de antes do login,
  ele não apaga nada: só cria a conta de quem ainda não tem (e mostra os
  e-mails no terminal) e acrescenta chamados e agenda de exemplo.

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
endereço em `FRONTEND_URL` no `.env` da raiz e reinicie a API. O QR code do
crachá também aponta para o primeiro endereço do `FRONTEND_URL`.

## Como usar

### Contas de exemplo

Depois de `python popular_demo.py`, todas com a senha **`internhub123`**:

| E-mail | Quem | Bom para ver |
|---|---|---|
| `lucas@internhub.dev` | Lucas Andrade, estagiário | Saldo positivo, dia com pendência, pedido na fila, duas provas na agenda, chamado em andamento, recesso pedido, atividades do semestre |
| `beatriz@internhub.dev` | Beatriz Souza, estagiária | Saldo abaixo do limite de alerta, chamado sem resposta, contrato terminando em 20 dias |
| `rafael@internhub.dev` | Rafael Lima, estagiário | Dias acima do limite legal de 6h, chamado resolvido |
| `carla@internhub.dev` | Carla Mendes, gestora | Equipe com os três, pedido de ajuste e de recesso para aprovar, fila de chamados, semestre do Lucas para avaliar |

Essas senhas são só da demonstração. Para uma conta nova, use **Criar conta**
na tela de entrada (estagiário). O primeiro gestor de um banco vazio se
cadastra pela tela de entrada; os próximos são cadastrados por um gestor, em
**Conta e gestores**.

### Estagiário

| Tela | Como usar |
|---|---|
| **Início** | Resumo do banco de horas. O botão do cartão "Ponto de hoje" marca a próxima marcação com a hora atual. Em dia de prova aparece a meta reduzida. |
| **Ponto** | Mesmo botão de ponto, mais o formulário **Lançar um dia inteiro** e o histórico do mês, agrupado por semana. |
| **Agenda** | Cadastre provas, aulas, reuniões e entregas. **Google Agenda** abre o evento já preenchido no Google; **Baixar .ics** exporta todos (Google Agenda › Configurações › Importar). |
| **Solicitações** | Escolha o dia, o horário a corrigir, o horário certo e a justificativa. O pedido vai para o gestor; a lista mostra a resposta e o comprovante em PDF. |
| **Chamados** | **Novo chamado** com assunto, categoria, prioridade e descrição. A conversa com o gestor fica no chamado. |
| **Contrato e recesso** | Dias até o fim do contrato e o saldo de recesso (direito, aprovado, pedido, disponível). **Pedir recesso** escolhe o período; dá para cancelar enquanto o gestor não responde. |
| **Atividades** | Registre o que fez (uma linha por semana já basta). Quando o gestor validar o semestre, clique em **Estou ciente**; **PDF para a faculdade** gera o relatório. |
| **Relatório** | Horas, faltas e saldo do mês, calendário (com "P" nos dias de prova), gráficos, **PDF** e **Excel**. |
| **Simulação** | Arraste os controles de faltas e atrasos: o saldo projetado aparece na hora. Nada é gravado. |
| **Assistente** | Pergunte sobre saldo, semana, pendências, meses anteriores ou cenários ("E se eu faltar 2 dias?"). |
| **Crachá** | O crachá com QR code. **Imprimir** sai só o crachá; **Reemitir** troca o código se o impresso for perdido. |
| **Configurações** | Meta e limites (só leitura: quem altera é o gestor) e troca de senha. |

### Gestor

| Tela | Como usar |
|---|---|
| **Equipe** | Situação de cada estagiário (inclui contrato terminando e recesso a aprovar). **Gerenciar** abre o termo de compromisso, meta e limites, próximas provas e o crachá. |
| **Aprovações** | Ajustes de ponto: **Aprovar** aplica o horário e recalcula o saldo; **Rejeitar** não mexe no registro. Abaixo, os pedidos de recesso. |
| **Relatórios semestrais** | Escolha o estagiário, leia as atividades, escreva a avaliação e **Validar semestre** (fecha o semestre). **PDF para a faculdade** sai pronto. |
| **Chamados** | Fila da equipe. Responder já coloca o chamado "em andamento"; **Marcar resolvido** fecha. |
| **Feriados** | Cadastre um dia não útil ou use os atalhos dos feriados nacionais. |
| **Auditoria** | Pedidos da equipe, com quem pediu, quem decidiu e quando. |
| **Conta e gestores** | Troca de senha e cadastro de outro gestor. |

O botão **Tema claro / Tema escuro** fica na barra lateral, e **Sair**
encerra a sessão.

## Contrato de estágio: o que o sistema controla e por quê

Até a Entrega 3 o InternHub controlava as **horas**. Estas três partes
controlam o **estágio**, naquilo que a Lei 11.788/2008 exige da empresa. Cada
uma foi escolhida porque a lei manda; nenhuma é enfeite.

### Termo de compromisso (art. 11)

- **O que faz:** o gestor cadastra o início e o fim do contrato, a
  instituição de ensino e o curso. Um termo de mais de 2 anos é recusado,
  exceto para pessoa com deficiência. Faltando 30 dias para o fim, aparece um
  aviso no painel do gestor, na linha do estagiário na Equipe e no Início do
  estagiário.
- **Por quê:** a lei proíbe estágio de mais de 2 anos na mesma empresa, e o
  sistema não sabia quando o contrato terminava. Ninguém via o fim chegando.
- **Por que só o gestor cadastra:** as datas fazem parte do contrato
  assinado, assim como a meta de horas.

### Recesso remunerado (art. 13)

- **O que faz:** o estagiário acumula 2,5 dias de recesso por mês completo
  de estágio (30 por ano), pede um período e o gestor aprova ou recusa na
  tela de Aprovações. O sistema recusa pedido no passado, com mais dias do
  que a pessoa tem, depois do fim do contrato ou em cima de outro pedido.
- **Por quê:** a lei garante 30 dias de recesso por ano, proporcional para
  quem tem menos de um ano de estágio. Antes, se o estagiário tirasse esses
  dias, o relatório mensal contava cada um como **falta**. Agora, dia de
  recesso aprovado não é falta e aparece marcado no calendário do relatório.
- **Por que o gestor aprova:** é o mesmo princípio do ajuste de ponto — quem
  pede não decide.

### Relatório de atividades semestral (art. 9º, VII)

- **O que faz:** o estagiário registra o que fez num diário de atividades; o
  gestor lê, escreve a avaliação e valida o semestre; o estagiário confirma
  que está ciente; sai um PDF pronto para entregar à faculdade.
- **Por quê:** a lei obriga a empresa a enviar à instituição de ensino, no
  mínimo a cada 6 meses, um relatório de atividades "com vista obrigatória ao
  estagiário". A validação do gestor e a ciência do estagiário existem para
  cumprir exatamente essas duas exigências.
- **Por que o semestre validado fica fechado:** o PDF vai para a faculdade.
  Se as atividades pudessem mudar depois, o documento enviado não bateria
  com o que está no sistema.

### Decisões técnicas

- **Tabelas novas, sem colunas novas nas antigas** (`termos_compromisso`,
  `pedidos_recesso`, `atividades_estagio`, `relatorios_atividades`): o
  `create_all` do SQLAlchemy cria tabelas que faltam, mas não acrescenta
  colunas. Assim quem já tem o banco não perde nada.
- **Recesso somado no banco:** os dias de cada pedido são calculados com
  `func.julianday()` dentro de `func.sum()`, agrupados por status com
  `group_by()`, sem trazer os pedidos para o Python.
- **Um relatório por semestre:** uma `UniqueConstraint` (estagiário, ano,
  semestre) garante isso no próprio banco.
- **Ficou para depois:** a central de notificações foi avaliada e adiada
  porque, diferente das três acima, não tem base legal.

O registro dessas decisões, com data, está em
[`docs/decisoes.md`](docs/decisoes.md) (fase 3c).

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

São 90 casos em seis arquivos, todos num banco em memória (não mexem no
`dados.db`):

- `testes/test_calculo.py` — regras do dia (horas trabalhadas, almoço
  mínimo de 1h, pendência, ordem dos horários, limite legal).
- `testes/test_api.py` — requisições de verdade na API: registro e saldo,
  validação 422, fluxo completo de ajuste com aprovação do gestor, faltas do
  relatório, exportação PDF/Excel, aviso de limite legal semanal, chave do
  aplicativo e CORS restrito ao frontend.
- `testes/test_entrega3.py` — ponto rápido, edição da meta, tendência mês a
  mês, painéis, remoção de feriado, provedor de IA e modo demonstração.
- `testes/test_login.py` — senha em hash, sessão que vence e que acaba ao
  sair, limite de tentativas, e as regras de acesso: um estagiário não vê o
  outro, gestor só vê a própria equipe, só o dono pede ajuste, só o gestor
  responsável decide e altera a meta. Um teste percorre **todas** as rotas
  da API e confere que cada uma exige login, menos as abertas de propósito.
- `testes/test_novidades.py` — chamados (fila por prioridade, andamento que
  só vai para a frente), dia de prova (meta e limite pela metade no saldo,
  no relatório e na tendência), exportação `.ics` e crachá (verificação sem
  login, reemissão, desativação).
- `testes/test_estagio.py` — termo de no máximo 2 anos (e a exceção para
  pessoa com deficiência), aviso de fim de contrato, recesso proporcional,
  pedido de recesso (saldo, datas, choque de períodos), aprovação só pelo
  gestor responsável, recesso que não vira falta e o fluxo do relatório
  semestral (validação, semestre fechado, ciência e PDF).

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
1h, marca os dias de prova (que cobram metade da meta) com uma subconsulta
e soma todos os dias completos, sem trazer os registros para o Python. A
tendência mês a mês usa a mesma conta agrupada por mês (`saldo_por_mes`).

| # | Recurso | Para quê | Onde |
|---|---|---|---|
| 1 | `create_engine` + `event.listens_for` | Conexão com o SQLite e chave estrangeira ligada em cada conexão | `banco/conexao.py` |
| 2 | `declarative_base` | Classe `Base` de todos os modelos | `banco/conexao.py` → `modelos/` |
| 3 | `sessionmaker` / `Session` | Uma sessão por requisição (`Depends(get_session)`) | `banco/conexao.py`, todas as rotas |
| 4 | `Base.metadata.create_all` | Cria as tabelas quando a API sobe | `banco/conexao.py` |
| 5 | `Column` e tipos (`Integer`, `String`, `Float`, `Boolean`, `Date`, `Time`, `DateTime`) com `nullable`, `unique`, `index`, `default` | As 16 tabelas | `modelos/` |
| 6 | `ForeignKey` (com `unique=True` no 1-para-1) | Registro → estagiário, configuração/crachá/conta → estagiário, chamado → estagiário e gestor | `modelos/` |
| 7 | `relationship` com `back_populates`, `uselist=False`, `cascade`, `order_by` | Navegar entre estagiário, conta, configuração, registros, solicitações, chamados e mensagens | `modelos/` |
| 8 | `query().filter()` / `filter_by()` | Buscar por pessoa, data, status e token | rotas e serviços |
| 9 | `order_by()` e `.desc()` | Histórico em ordem; auditoria do mais recente para o mais antigo | `api/rotas/registros.py`, `servicos/solicitacao.py` |
| 10 | `join()` | Fila e auditoria do gestor: só pedidos da equipe dele | `servicos/solicitacao.py` |
| 11 | `func.sum()` e `func.count()` | Soma das horas e contagem de dias no banco | `servicos/saldo.py`, `servicos/painel.py` |
| 12 | `case()`, `func.cast()`, `func.strftime()` | Horário em segundos, almoço mínimo de 1h e dia de prova dentro da consulta; fila de chamados por prioridade | `servicos/saldo.py`, `servicos/chamados.py` |
| 13 | `group_by()` | Saldo mês a mês; chamados por status | `servicos/saldo.py`, `servicos/chamados.py` |
| 14 | `select()` como subconsulta + `in_()` | Datas de prova usadas dentro da soma do saldo | `servicos/agenda.py`, `servicos/saldo.py` |
| 15 | `extract("month"/"year")` | Registros de um mês | `api/rotas/relatorio.py` |
| 16 | `func.min()` / `func.max()` + `scalar()` | Primeiro ponto (faltas, início do estágio no crachá) e último ponto | `api/rotas/relatorio.py`, `servicos/cracha.py`, `servicos/painel.py` |
| 17 | `is_not(None)` / `is_(None)` | Só dias completos no saldo; achar dias com pendência | `servicos/saldo.py`, `servicos/painel.py` |
| 18 | `limit()` | Os últimos dias do painel | `servicos/painel.py` |
| 19 | `query().filter().delete()` | Apagar sessões vencidas ou derrubadas num comando só | `servicos/autenticacao.py` |
| 20 | `UniqueConstraint` em `__table_args__` | Um relatório semestral só por estagiário e semestre | `modelos/estagio.py` |
| 21 | `func.julianday()` dentro de `func.sum()` + `group_by()` | Dias de recesso somados no banco, por status | `servicos/estagio.py` |
| 22 | `add`, `add_all`, `delete`, `commit`, `rollback`, `refresh` + `SQLAlchemyError` | Gravar com integridade: ou grava tudo, ou nada (estagiário + configuração + conta numa transação) | rotas de criação, serviços, `popular_demo.py` |

## Estrutura

```
api/              # FastAPI: app, rotas por modulo, schemas Pydantic,
                  # regras de acesso (permissoes.py), chave do aplicativo
                  # e rate limiting (seguranca.py)
banco/            # engine e sessao do SQLAlchemy (conexao.py) + dados.db
modelos/          # classes mapeadas: Estagiario, Gestor, Configuracao,
                  # RegistroPonto, SolicitacaoAjuste, Feriado, Usuario,
                  # SessaoLogin, Chamado, MensagemChamado, Compromisso, Cracha,
                  # TermoCompromisso, PedidoRecesso, AtividadeEstagio,
                  # RelatorioAtividades
servicos/         # regras de negocio: calculo, saldo, ponto, painel,
                  # simulador, vencimento, feriados, solicitacao, assistente,
                  # exportacoes, autenticacao, chamados, agenda, cracha,
                  # estagio (termo, recesso, relatorio semestral)
testes/           # pytest (conftest.py tem o banco em memoria e os ajudantes de login)
frontend/         # interface em React (Vite), consome a API por HTTP
docs/             # registro das decisoes do grupo (decisoes.md)
popular_demo.py   # carga de dados e contas de exemplo
```

Cada arquivo do backend começa dizendo quem é o dono do módulo e quais
recursos do SQLAlchemy ele usa.

## Limitações conhecidas

- **Sem recuperação de senha por e-mail.** Quem esquecer a senha precisa de
  uma conta nova (ou de alguém com acesso ao banco). Enviar e-mail exigiria
  um servidor de e-mail, fora do escopo.
- **Integração com o Google Agenda é de mão única.** O InternHub manda os
  compromissos para o Google (link e `.ics`), mas não lê a agenda do Google.
  Ler exigiria login com conta Google (OAuth) e uma chave de projeto, e quem
  avaliar o trabalho não conseguiria testar.
- **SQLite e um processo só.** O banco é um arquivo local e os limites de
  requisições e de tentativas de login ficam em memória (zeram quando a API
  reinicia). Basta para uma equipe pequena.
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
ou trabalhista e compensação de horas (folga usando o crédito do banco).

## Histórico

A primeira interface foi feita em Streamlit e foi substituída pelo frontend
em React (o código antigo continua no histórico do Git). O login com senha
estava fora do escopo na Entrega 1 e entrou na Entrega 3, junto com os
chamados, a agenda, o crachá e o contrato de estágio (termo, recesso e
relatório de atividades). As decisões do grupo, com data e motivo,
estão em [`docs/decisoes.md`](docs/decisoes.md).
