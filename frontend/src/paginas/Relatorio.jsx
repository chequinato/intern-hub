import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { NumeroMecanico } from "../components/NumeroMecanico";

const MESES = [
  "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

function agora() {
  const hoje = new Date();
  return { mes: hoje.getMonth() + 1, ano: hoje.getFullYear() };
}

// Relatorio mensal: totais do mes + grafico de evolucao do saldo diario
// + exportacao em PDF/Excel (funcionalidade 9 do README).
export function Relatorio() {
  const { estagiarioId } = useOutletContext();
  const [{ mes, ano }, setPeriodo] = useState(agora());
  const [baixando, setBaixando] = useState(null);
  const [erroExport, setErroExport] = useState(null);

  const { dados, carregando, erro } = useApiState(
    () => api.get(`/relatorio/${estagiarioId}`, { mes, ano }),
    [estagiarioId, mes, ano]
  );

  async function exportar(formato) {
    setBaixando(formato);
    setErroExport(null);
    try {
      const blob = await api.baixarArquivo(`/relatorio/${estagiarioId}/exportar`, { mes, ano, formato });
      const extensao = formato === "pdf" ? "pdf" : "xlsx";
      dispararDownload(blob, `relatorio_${estagiarioId}_${mes}_${ano}.${extensao}`);
    } catch (e) {
      setErroExport(e.message);
    } finally {
      setBaixando(null);
    }
  }

  return (
    <>
      <div className="section-mark"><span className="name">Relatorio mensal</span></div>

      <div className="campo-linha" style={{ maxWidth: 340, marginBottom: 20 }}>
        <div className="campo">
          <label>Mes</label>
          <select value={mes} onChange={(e) => setPeriodo((p) => ({ ...p, mes: Number(e.target.value) }))}>
            {MESES.map((nome, i) => <option key={i} value={i + 1}>{nome}</option>)}
          </select>
        </div>
        <div className="campo">
          <label>Ano</label>
          <input type="number" value={ano} onChange={(e) => setPeriodo((p) => ({ ...p, ano: Number(e.target.value) }))} />
        </div>
      </div>

      {carregando && <p className="empty">Carregando...</p>}
      {erro && <p className="aviso aviso--erro">{erro}</p>}

      {!carregando && !erro && dados && (
        <>
          <div className="band">
            <div className="band-grid">
              <div className="readout">
                <div className="readout-label">Horas trabalhadas</div>
                <div className="readout-val"><NumeroMecanico valor={dados.total_horas_trabalhadas} casasDecimais={1} sufixo="h" /></div>
              </div>
              <div className="readout">
                <div className="readout-label">Dias trabalhados</div>
                <div className="readout-val"><NumeroMecanico valor={dados.dias_uteis_trabalhados} /></div>
              </div>
              <div className="readout">
                <div className="readout-label">Faltas</div>
                <div className={`readout-val${dados.faltas > 0 ? " readout-val--amber" : ""}`}>
                  <NumeroMecanico valor={dados.faltas} />
                </div>
              </div>
              <div className="readout">
                <div className="readout-label">Saldo acumulado</div>
                <div className={`readout-val${dados.saldo_acumulado < 0 ? " readout-val--signal" : " readout-val--verde"}`}>
                  <NumeroMecanico valor={dados.saldo_acumulado} casasDecimais={2} sufixo="h" />
                </div>
              </div>
            </div>
          </div>

          {dados.aviso_vencimento && <p className="aviso">{dados.aviso_vencimento}</p>}

          <div className="section-mark" style={{ marginTop: 24 }}><span className="name">Evolucao do saldo diario</span></div>
          <GraficoEvolucao dados={dados.evolucao_diaria} />

          <div className="section-mark" style={{ marginTop: 28 }}><span className="name">Exportar</span></div>
          {erroExport && <p className="aviso aviso--erro">{erroExport}</p>}
          <div style={{ display: "flex", gap: 12 }}>
            <button type="button" className="botao" disabled={baixando === "pdf"} onClick={() => exportar("pdf")}>
              {baixando === "pdf" ? "Gerando..." : "Baixar PDF"}
            </button>
            <button type="button" className="botao" disabled={baixando === "excel"} onClick={() => exportar("excel")}>
              {baixando === "excel" ? "Gerando..." : "Baixar Excel"}
            </button>
          </div>
        </>
      )}
    </>
  );
}

function GraficoEvolucao({ dados }) {
  if (!dados || dados.length === 0) return <p className="empty">Sem registros neste periodo.</p>;

  const serie = dados.map((d) => ({ dia: d.data.slice(8, 10), saldo: d.saldo_do_dia }));

  return (
    <div className="card" style={{ height: 280 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={serie} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
          <CartesianGrid stroke="var(--rule-soft)" vertical={false} />
          <XAxis dataKey="dia" stroke="var(--ink-45)" fontSize={11} tickLine={false} axisLine={{ stroke: "var(--rule)" }} />
          <YAxis stroke="var(--ink-45)" fontSize={11} tickLine={false} axisLine={false} />
          <ReferenceLine y={0} stroke="var(--rule-hard)" />
          <Tooltip
            contentStyle={{ background: "var(--paper)", border: "1px solid var(--rule-hard)", fontFamily: "var(--mono)", fontSize: 12 }}
            formatter={(v) => [`${v.toFixed(2)}h`, "Saldo do dia"]}
            labelFormatter={(d) => `Dia ${d}`}
          />
          <Line type="monotone" dataKey="saldo" stroke="var(--signal)" strokeWidth={1.5} dot={{ r: 2.5 }} isAnimationActive />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function dispararDownload(blob, nomeDoArquivo) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = nomeDoArquivo;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
