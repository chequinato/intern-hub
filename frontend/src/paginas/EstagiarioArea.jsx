import { NavLink, Outlet, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { useSessao } from "../context/SessaoContext";

const ABAS = [
  { rota: "", rotulo: "Registrar ponto" },
  { rota: "saldo", rotulo: "Saldo" },
  { rota: "relatorio", rotulo: "Relatorio" },
  { rota: "simulacao", rotulo: "Simulacao" },
  { rota: "solicitacoes", rotulo: "Solicitacoes" },
  { rota: "auditoria", rotulo: "Auditoria" },
  { rota: "assistente", rotulo: "Assistente de IA" },
];

// Cabecalho + navegacao da area do estagiario. Busca os dados da pessoa
// (nome, configuracao) uma vez aqui e entrega para as sub-paginas via
// contexto de rota do react-router (Outlet context), evitando repetir a
// mesma chamada GET /estagiarios/{id} em cada aba.
export function EstagiarioArea() {
  const { id } = useParams();
  const estagiarioId = Number(id);
  const navegar = useNavigate();
  const { sair } = useSessao();

  const { dados: estagiario, carregando, erro } = useApiState(
    () => api.get(`/estagiarios/${estagiarioId}`),
    [estagiarioId]
  );

  function trocarPessoa() {
    sair();
    navegar("/");
  }

  if (carregando) return <p className="empty" style={{ marginTop: 40 }}>Carregando...</p>;
  if (erro) return <p className="aviso aviso--erro" style={{ marginTop: 40 }}>{erro}</p>;

  return (
    <>
      <header className="masthead">
        <div>
          <h1 className="masthead-title">{estagiario.nome}</h1>
          <p className="masthead-sub">Estagiario #{estagiario.id}</p>
        </div>
        <div className="masthead-meta">
          <span>Meta diaria <b>{estagiario.configuracao?.meta_horas_diaria.toFixed(1)}h</b></span>
          <span>Meta semanal <b>{estagiario.configuracao?.meta_horas_semanal.toFixed(1)}h</b></span>
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
        <Outlet context={{ estagiario, estagiarioId }} />
      </div>
    </>
  );
}
