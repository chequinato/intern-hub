// Alterna entre o tema claro e o escuro, aplicando o atributo data-tema no
// <html> - e o que estilos/tema.css usa para trocar as variaveis de cor.
// Na primeira visita segue a preferencia do sistema operacional; depois
// guarda a escolha no localStorage (so conveniencia, nada critico).

import { useEffect, useState } from "react";

const CHAVE_STORAGE = "internhub-tema";

function temaInicial() {
  try {
    const salvo = localStorage.getItem(CHAVE_STORAGE);
    if (salvo === "escuro" || salvo === "claro") return salvo;
  } catch {
    // sem storage: cai na preferencia do sistema
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
}

export function useTema() {
  const [tema, setTema] = useState(temaInicial);

  useEffect(() => {
    document.documentElement.dataset.tema = tema;
    try {
      localStorage.setItem(CHAVE_STORAGE, tema);
    } catch {
      // sem storage disponivel: o tema so nao sobrevive a um F5.
    }
  }, [tema]);

  return { escuro: tema === "escuro", alternar: () => setTema((t) => (t === "escuro" ? "claro" : "escuro")) };
}
