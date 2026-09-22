# InternHub — Frontend (React)

Interface web do InternHub, em React + Vite (JavaScript puro, sem
TypeScript). Substitui o dashboard em Streamlit: fala com a mesma API
FastAPI (`api/app_api.py`, na raiz do projeto) por HTTP, sem tocar no
banco nem nos modelos diretamente.

## Como rodar

A API precisa estar no ar antes (na raiz do projeto):

```
uvicorn api.app_api:app --reload
```

Depois, na pasta `frontend/`:

```
npm install
npm run dev
```

Abre em `http://localhost:5173`.

## Configuração

Copie `.env.example` para `.env` e ajuste se precisar:

- `VITE_API_URL` — endereço da API (padrão `http://localhost:8000`).
- `VITE_API_TOKEN` — mesmo valor do `API_TOKEN` do `.env` da raiz, se a
  autenticação por token estiver ativada (`api/seguranca.py`). Deixe vazio
  se a API estiver rodando sem token configurado.

## Estrutura

- `src/api/cliente.js` — cliente HTTP único, usado por todas as telas.
- `src/context/SessaoContext.jsx` — guarda quem está usando o sistema
  (estagiário ou gestor selecionado), equivalente ao `st.session_state`
  do Streamlit original.
- `src/components/` — peças reutilizáveis (layout, número animado, selo
  de status).
- `src/paginas/` — uma tela por arquivo, na mesma divisão de
  funcionalidades do `DIVISAO_RESPONSABILIDADES.md`.
- `src/index.css` / `src/layout.css` — sistema visual do projeto (tokens
  de cor, tipografia, composição), na mesma linguagem do projeto de
  referência de design (papel + telemetria).

## Build de produção

```
npm run build
```

Gera a pasta `dist/` (não é versionada).
