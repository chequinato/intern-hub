// Cliente HTTP compartilhado por todas as telas.
//
// Monta a URL, manda os dois cabecalhos de acesso, trata "API fora do ar"
// e traduz o erro da API (que vem em { detail: ... }) para uma mensagem em
// portugues, pronta para mostrar na tela.
//
// Os dois cabecalhos (Entrega 3):
//   X-API-Key      a chave do APLICATIVO (VITE_API_TOKEN), igual para todos
//   Authorization  o token do LOGIN de quem esta usando ("Bearer ...")
// O token do login fica no localStorage (ver context/SessaoContext.jsx) e e
// lido aqui a cada chamada, entao entrar e sair valem na hora.
//
// Uso:
//   const dados = await api.get("/estagiarios");
//   const criado = await api.post("/estagiarios", { nome, meta_horas_diaria });
// Em caso de erro, a Promise rejeita com um Error cuja .message ja vem em
// portugues - basta um try/catch (ou .catch) em quem chamou.

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const API_TOKEN = import.meta.env.VITE_API_TOKEN || "";
export const CHAVE_LOGIN = "internhub-login";

// Quem esta logado registra aqui o que fazer quando a sessao vence (a API
// responde 401): volta para a tela de login em vez de mostrar erro solto.
let aoSessaoExpirar = () => {};
export function quandoSessaoExpirar(funcao) {
  aoSessaoExpirar = funcao;
}

function tokenDoLogin() {
  try {
    return JSON.parse(localStorage.getItem(CHAVE_LOGIN) || "{}").token || "";
  } catch {
    return "";
  }
}

function cabecalhosDeAcesso() {
  const cabecalhos = {};
  if (API_TOKEN) cabecalhos["X-API-Key"] = API_TOKEN;
  const token = tokenDoLogin();
  if (token) cabecalhos.Authorization = `Bearer ${token}`;
  return cabecalhos;
}

async function chamar(verbo, caminho, { payload, params } = {}) {
  const url = new URL(API_URL + caminho);
  if (params) {
    Object.entries(params).forEach(([chave, valor]) => {
      if (valor !== undefined && valor !== null && valor !== "") {
        url.searchParams.set(chave, valor);
      }
    });
  }

  const cabecalhos = { "Content-Type": "application/json", ...cabecalhosDeAcesso() };

  let resposta;
  try {
    resposta = await fetch(url, {
      method: verbo,
      headers: cabecalhos,
      body: payload !== undefined ? JSON.stringify(payload) : undefined,
    });
  } catch {
    throw new Error(
      `Não foi possível falar com a API em ${API_URL}. Confira se ela está ` +
        "rodando (uvicorn api.app_api:app --reload)."
    );
  }

  if (resposta.status === 204) return null;

  const tipoDoConteudo = resposta.headers.get("content-type") || "";
  const ehJson = tipoDoConteudo.includes("application/json");
  const corpo = ehJson ? await resposta.json().catch(() => null) : await resposta.blob();

  if (!resposta.ok) {
    avisarSeSessaoVenceu(resposta, corpo, caminho);
    throw new Error(mensagemDoErro(resposta, corpo));
  }
  return corpo;
}

// 401 que nao e da chave do aplicativo nem da propria tela de login = o
// token do login venceu ou foi encerrado.
function avisarSeSessaoVenceu(resposta, corpo, caminho) {
  const detalhe = corpo && typeof corpo === "object" ? String(corpo.detail || "") : "";
  if (resposta.status === 401 && !detalhe.includes("X-API-Key") && caminho !== "/auth/entrar") {
    aoSessaoExpirar();
  }
}

// As mensagens da API sao escritas sem acento (o codigo Python do grupo
// evita acentos). Aqui elas ganham acentuacao antes de chegar na tela.
const ACENTOS = {
  nao: "não", saida: "saída", almoco: "almoço", horario: "horário", horarios: "horários",
  estagiario: "estagiário", estagiarios: "estagiários", solicitacao: "solicitação",
  solicitacoes: "solicitações", ja: "já", possivel: "possível", configuracao: "configuração",
  invalido: "inválido", invalida: "inválida", ate: "até", voce: "você", atencao: "atenção",
  credito: "crédito", decisao: "decisão", gestao: "gestão", minimo: "mínimo", ha: "há",
  sera: "será", tambem: "também", periodo: "período", util: "útil",
  sessao: "sessão", permissao: "permissão", so: "só", proprio: "próprio", propria: "própria",
  inicio: "início", faca: "faça", codigo: "código", cracha: "crachá", estagio: "estágio",
  disponiveis: "disponíveis", ciencia: "ciência", avaliacao: "avaliação",
  relatorio: "relatório", ultimo: "último",
};

export function acentuar(texto) {
  return String(texto)
    .replace(/\b[A-Za-z]+\b/g, (palavra) => {
      const trocada = ACENTOS[palavra.toLowerCase()];
      if (!trocada) return palavra;
      return palavra[0] === palavra[0].toUpperCase() ? trocada[0].toUpperCase() + trocada.slice(1) : trocada;
    })
    // 2026-10-13 -> 13/10/2026 e 2.17h -> 2,17h (formato brasileiro). So
    // decimais de ate 2 casas: "Lei 11.788" continua com ponto.
    .replace(/(\d{4})-(\d{2})-(\d{2})/g, "$3/$2/$1")
    .replace(/(\d)\.(\d{1,2})(?!\d)/g, "$1,$2");
}

function mensagemDoErro(resposta, corpo) {
  const detalhe = corpo && typeof corpo === "object" ? corpo.detail : null;

  if (resposta.status === 401 && typeof detalhe === "string" && detalhe.includes("X-API-Key")) {
    return "A API recusou a chave do aplicativo. Coloque o mesmo API_TOKEN do .env da raiz em VITE_API_TOKEN, no frontend/.env.";
  }
  if (resposta.status === 429) {
    return "Muitas requisições em pouco tempo. Aguarde alguns segundos e tente de novo.";
  }
  if (typeof detalhe === "string") return acentuar(detalhe);

  // 422 do Pydantic: uma lista com um item por campo invalido.
  if (Array.isArray(detalhe)) {
    return detalhe
      .map((item) => acentuar(String(item.msg || "campo inválido").replace(/^Value error, /, "")))
      .map((texto) => texto.charAt(0).toUpperCase() + texto.slice(1))
      .join(". ");
  }

  return `A API respondeu com erro ${resposta.status}.`;
}

export const api = {
  get: (caminho, params) => chamar("GET", caminho, { params }),
  post: (caminho, payload) => chamar("POST", caminho, { payload }),
  patch: (caminho, payload) => chamar("PATCH", caminho, { payload }),
  put: (caminho, payload) => chamar("PUT", caminho, { payload }),
  delete: (caminho) => chamar("DELETE", caminho),

  // Baixa um arquivo (PDF/Excel) e devolve o Blob pronto pra download.
  async baixarArquivo(caminho, params) {
    const url = new URL(API_URL + caminho);
    if (params) {
      Object.entries(params).forEach(([chave, valor]) => url.searchParams.set(chave, valor));
    }
    const resposta = await fetch(url, { headers: cabecalhosDeAcesso() });
    if (!resposta.ok) {
      const corpo = await resposta.json().catch(() => null);
      avisarSeSessaoVenceu(resposta, corpo, caminho);
      throw new Error(mensagemDoErro(resposta, corpo));
    }
    return resposta.blob();
  },
};
