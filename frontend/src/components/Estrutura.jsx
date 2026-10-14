import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { ArrowLeftRight, ChevronRight, Clock, Menu, Moon, Sun, X } from "lucide-react";
import { api } from "../api/cliente";
import { useSessao } from "../context/SessaoContext";
import { useTema } from "../useTema";
import { dataPorExtenso } from "../utils/formato";
import { Avatar } from "./Ui";
import { Logo } from "./Logo";

// Moldura de toda pagina logada: barra lateral (marca, pessoa, navegacao,
// tema, trocar perfil) + barra superior (titulo da pagina e relogio) + a
// area onde cada rota desenha o proprio conteudo (<Outlet />).
//
// `itens` vem da area (estagiario ou gestor):
//   [{ rota: "ponto", rotulo: "Ponto", icone: Clock, contador: 2, grupo: "Dia a dia" }]
export function Estrutura({ base, pessoa, papel, itens, contexto }) {
  const { alternar, escuro } = useTema();
  const { sair } = useSessao();
  const navegar = useNavigate();
  const local = useLocation();
  const [gavetaAberta, setGavetaAberta] = useState(false);
  const apiNoAr = useApiNoAr();

  const itemAtual =
    itens.find((item) => item.rota && local.pathname.startsWith(`${base}/${item.rota}`)) ||
    itens.find((item) => item.rota === "");

  function trocarPerfil() {
    sair();
    navegar("/");
  }

  return (
    <div className={`app${gavetaAberta ? " gaveta-aberta" : ""}`}>
      <aside className="lateral" aria-label="Navegação principal">
        <div className="marca">
          <Logo />
          <div className="marca-nome">InternHub<span>Banco de horas do estágio</span></div>
        </div>

        <div className="perfil-lateral">
          <Avatar nome={pessoa} tamanho={34} />
          <div style={{ minWidth: 0 }}>
            <div className="nome">{pessoa}</div>
            <div className="papel">{papel}</div>
          </div>
        </div>

        <nav className="nav">
          {itens.map((item, indice) => {
            const Icone = item.icone;
            // Titulo do grupo so no primeiro item de cada grupo.
            const titulo = item.grupo && item.grupo !== itens[indice - 1]?.grupo ? item.grupo : null;
            return (
              <div key={item.rota} style={{ display: "contents" }}>
                {titulo && <div className="nav-grupo">{titulo}</div>}
                <NavLink
                  to={item.rota ? `${base}/${item.rota}` : base}
                  end={item.rota === ""}
                  className={({ isActive }) => (isActive ? "ativo" : "")}
                  onClick={() => setGavetaAberta(false)}
                >
                  <Icone />
                  <span>{item.rotulo}</span>
                  {item.contador > 0 && <span className="contador">{item.contador}</span>}
                </NavLink>
              </div>
            );
          })}
        </nav>

        <div className="lateral-rodape">
          <button type="button" onClick={alternar}>
            {escuro ? <Sun /> : <Moon />}
            {escuro ? "Tema claro" : "Tema escuro"}
          </button>
          <button type="button" onClick={trocarPerfil}>
            <ArrowLeftRight />
            Trocar perfil
          </button>
          <div className={`status-api${apiNoAr === false ? " fora" : ""}`}>
            <i />
            {apiNoAr === false ? "API fora do ar" : "API conectada"}
          </div>
        </div>
      </aside>

      <div className="veu" onClick={() => setGavetaAberta(false)} />

      <div className="principal">
        <header className="topo">
          <button
            type="button"
            className="botao botao--fantasma botao--icone topo-menu"
            onClick={() => setGavetaAberta((v) => !v)}
            aria-label={gavetaAberta ? "Fechar menu" : "Abrir menu"}
          >
            {gavetaAberta ? <X /> : <Menu />}
          </button>
          <div className="topo-titulo">
            <div className="trilha">
              {papel}
              <ChevronRight />
              {itemAtual?.rotulo}
            </div>
            <h1>{itemAtual?.titulo || itemAtual?.rotulo}</h1>
          </div>
          <div className="topo-acoes">
            <Relogio />
          </div>
        </header>

        <main className="conteudo" key={local.pathname}>
          <Outlet context={contexto} />
        </main>
      </div>
    </div>
  );
}

function Relogio() {
  const [agora, setAgora] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setAgora(new Date()), 1000 * 15);
    return () => clearInterval(id);
  }, []);
  const horaTexto = `${String(agora.getHours()).padStart(2, "0")}:${String(agora.getMinutes()).padStart(2, "0")}`;
  return (
    <span className="relogio-topo">
      <Clock />
      <span className="data-longa">{dataPorExtenso(agora)}</span>
      <b className="mono">{horaTexto}</b>
    </span>
  );
}

// Confere a rota de saude "/" da API a cada 30 segundos.
function useApiNoAr() {
  const [noAr, setNoAr] = useState(null);
  useEffect(() => {
    let ativo = true;
    const conferir = () =>
      api.get("/").then(() => ativo && setNoAr(true)).catch(() => ativo && setNoAr(false));
    conferir();
    const id = setInterval(conferir, 30000);
    return () => {
      ativo = false;
      clearInterval(id);
    };
  }, []);
  return noAr;
}
