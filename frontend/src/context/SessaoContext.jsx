// Guarda quem esta usando o sistema agora: o perfil escolhido (estagiario
// ou gestor) e o id da pessoa. Equivalente ao st.session_state do Streamlit
// (app.py), so que em React.
//
// Fica salvo no localStorage para sobreviver a um F5 - e so uma conveniencia
// de navegacao (nao e autenticacao: qualquer um pode trocar de "estagiario
// selecionado" pelo seletor, igual no Streamlit original).

import { createContext, useContext, useEffect, useState } from "react";

const SessaoContext = createContext(null);

const CHAVE_STORAGE = "internhub-sessao";

function lerSessaoSalva() {
  try {
    const bruto = localStorage.getItem(CHAVE_STORAGE);
    return bruto ? JSON.parse(bruto) : {};
  } catch {
    return {};
  }
}

export function SessaoProvider({ children }) {
  const [sessao, setSessao] = useState(lerSessaoSalva);

  useEffect(() => {
    try {
      localStorage.setItem(CHAVE_STORAGE, JSON.stringify(sessao));
    } catch {
      // localStorage indisponivel (aba anonima, etc) - a sessao continua
      // funcionando normalmente, so nao sobrevive a um F5.
    }
  }, [sessao]);

  const valor = {
    perfil: sessao.perfil ?? null,
    estagiarioId: sessao.estagiarioId ?? null,
    gestorId: sessao.gestorId ?? null,
    escolherEstagiario: (id) => setSessao({ perfil: "estagiario", estagiarioId: id }),
    escolherGestor: (id) => setSessao({ perfil: "gestor", gestorId: id }),
    sair: () => setSessao({}),
  };

  return <SessaoContext.Provider value={valor}>{children}</SessaoContext.Provider>;
}

export function useSessao() {
  const contexto = useContext(SessaoContext);
  if (!contexto) throw new Error("useSessao precisa estar dentro de <SessaoProvider>");
  return contexto;
}
