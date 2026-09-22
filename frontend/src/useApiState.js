// Roda uma chamada de API e guarda o resultado, o estado de carregamento e
// o erro (ja em portugues, pronto pra mostrar). Evita repetir esse mesmo
// try/catch/useState em cada pagina - a mesma ideia do padrao
// "dados, erro = cliente_api.get(...)" do Streamlit, adaptada pro React.
//
// carregar() e memorizado (useCallback) para poder entrar no array de
// dependencias de um useEffect sem disparar um loop infinito.

import { useCallback, useEffect, useState } from "react";

export function useApiState(chamada, dependencias = []) {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);

  const carregar = useCallback(() => {
    setCarregando(true);
    setErro(null);
    chamada()
      .then(setDados)
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencias);

  useEffect(() => {
    carregar();
  }, [carregar]);

  return { dados, carregando, erro, recarregar: carregar, setDados };
}
