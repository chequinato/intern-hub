// Cliente HTTP compartilhado por todas as telas.
//
// Mesma ideia do paginas/cliente_api.py do Streamlit: monta a URL, manda o
// token (se houver um configurado), trata "API fora do ar" e traduz erro da
// API (que vem em { detail: ... }) para uma mensagem pronta de mostrar.
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
      `Nao consegui falar com a API em ${API_URL}. Confira se ela esta ` +
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

function mensagemDoErro(resposta, corpo) {
  const detalhe = corpo && typeof corpo === "object" ? corpo.detail : null;

  if (typeof detalhe === "string") return detalhe;

  // 422 do Pydantic: uma lista com um item por campo invalido.
  if (Array.isArray(detalhe)) {
    return "Dados invalidos: " + detalhe.map((item) => item.msg || "campo invalido").join("; ");
  }

  return `A API respondeu ${resposta.status}.`;
}

export const api = {
  get: (caminho, params) => chamar("GET", caminho, { params }),
  post: (caminho, payload) => chamar("POST", caminho, { payload }),
  patch: (caminho, payload) => chamar("PATCH", caminho, { payload }),

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
