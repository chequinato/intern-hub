import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { Estado } from "../components/Estado";

const CAMPOS = [
  { valor: "entrada", rotulo: "Entrada" },
  { valor: "saida", rotulo: "Saida" },
  { valor: "saida_almoco", rotulo: "Saida almoco" },
  { valor: "retorno_almoco", rotulo: "Retorno almoco" },
];

// Tela do estagiario: abrir um pedido de ajuste sobre um registro existente
// e acompanhar o status dos que ja abriu (funcionalidade 14 do README).
export function Solicitacoes() {
  const { estagiarioId } = useOutletContext();

  const { dados: registros } = useApiState(() => api.get(`/registros/${estagiarioId}`), [estagiarioId]);
  const { dados: solicitacoes, carregando, erro, recarregar } = useApiState(
    () => api.get("/solicitacoes", { estagiario_id: estagiarioId }),
    [estagiarioId]
  );

  return (
    <>
      <div className="section-mark"><span className="name">Abrir solicitacao</span></div>
      <FormularioSolicitacao registros={registros || []} onCriada={recarregar} />

      <div className="section-mark" style={{ marginTop: 32 }}><span className="name">Minhas solicitacoes</span></div>
      {carregando && <p className="empty">Carregando...</p>}
      {erro && <p className="aviso aviso--erro">{erro}</p>}
      {!carregando && !erro && <TabelaSolicitacoes solicitacoes={solicitacoes || []} />}
    </>
  );
}

function FormularioSolicitacao({ registros, onCriada }) {
  const [registroId, setRegistroId] = useState("");
  const [campo, setCampo] = useState("entrada");
  const [horario, setHorario] = useState("");
  const [justificativa, setJustificativa] = useState("");
  const [erro, setErro] = useState(null);
  const [enviando, setEnviando] = useState(false);

  const registrosRecentes = [...registros].reverse().slice(0, 20);

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await api.post("/solicitacoes", {
        registro_id: Number(registroId),
        campo_alterado: campo,
        horario_sugerido: horario,
        justificativa,
      });
      setRegistroId("");
      setHorario("");
      setJustificativa("");
      onCriada();
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  if (registrosRecentes.length === 0) {
    return <p className="empty">Registre algum ponto antes de pedir um ajuste.</p>;
  }

  return (
    <form className="form card" onSubmit={enviar}>
      <div className="campo-linha">
        <div className="campo">
          <label>Registro</label>
          <select value={registroId} onChange={(e) => setRegistroId(e.target.value)} required>
            <option value="" disabled>Escolha o dia...</option>
            {registrosRecentes.map((r) => (
              <option key={r.id} value={r.id}>{r.data} {r.pendencia ? "(pendencia)" : ""}</option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label>Campo a corrigir</label>
          <select value={campo} onChange={(e) => setCampo(e.target.value)}>
            {CAMPOS.map((c) => <option key={c.valor} value={c.valor}>{c.rotulo}</option>)}
          </select>
        </div>
        <div className="campo">
          <label>Horario correto</label>
          <input type="time" value={horario} onChange={(e) => setHorario(e.target.value)} required />
        </div>
      </div>
      <div className="campo">
        <label>Justificativa</label>
        <textarea rows={2} value={justificativa} onChange={(e) => setJustificativa(e.target.value)} minLength={5} maxLength={300} required />
      </div>
      {erro && <p className="aviso aviso--erro">{erro}</p>}
      <button type="submit" className="botao" disabled={enviando}>
        {enviando ? "Enviando..." : "Enviar pedido"}
      </button>
    </form>
  );
}

function TabelaSolicitacoes({ solicitacoes }) {
  if (solicitacoes.length === 0) return <p className="empty">Nenhuma solicitacao ainda.</p>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Data do registro</th>
            <th>Campo</th>
            <th>De</th>
            <th>Para</th>
            <th>Justificativa</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {solicitacoes.map((s, i) => (
            <tr key={s.id} style={{ "--i": i }}>
              <td>{s.data_registro}</td>
              <td>{s.campo_alterado}</td>
              <td>{(s.horario_atual || "-").slice(0, 5)}</td>
              <td>{s.horario_sugerido.slice(0, 5)}</td>
              <td style={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.justificativa}</td>
              <td><Estado status={s.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
