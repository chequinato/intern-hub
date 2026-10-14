// Graficos reaproveitados entre o painel inicial e o relatorio (recharts).
// As cores vem das variaveis do tema, entao funcionam no claro e no escuro.

import {
  Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { CalendarRange, TrendingUp } from "lucide-react";
import { DicaGrafico } from "./DicaGrafico";
import { Vazio } from "./Ui";
import { diaDaSemana, formatarDataCurta, formatarHoras, formatarSaldo, horasEMinutos, MESES_CURTOS } from "../utils/formato";

// Eixo vertical que sempre inclui o zero, arredondado em horas inteiras:
// barras de saldo negativo partem da linha do zero para baixo.
export const EIXO_COM_ZERO = [(min) => Math.min(0, Math.floor(min / 2) * 2), (max) => Math.max(0, Math.ceil(max / 2) * 2)];

export function GraficoTendencia({ tendencia }) {
  if (!tendencia.length) {
    return <Vazio icone={TrendingUp} titulo="Ainda sem dias completos">A tendência aparece quando o primeiro dia completo entrar no saldo.</Vazio>;
  }
  const dados = tendencia.map((m) => ({ ...m, rotulo: `${MESES_CURTOS[m.mes - 1]}/${String(m.ano).slice(2)}` }));
  return (
    <div style={{ height: 250 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={dados} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <CartesianGrid stroke="var(--borda)" vertical={false} />
          <XAxis dataKey="rotulo" tickLine={false} axisLine={false} tick={{ fill: "var(--texto-3)", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "var(--texto-3)", fontSize: 12 }} tickFormatter={(v) => `${v}h`} domain={EIXO_COM_ZERO} />
          <ReferenceLine y={0} stroke="var(--borda-forte)" />
          <Tooltip
            cursor={{ fill: "var(--superficie-3)" }}
            content={<DicaGrafico
              titulo={(p) => `${p.rotulo} · ${p.dias_completos} dias completos`}
              linhas={[
                { rotulo: "Horas no mês", valor: (p) => formatarHoras(p.horas_trabalhadas) },
                { rotulo: "Saldo do mês", valor: (p) => formatarSaldo(p.saldo_mes, 2) },
                { rotulo: "Acumulado", valor: (p) => formatarSaldo(p.saldo_acumulado, 2) },
              ]}
            />}
          />
          <Bar dataKey="saldo_mes" radius={[5, 5, 5, 5]} maxBarSize={34} animationDuration={900}>
            {dados.map((m) => <Cell key={m.rotulo} fill={m.saldo_mes >= 0 ? "var(--marca-400)" : "var(--alerta)"} fillOpacity={0.75} />)}
          </Bar>
          <Line type="monotone" dataKey="saldo_acumulado" stroke="var(--marca-700)" strokeWidth={2.5}
            dot={{ r: 4, fill: "var(--superficie)", strokeWidth: 2 }} activeDot={{ r: 6 }} animationDuration={1200} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function GraficoUltimosDias({ dias, meta, limite }) {
  if (!dias.length) {
    return <Vazio icone={CalendarRange} titulo="Nenhum ponto ainda">Bata o primeiro ponto para ver seus dias aqui.</Vazio>;
  }
  const dados = dias.map((d) => ({ ...d, rotulo: formatarDataCurta(d.data), semana: diaDaSemana(d.data) }));
  const cor = (d) => (!d.completo ? "var(--borda-forte)" : d.horas_trabalhadas > limite ? "var(--atencao-forte)" : "var(--marca-500)");
  return (
    <div style={{ height: 250 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={dados} margin={{ top: 8, right: 4, bottom: 0, left: -22 }}>
          <CartesianGrid stroke="var(--borda)" vertical={false} />
          <XAxis dataKey="rotulo" tickLine={false} axisLine={false} tick={{ fill: "var(--texto-3)", fontSize: 11 }} interval="preserveStartEnd" minTickGap={6} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "var(--texto-3)", fontSize: 12 }} domain={[0, (max) => Math.max(8, Math.ceil(max))]} />
          <ReferenceLine y={meta} stroke="var(--marca-700)" strokeDasharray="4 4" />
          <Tooltip
            cursor={{ fill: "var(--superficie-3)" }}
            content={<DicaGrafico
              titulo={(p) => `${p.semana}, ${p.rotulo}`}
              linhas={[
                { rotulo: "Trabalhado", valor: (p) => horasEMinutos(p.horas_trabalhadas) },
                { rotulo: "Situação", valor: (p) => (!p.completo ? "Incompleto" : p.horas_trabalhadas > limite ? "Acima do limite" : "Completo") },
              ]}
            />}
          />
          <Bar dataKey="horas_trabalhadas" radius={[5, 5, 0, 0]} maxBarSize={26} animationDuration={800}>
            {dados.map((d) => <Cell key={d.data} fill={cor(d)} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="legenda-grafico">
        <span><i style={{ background: "var(--marca-500)" }} />Completo</span>
        <span><i style={{ background: "var(--atencao-forte)" }} />Acima de {formatarHoras(limite, 0)}</span>
        <span><i style={{ background: "var(--borda-forte)" }} />Incompleto</span>
        <span><i className="tracejado" />Meta</span>
      </div>
    </div>
  );
}
