import { Outlet } from "react-router-dom";
import { useTema } from "../useTema";

// Composicao base de toda pagina logada: trilho fixo a esquerda (marca do
// sistema + tema) e a folha a direita, onde cada rota renderiza o proprio
// conteudo (via <Outlet/>). O cabecalho especifico de cada area (estagiario
// ou gestor) fica em Cabecalho.jsx, dentro da folha.
export function Layout() {
  const { modoTinta, alternar } = useTema();

  return (
    <div className="frame">
      <aside className="rail">
        <span className="rail-word">InternHub</span>
        <div className="rail-spacer" />
        <button
          type="button"
          className="invert"
          onClick={alternar}
          aria-label="Alternar tema"
          title={modoTinta ? "Modo papel" : "Modo tinta"}
        />
      </aside>
      <div className="sheet">
        <Outlet />
      </div>
    </div>
  );
}
