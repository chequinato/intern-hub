import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/cliente";
import { NumeroMecanico } from "../components/NumeroMecanico";

// "E se eu faltar / chegar atrasado": so projeta, nunca grava nada no
// banco (funcionalidade 8 do README).
export function Simulacao() {
  const { estagiarioId } = useOutletContext();
  const [diasFalta, setDiasFalta] = useState(0);
  const [horasAtraso, setHorasAtraso] = useState(0);
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState(null);
  const [calculando, setCalculando] = useState(false);

  async function simular(e) {
    e.preventDefault();
    setCalculando(true);
    setErro(null);
    try {
      const dados = await api.post("/simulacoes", {
        estagiario_id: estagiarioId,
        dias_falta: Number(diasFalta),
        horas_atraso: Number(horasAtraso),
      });
      setResultado(dados);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setCalculando(false);
    }
  }

  return (
    <>
      <div className="section-mark"><span className="name">Simular cenario</span></div>

      <form className="form card" onSubmit={simular}>
        <div className="campo-linha">
          <div className="campo">
            <label>Dias de falta</label>
            <input type="number" min="0" value={diasFalta} onChange={(e) => setDiasFalta(e.target.value)} />
          </div>
          <div className="campo">
            <label>Horas de atraso</label>
            <input type="number" min="0" step="0.5" value={horasAtraso} onChange={(e) => setHorasAtraso(e.target.value)} />
          </div>
        </div>
        {erro && <p className="aviso aviso--erro">{erro}</p>}
        <button type="submit" className="botao" disabled={calculando}>
          {calculando ? "Calculando..." : "Simular"}
        </button>
      </form>

      {resultado && (
        <div className="band" style={{ marginTop: 24 }}>
          <div className="band-grid">
            <div className="readout">
              <div className="readout-label">Saldo atual</div>
              <div className="readout-val"><NumeroMecanico valor={resultado.saldo_atual} casasDecimais={2} sufixo="h" /></div>
            </div>
            <div className="readout">
              <div className="readout-label">Impacto do cenario</div>
              <div className="readout-val readout-val--signal">
                <NumeroMecanico valor={resultado.impacto_horas} casasDecimais={2} sufixo="h" />
              </div>
            </div>
            <div className="readout">
              <div className="readout-label">Saldo projetado</div>
              <div className={`readout-val${resultado.saldo_projetado < 0 ? " readout-val--signal" : " readout-val--verde"}`}>
                <NumeroMecanico valor={resultado.saldo_projetado} casasDecimais={2} sufixo="h" />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
