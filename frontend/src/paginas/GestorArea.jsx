import { NavLink, Outlet, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { useSessao } from "../context/SessaoContext";

const ABAS = [
  { rota: "", rotulo: "Aprovacoes" },
  { rota: "auditoria", rotulo: "Auditoria" },
];

// Cabecalho + navegacao da area do gestor: fila de aprovacoes e auditoria
// geral (todos os estagiarios, nao so os dele).
export function GestorArea() {
  const { id } = useParams();
  const gestorId = Number(id);
  const navegar = useNavigate();
  const { sair } = useSessao();

  const { dados: gestor, carregando, erro } = useApiState(
    () => api.get("/gestores").then((lista) => lista.find((g) => g.id === gestorId)),
    [gestorId]
  );
  const { dados: equipe } = useApiState(() => api.get("/estagiarios"), []);

  function trocarPessoa() {
    sair();
    navegar("/");
  }

  if (carregando) return <p className="empty" style={{ marginTop: 40 }}>Carregando...</p>;
  if (erro || !gestor) return <p className="aviso aviso--erro" style={{ marginTop: 40 }}>Gestor nao encontrado.</p>;

  const sobGestao = (equipe || []).filter((p) => p.gestor_id === gestorId).length;

  return (
    <>
      <header className="masthead">
        <div>
          <h1 className="masthead-title">{gestor.nome}</h1>
          <p className="masthead-sub">Gestor #{gestor.id}</p>
        </div>
        <div className="masthead-meta">
          <span>Estagiarios sob gestao <b>{sobGestao}</b></span>
          <button type="button" className="masthead-sair" onClick={trocarPessoa}>Trocar pessoa</button>
        </div>
      </header>

      <nav className="nav">
        {ABAS.map((aba) => (
          <NavLink
            key={aba.rota}
            to={aba.rota}
            end={aba.rota === ""}
            className={({ isActive }) => `nav-item${isActive ? " on" : ""}`}
          >
            {aba.rotulo}
          </NavLink>
        ))}
      </nav>

      <div className="pagina">
        <Outlet context={{ gestorId }} />
      </div>
    </>
  );
}
