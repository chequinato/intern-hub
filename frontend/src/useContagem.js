// Faz um numero "contar" ate o valor novo em vez de trocar de uma vez:
// quando o saldo muda de 2,0h para 3,5h, a tela mostra 2,1... 2,8... 3,5.
// Usa requestAnimationFrame com uma curva que desacelera no fim.

import { useEffect, useRef, useState } from "react";

export function useContagem(alvo, duracao = 900) {
  const destino = Number(alvo ?? 0);
  const [valor, setValor] = useState(0);
  const atual = useRef(0);

  useEffect(() => {
    const inicio = atual.current;
    const diferenca = destino - inicio;
    if (diferenca === 0) return undefined;

    // Quem pediu menos movimento no sistema operacional ve o valor final direto.
    const semMovimento = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    let quadro;
    const comeco = performance.now();
    const passo = (agora) => {
      const t = semMovimento ? 1 : Math.min(1, (agora - comeco) / duracao);
      const suave = 1 - Math.pow(1 - t, 3);
      atual.current = inicio + diferenca * suave;
      setValor(atual.current);
      if (t < 1) quadro = requestAnimationFrame(passo);
    };
    quadro = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(quadro);
  }, [destino, duracao]);

  return valor;
}
