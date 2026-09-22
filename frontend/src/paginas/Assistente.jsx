import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/cliente";

// Chat com o assistente de IA: manda a pergunta, a API busca os dados reais
// (saldo, simulacao) e devolve a resposta pronta. O historico fica so no
// componente (nao precisa persistir - se recarregar a pagina, comeca do
// zero, igual o st.session_state do Streamlit original fazia por sessao).
export function Assistente() {
  const { estagiarioId } = useOutletContext();
  const [historico, setHistorico] = useState([]);
  const [pergunta, setPergunta] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar(e) {
    e.preventDefault();
    const texto = pergunta.trim();
    if (texto.length < 3) return;

    setHistorico((h) => [...h, { autor: "voce", texto }]);
    setPergunta("");
    setEnviando(true);
    setErro(null);
    try {
      const resposta = await api.post("/assistente/perguntar", { estagiario_id: estagiarioId, pergunta: texto });
      setHistorico((h) => [...h, { autor: "assistente", texto: resposta.resposta }]);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      <div className="section-mark"><span className="name">Assistente de IA</span></div>

      <div className="card" style={{ minHeight: 260, display: "flex", flexDirection: "column", gap: 14 }}>
        {historico.length === 0 && (
          <p className="empty">Pergunte sobre seu saldo ou cenarios hipoteticos.</p>
        )}
        {historico.map((msg, i) => (
          <div key={i} className="rv" style={{ "--i": i, alignSelf: msg.autor === "voce" ? "flex-end" : "flex-start", maxWidth: "80%" }}>
            <div className="mono-label" style={{ marginBottom: 4 }}>{msg.autor === "voce" ? "Voce" : "Assistente"}</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 13.5, color: "var(--ink-70)" }}>{msg.texto}</div>
          </div>
        ))}
      </div>

      {erro && <p className="aviso aviso--erro">{erro}</p>}

      <form className="form" style={{ flexDirection: "row", marginTop: 16 }} onSubmit={enviar}>
        <input
          style={{ flex: 1, border: "1px solid var(--rule)", background: "var(--paper)", padding: "10px 12px", fontFamily: "var(--mono)" }}
          value={pergunta}
          onChange={(e) => setPergunta(e.target.value)}
          placeholder="Qual meu saldo atual?"
          minLength={3}
          maxLength={500}
        />
        <button type="submit" className="botao" style={{ marginLeft: 10 }} disabled={enviando}>
          {enviando ? "..." : "Enviar"}
        </button>
      </form>
    </>
  );
}
