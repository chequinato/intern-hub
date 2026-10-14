// Cliente HTTP compartilhado por todas as telas.
//
// Monta a URL, manda o token (se houver um configurado), trata "API fora
// do ar" e traduz o erro da API (que vem em { detail: ... }) para uma
// mensagem em portugues, pronta para mostrar na tela.
//
// Uso:
//   const dados = await api.get("/estagiarios");
//   const criado = await api.post("/estagiarios", { nome, meta_horas_diaria });
// Em caso de erro, a Promise rejeita com um Error cuja .message ja vem em
// portugues - basta um try/catch (ou .catch) em quem chamou.

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const API_TOKEN = import.meta.env.VITE_API_TOKEN || "";

async function chamar(verbo, caminho, { payload, params } = {}) {
  const url = new URL(API_URL + caminho);
  if (params) {
    Object.entries(params).forEach(([chave, valor]) => {
      if (valor !== undefined && valor !== null && valor !== "") {
        url.searchParams.set(chave, valor);
      }
    });
  }

  const cabecalhos = { "Content-Type": "application/json" };
  if (API_TOKEN) cabecalhos.Authorization = `Bearer ${API_TOKEN}`;

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
    throw new Error(mensagemDoErro(resposta, corpo));
  }
  return corpo;
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
};

export function acentuar(texto) {
  return String(texto)
    .replace(/\b[A-Za-z]+\b/g, (palavra) => {
      const trocada = ACENTOS[palavra.toLowerCase()];
      if (!trocada) return palavra;
      return palavra[0] === palavra[0].toUpperCase() ? trocada[0].toUpperCase() + trocada.slice(1) : trocada;
    })
    // 2026-10-13 -> 13/10/2026 e 2.17h -> 2,17h (formato brasileiro)
    .replace(/(\d{4})-(\d{2})-(\d{2})/g, "$3/$2/$1")
    .replace(/(\d)\.(\d)/g, "$1,$2");
}

function mensagemDoErro(resposta, corpo) {
  const detalhe = corpo && typeof corpo === "object" ? corpo.detail : null;

  if (resposta.status === 401) {
    return "A API recusou o acesso (token inválido). Coloque o mesmo API_TOKEN do .env da raiz em VITE_API_TOKEN, no frontend/.env.";
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
  delete: (caminho) => chamar("DELETE", caminho),

  // Baixa um arquivo (PDF/Excel) e devolve o Blob pronto pra download.
  async baixarArquivo(caminho, params) {
    const url = new URL(API_URL + caminho);
    if (params) {
      Object.entries(params).forEach(([chave, valor]) => url.searchParams.set(chave, valor));
    }
    const cabecalhos = {};
    if (API_TOKEN) cabecalhos.Authorization = `Bearer ${API_TOKEN}`;

    const resposta = await fetch(url, { headers: cabecalhos });
    if (!resposta.ok) {
      const corpo = await resposta.json().catch(() => null);
      throw new Error(mensagemDoErro(resposta, corpo));
    }
    return resposta.blob();
  },
};
