# InternHub — Banco de Horas do Estágio

Sistema para estagiários registrarem o ponto, acompanharem o saldo de
horas (banco de horas) e simularem cenários futuros. Projeto da disciplina
de Programação em Python, UniAnchieta 2026/2, construído em torno do
**SQLAlchemy** como biblioteca principal.

Arquitetura: uma API própria em **FastAPI** cobre todo o sistema (o único
lugar que fala com o banco) e um frontend em **React** consome essa API
por HTTP. Não existe acesso direto ao banco fora da API.

## Como rodar

São dois processos: a API e o frontend.

### 1. API (Python)

```
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env          # preencha OPENAI_API_KEY e API_TOKEN se quiser usar
uvicorn api.app_api:app --reload
```

Documentação interativa em `http://localhost:8000/docs`.

Sem `API_TOKEN` configurado no `.env`, a API roda aberta (sem exigir
token) — útil para desenvolvimento. Ver `api/seguranca.py`.

### 2. Frontend (React)

```
cd frontend
npm install
copy .env.example .env          # copie o mesmo API_TOKEN, se configurado
npm run dev
```

Abre em `http://localhost:5173`.

## Estrutura

```
api/            # FastAPI: rotas, schemas Pydantic, autenticacao/rate limit
banco/          # engine e sessao do SQLAlchemy
modelos/        # classes mapeadas (Estagiario, RegistroPonto, Configuracao...)
servicos/       # regras de negocio (calculo de horas, saldo, solicitacoes...)
testes/         # pytest
frontend/       # interface em React (Vite), consome a API por HTTP
```

## Funcionalidades

Registro de ponto com controle de almoço, cálculo de saldo (banco de
horas), alerta de saldo negativo, aviso de limite legal de horas do
estágio (Lei 11.788/2008 — 6h/dia, 30h/semana), relatório mensal com
gráfico e exportação em PDF/Excel, simulador de cenários, solicitação de
ajuste de ponto com aprovação do gestor, auditoria, calendário de
feriados, múltiplos estagiários, assistente de IA para dúvidas sobre
saldo, autenticação por token e rate limiting na API.

Detalhes de escopo, decisões de arquitetura e divisão de responsabilidades
do grupo estão nos documentos de entrega da disciplina.

## Testes

```
pytest testes/ -v
```
