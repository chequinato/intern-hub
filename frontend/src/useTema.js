// Alterna entre "papel" (claro) e "modo tinta" (escuro), aplicando o
// atributo data-mode no <html> - e o que index.css usa para trocar as
// variaveis de cor. Guarda a escolha no localStorage so como conveniencia
// (lembrar o tema na proxima visita), nada critico.

import { useEffect, useState } from "react";

const CHAVE_STORAGE = "internhub-tema";

export function useTema() {
  const [modoTinta, setModoTinta] = useState(() => {
    try {
      return localStorage.getItem(CHAVE_STORAGE) === "ink";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    document.documentElement.dataset.mode = modoTinta ? "ink" : "paper";
    try {
      localStorage.setItem(CHAVE_STORAGE, modoTinta ? "ink" : "paper");
    } catch {
      // sem storage disponivel: o tema so nao sobrevive a um F5.
    }
  }, [modoTinta]);

  return { modoTinta, alternar: () => setModoTinta((atual) => !atual) };
}
