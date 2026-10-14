// Hora atual que se atualiza sozinha (relogio do cartao de ponto).

import { useEffect, useState } from "react";

export function useAgora(intervalo = 1000) {
  const [agora, setAgora] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setAgora(new Date()), intervalo);
    return () => clearInterval(id);
  }, [intervalo]);
  return agora;
}
