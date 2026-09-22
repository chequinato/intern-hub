import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";

// Fila de pedidos pendentes dos estagiarios sob a gestao deste gestor.
// Aprovar aplica o horario no RegistroPonto e recalcula o saldo; rejeitar
// so fecha o pedido, sem tocar no registro (README, secao 3.4).
export function Aprovacoes() {
  const { gestorId } = useOutletContext();
  const { dados: pendentes, carregando, erro, recarregar } = useApiState(
    () => api.get("/solicitacoes/pendentes", { gestor_id: gestorId }),
    [gestorId]
  );
  const [mensagem, setMensagem] = useState(null);

  async function decidir(solicitacaoId, status) {
    setMensagem(null);
    try {
      const resultado = await api.patch(`/solicitacoes/${solicitacaoId}`, { status, gestor_id: gestorId });
      setMensagem({ tipo: status === "aprovado" ? "ok" : "erro", texto: resultado.mensagem });
      recarregar();
    } catch (e) {
      setMensagem({ tipo: "erro", texto: e.message });
    }
  }

  return (
    <>
      <div className="section-mark"><span className="name">Pedidos pendentes</span></div>

      {mensagem && <p className={`aviso ${mensagem.tipo === "erro" ? "aviso--erro" : "aviso--ok"}`}>{mensagem.texto}</p>}
      {carregando && <p className="empty">Carregando...</p>}
      {erro && <p className="aviso aviso--erro">{erro}</p>}
      {!carregando && !erro && (pendentes || []).length === 0 && (
        <p className="empty">Nenhum pedido pendente.</p>
      )}

      {!carregando && !erro && (pendentes || []).length > 0 && (
        <div className="grade">
          {pendentes.map((s, i) => (
            <div key={s.id} className="card rv" style={{ "--i": i }}>
              <div className="mono-label">{s.estagiario_nome} · {s.data_registro}</div>
              <p style={{ marginTop: 8, fontFamily: "var(--display)", fontWeight: 700, fontSize: 18 }}>
                {s.campo_alterado}: {(s.horario_atual || "--:--").slice(0, 5)} <span style={{ color: "var(--ink-45)" }}>&rarr;</span> {s.horario_sugerido.slice(0, 5)}
              </p>
              <p style={{ marginTop: 8, fontSize: 13, color: "var(--ink-70)" }}>{s.justificativa}</p>
              <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                <button type="button" className="botao" onClick={() => decidir(s.id, "aprovado")}>Aprovar</button>
                <button type="button" className="botao botao--signal" onClick={() => decidir(s.id, "rejeitado")}>Rejeitar</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
