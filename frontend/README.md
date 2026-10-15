# InternHub — Frontend (React)

Interface web do InternHub, em React + Vite (JavaScript puro, sem
TypeScript). Fala com a API FastAPI (`api/app_api.py`, na raiz do projeto)
por HTTP, sem tocar no banco nem nos modelos diretamente.

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

- `src/App.jsx` — mapa de rotas. Cada tela é carregada só quando a pessoa
  entra nela (`React.lazy`).
- `src/api/cliente.js` — cliente HTTP único. Também traduz os erros da API
  para português (acentos, datas dd/mm/aaaa, decimal com vírgula).
- `src/paginas/Portal.jsx` — tela de entrada (escolha do perfil e da pessoa).
- `src/paginas/EstagiarioArea.jsx` / `GestorArea.jsx` — carregam a pessoa e
  o painel da API e montam a navegação de cada perfil.
- `src/paginas/estagiario/` — Início (painel), Ponto, Solicitações,
  Relatório, Simulação, Assistente e Configurações.
- `src/paginas/gestor/` — Equipe (painel), Aprovações, Feriados e Auditoria.
- `src/components/` — estrutura da página (barra lateral e superior), cartão
  de bater ponto, gráficos (recharts), notificações e peças pequenas
  (`Ui.jsx`: indicadores, selos, avatares, estados vazios).
- `src/estilos/` — `tema.css` (paleta grafite e laranja nos temas escuro e
  claro, fontes, tempos de animação), `base.css`, `componentes.css`,
  `estrutura.css` e `telas.css`.
- `src/components/VitrinePainel.jsx` — o painel inclinado e animado da tela
  de entrada (só ilustração, com números de exemplo).
- `src/utils/formato.js` — datas, horas ("6,5h", "6h30") e os nomes
  amigáveis dos campos da API.

## Build de produção

```
npm run build
```

Gera a pasta `dist/` (não é versionada).
