import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { CircleAlert, CircleCheck, Info, X } from "lucide-react";

// Notificacoes que aparecem no canto da tela depois de uma acao ("Ponto
// registrado", "Pedido aprovado"). Qualquer tela chama:
//   const notificar = useNotificar();
//   notificar.sucesso("Ponto registrado", "Entrada às 09:02");
// e a mensagem some sozinha depois de alguns segundos.

const NotificacoesContext = createContext(null);

const ICONES = { sucesso: CircleCheck, erro: CircleAlert, info: Info };

export function NotificacoesProvider({ children }) {
  const [lista, setLista] = useState([]);

  const fechar = useCallback((id) => setLista((atual) => atual.filter((n) => n.id !== id)), []);

  const mostrar = useCallback(
    (tipo, titulo, texto) => {
      const id = Date.now() + Math.random();
      setLista((atual) => [...atual.slice(-2), { id, tipo, titulo, texto }]);
      setTimeout(() => fechar(id), tipo === "erro" ? 7000 : 4500);
    },
    [fechar]
  );

  const api = useMemo(
    () => ({
      sucesso: (titulo, texto) => mostrar("sucesso", titulo, texto),
      erro: (titulo, texto) => mostrar("erro", titulo, texto),
      info: (titulo, texto) => mostrar("info", titulo, texto),
    }),
    [mostrar]
  );

  return (
    <NotificacoesContext.Provider value={api}>
      {children}
      <div className="notificacoes" role="status" aria-live="polite">
        {lista.map((n) => {
          const Icone = ICONES[n.tipo];
          return (
            <div key={n.id} className={`notificacao notificacao--${n.tipo}`}>
              <Icone />
              <div>
                <strong>{n.titulo}</strong>
                {n.texto && <p>{n.texto}</p>}
              </div>
              <button type="button" onClick={() => fechar(n.id)} aria-label="Fechar">
                <X />
              </button>
            </div>
          );
        })}
      </div>
    </NotificacoesContext.Provider>
  );
}

export function useNotificar() {
  const contexto = useContext(NotificacoesContext);
  if (!contexto) throw new Error("useNotificar precisa estar dentro de <NotificacoesProvider>");
  return contexto;
}
