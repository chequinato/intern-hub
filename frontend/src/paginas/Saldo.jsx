import { useOutletContext } from "react-router-dom";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { NumeroMecanico } from "../components/NumeroMecanico";

// Saldo acumulado (banco de horas) em uma faixa de telemetria - a mesma
// linguagem visual do resumo do dia do vero-webhook, com o numero em
// contador mecanico (README de design).
export function Saldo() {
  const { estagiarioId } = useOutletContext();
  const { dados, carregando, erro } = useApiState(
    () => api.get(`/saldo/${estagiarioId}`),
    [estagiarioId]
  );

  if (carregando) return <p className="empty">Carregando...</p>;
  if (erro) return <p className="aviso aviso--erro">{erro}</p>;

  const positivo = dados.saldo_acumulado >= 0;

  return (
    <>
      <div className="section-mark"><span className="name">Banco de horas</span></div>

      <div className="band">
        <div className="band-grid">
          <div className="readout">
            <div className="readout-label">Saldo acumulado</div>
            <div className={`readout-val${dados.em_alerta ? " readout-val--signal" : positivo ? " readout-val--verde" : ""}`}>
              <NumeroMecanico valor={dados.saldo_acumulado} casasDecimais={2} sufixo="h" />
            </div>
            <div className="readout-sub">{positivo ? "Credito" : "A compensar"}</div>
          </div>
          <div className="readout">
            <div className="readout-label">Dias registrados</div>
            <div className="readout-val"><NumeroMecanico valor={dados.dias_registrados} /></div>
            <div className="readout-sub">Dias completos no banco</div>
          </div>
          <div className="readout">
            <div className="readout-label">Limite de alerta</div>
            <div className="readout-val readout-val--amber">
              <NumeroMecanico valor={dados.limite_alerta} casasDecimais={1} sufixo="h" />
            </div>
            <div className="readout-sub">{dados.em_alerta ? "Alerta disparado" : "Dentro do limite"}</div>
          </div>
        </div>
      </div>

      {dados.em_alerta && (
        <p className="aviso aviso--erro">
          Saldo negativo passou do limite de alerta ({dados.limite_alerta}h). Procure regularizar as horas.
        </p>
      )}
    </>
  );
}
