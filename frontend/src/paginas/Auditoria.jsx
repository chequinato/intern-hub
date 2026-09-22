import { useOutletContext } from "react-router-dom";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { Estado } from "../components/Estado";

// Historico de solicitacoes de ajuste (funcionalidade 17). Reaproveitada
// nas duas areas: do estagiario (filtrada pelo proprio id, vinda do
// Outlet context) e do gestor (sem filtro - ve o historico de todo mundo).
export function Auditoria() {
  const contexto = useOutletContext() || {};
  const { estagiarioId } = contexto;

  const { dados, carregando, erro } = useApiState(
    () => api.get("/solicitacoes", estagiarioId ? { estagiario_id: estagiarioId } : undefined),
    [estagiarioId]
  );

  return (
    <>
      <div className="section-mark"><span className="name">Auditoria</span></div>
      {carregando && <p className="empty">Carregando...</p>}
      {erro && <p className="aviso aviso--erro">{erro}</p>}
      {!carregando && !erro && <Tabela solicitacoes={dados || []} mostrarEstagiario={!estagiarioId} />}
    </>
  );
}

function Tabela({ solicitacoes, mostrarEstagiario }) {
  if (solicitacoes.length === 0) return <p className="empty">Nenhuma solicitacao no historico.</p>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {mostrarEstagiario && <th>Estagiario</th>}
            <th>Data do registro</th>
            <th>Campo</th>
            <th>Sugerido</th>
            <th>Pedido em</th>
            <th>Gestor</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {solicitacoes.map((s, i) => (
            <tr key={s.id} style={{ "--i": i }}>
              {mostrarEstagiario && <td>{s.estagiario_nome}</td>}
              <td>{s.data_registro}</td>
              <td>{s.campo_alterado}</td>
              <td>{s.horario_sugerido.slice(0, 5)}</td>
              <td>{new Date(s.data_solicitacao).toLocaleDateString("pt-BR")}</td>
              <td>{s.gestor_nome || "-"}</td>
              <td><Estado status={s.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
