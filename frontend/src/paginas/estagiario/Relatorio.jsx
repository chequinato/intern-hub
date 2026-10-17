import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  Bar, CartesianGrid, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  ChevronLeft, ChevronRight, FileSpreadsheet, FileText, Info, LoaderCircle, TrendingUp,
} from "lucide-react";
import { acentuar, api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { DicaGrafico } from "../../components/DicaGrafico";
import { EIXO_COM_ZERO, GraficoTendencia } from "../../components/Graficos";
import { useNotificar } from "../../components/Notificacoes";
import { CarregandoPagina, ErroCarregar, Indicador, Numero, Vazio } from "../../components/Ui";
import { formatarHoras, formatarSaldo, hojeIso, horasEMinutos, MESES, nomeDoMes } from "../../utils/formato";

const DIAS_CABECALHO = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"];

// Relatorio mensal (funcionalidade 9) com o que a Entrega 3 acrescentou:
// calendario do mes, saldo dia a dia, tendencia do semestre (funcionalidade
// 19) e exportacao em PDF/Excel.
export function Relatorio() {
  const { estagiarioId } = useOutletContext();
  const notificar = useNotificar();
  const hoje = new Date();
  const [periodo, setPeriodo] = useState({ ano: hoje.getFullYear(), mes: hoje.getMonth() + 1 });
  const [baixando, setBaixando] = useState(null);

  const relatorio = useApiState(
    () => api.get(`/relatorio/${estagiarioId}`, { mes: periodo.mes, ano: periodo.ano }),
    [estagiarioId, periodo.mes, periodo.ano]
  );
  const tendencia = useApiState(() => api.get(`/relatorio/${estagiarioId}/tendencia`), [estagiarioId]);
  const feriados = useApiState(() => api.get("/feriados"), []);

  function mudarMes(delta) {
    setPeriodo(({ ano, mes }) => {
      const d = new Date(ano, mes - 1 + delta, 1);
      return { ano: d.getFullYear(), mes: d.getMonth() + 1 };
    });
  }

  async function exportar(formato) {
    setBaixando(formato);
    try {
      const blob = await api.baixarArquivo(`/relatorio/${estagiarioId}/exportar`, { mes: periodo.mes, ano: periodo.ano, formato });
      const nome = `relatorio_${String(periodo.mes).padStart(2, "0")}_${periodo.ano}.${formato === "pdf" ? "pdf" : "xlsx"}`;
      dispararDownload(blob, nome);
      notificar.sucesso("Relatório exportado", nome);
    } catch (e) {
      notificar.erro("Não foi possível exportar", e.message);
    } finally {
      setBaixando(null);
    }
  }

  const ehMesAtual = periodo.ano === hoje.getFullYear() && periodo.mes === hoje.getMonth() + 1;
  const dados = relatorio.dados;

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Relatório mensal</h1>
          <p>Horas, faltas e saldo do mês, com exportação para PDF e Excel.</p>
        </div>
        <div className="acoes">
          <div className="navegador-mes navegador-mes--destaque">
            <button type="button" className="botao botao--fantasma botao--icone" onClick={() => mudarMes(-1)} aria-label="Mês anterior"><ChevronLeft /></button>
            <span>{nomeDoMes(periodo.mes)} de {periodo.ano}</span>
            <button type="button" className="botao botao--fantasma botao--icone" onClick={() => mudarMes(1)} disabled={ehMesAtual} aria-label="Próximo mês"><ChevronRight /></button>
          </div>
          <button type="button" className="botao" onClick={() => exportar("pdf")} disabled={!!baixando}>
            {baixando === "pdf" ? <LoaderCircle className="girando" /> : <FileText />}PDF
          </button>
          <button type="button" className="botao" onClick={() => exportar("excel")} disabled={!!baixando}>
            {baixando === "excel" ? <LoaderCircle className="girando" /> : <FileSpreadsheet />}Excel
          </button>
        </div>
      </div>

      {relatorio.erro ? (
        <ErroCarregar mensagem={relatorio.erro} aoTentar={relatorio.recarregar} />
      ) : !dados ? (
        <CarregandoPagina />
      ) : (
        <>
          {dados.aviso_vencimento && (
            <div className="aviso entra" style={{ marginBottom: 16 }}><Info /><div>{acentuar(dados.aviso_vencimento)}</div></div>
          )}

          <div className="cartao faixa entra">
            <Indicador rotulo="Horas trabalhadas" rodape={`em ${dados.dias_uteis_trabalhados} dia(s) com ponto`}>
              <Numero valor={dados.total_horas_trabalhadas} formato="horas" />
            </Indicador>
            <Indicador rotulo="Média por dia" rodape="horas por dia com ponto">
              <Numero valor={dados.dias_uteis_trabalhados ? dados.total_horas_trabalhadas / dados.dias_uteis_trabalhados : 0} formato="horas" />
            </Indicador>
            <Indicador rotulo="Faltas"
              rodape={dados.faltas ? "dias úteis sem ponto" : "nenhuma falta no mês"}>
              <Numero valor={dados.faltas} />
            </Indicador>
            <Indicador destaque rotulo="Saldo acumulado" rodape="banco de horas até hoje">
              <span className={dados.saldo_acumulado >= 0 ? "credito" : "alerta"}><Numero valor={dados.saldo_acumulado} formato="saldo" /></span>
            </Indicador>
          </div>

          <div className="espaco" />

          <div className="grade grade-principal">
            <section className="cartao entra" style={{ "--i": 5 }}>
              <div className="cartao-cabeca">
                <h2>Saldo dia a dia</h2>
                <span className="sub">barras: saldo do dia · linha: acumulado no mês</span>
              </div>
              <div className="cartao-corpo">
                <GraficoDoMes evolucao={dados.evolucao_diaria} />
              </div>
            </section>

            <section className="cartao entra" style={{ "--i": 6 }}>
              <div className="cartao-cabeca">
                <h2>Calendário</h2>
                <span className="sub">{MESES[periodo.mes - 1]}</span>
              </div>
              <div className="cartao-corpo">
                <Calendario
                  ano={periodo.ano}
                  mes={periodo.mes}
                  evolucao={dados.evolucao_diaria}
                  faltas={dados.datas_faltas || []}
                  provas={dados.datas_provas || []}
                  feriados={feriados.dados || []}
                />
              </div>
            </section>
          </div>

          <div className="espaco" />

          <section className="cartao entra" style={{ "--i": 7 }}>
            <div className="cartao-cabeca">
              <h2>Tendência do semestre</h2>
              <span className="sub">saldo de cada mês e o acumulado</span>
            </div>
            <div className="cartao-corpo">
              {tendencia.dados ? <GraficoTendencia tendencia={tendencia.dados} /> : <div className="esqueleto" style={{ height: 250 }} />}
            </div>
          </section>
        </>
      )}
    </>
  );
}

function GraficoDoMes({ evolucao }) {
  if (!evolucao.length) {
    return <Vazio icone={TrendingUp} titulo="Sem ponto neste mês">Escolha outro mês na seta acima.</Vazio>;
  }
  // Acumulado do mes: cada dia soma o saldo dele ao total dos anteriores.
  const dados = evolucao.reduce((lista, d) => {
    const anterior = lista.length ? lista[lista.length - 1].acumulado : 0;
    lista.push({ ...d, dia: d.data.slice(8, 10), acumulado: Number((anterior + d.saldo_do_dia).toFixed(2)) });
    return lista;
  }, []);
  return (
    <div style={{ height: 290 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={dados} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
          <CartesianGrid stroke="var(--borda)" vertical={false} />
          <XAxis dataKey="dia" tickLine={false} axisLine={false} tick={{ fill: "var(--texto-3)", fontSize: 11 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "var(--texto-3)", fontSize: 12 }} tickFormatter={(v) => `${v}h`} domain={EIXO_COM_ZERO} />
          <ReferenceLine y={0} stroke="var(--borda-forte)" />
          <Tooltip
            cursor={{ fill: "var(--superficie-3)" }}
            content={<DicaGrafico
              titulo={(p) => `Dia ${p.dia}`}
              linhas={[
                { rotulo: "Trabalhado", valor: (p) => horasEMinutos(p.horas_trabalhadas) },
                { rotulo: "Saldo do dia", valor: (p) => formatarSaldo(p.saldo_do_dia, 2) },
                { rotulo: "Acumulado no mês", valor: (p) => formatarSaldo(p.acumulado, 2) },
              ]}
            />}
          />
          <Bar dataKey="saldo_do_dia" radius={[4, 4, 4, 4]} maxBarSize={18} animationDuration={800}>
            {dados.map((d) => <Cell key={d.data} fill={d.saldo_do_dia >= 0 ? "var(--grafico-base)" : "var(--alerta)"} fillOpacity={0.85} />)}
          </Bar>
          <Line type="monotone" dataKey="acumulado" stroke="var(--marca-500)" strokeWidth={2.2} dot={false} animationDuration={1200} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function Calendario({ ano, mes, evolucao, faltas, feriados, provas = [] }) {
  const trabalhados = new Map(evolucao.map((d) => [d.data, d]));
  const listaFaltas = new Set(faltas);
  // Entrega 3: dia de prova (meta pela metade) ganha a marca "P" no canto.
  const diasDeProva = new Set(provas);
  const nomesFeriados = new Map(feriados.map((f) => [f.data, f.descricao]));
  const hojeTexto = hojeIso();
  const totalDias = new Date(ano, mes, 0).getDate();
  const deslocamento = (new Date(ano, mes - 1, 1).getDay() + 6) % 7;

  const celulas = [];
  for (let n = 0; n < deslocamento; n += 1) celulas.push(<div key={`v${n}`} />);
  for (let dia = 1; dia <= totalDias; dia += 1) {
    const iso = `${ano}-${String(mes).padStart(2, "0")}-${String(dia).padStart(2, "0")}`;
    const semana = (new Date(ano, mes - 1, dia).getDay() + 6) % 7;
    let tipo = "vazio";
    let dica = "";
    if (trabalhados.has(iso)) {
      const d = trabalhados.get(iso);
      tipo = d.saldo_do_dia >= 0 ? "trabalhado" : "curto";
      dica = `${horasEMinutos(d.horas_trabalhadas)} · saldo ${formatarSaldo(d.saldo_do_dia, 2)}`;
    } else if (nomesFeriados.has(iso)) {
      tipo = "feriado";
      dica = nomesFeriados.get(iso);
    } else if (listaFaltas.has(iso)) {
      tipo = "falta";
      dica = "Falta: dia útil sem ponto";
    } else if (semana >= 5) {
      tipo = "fds";
    } else if (iso > hojeTexto) {
      tipo = "futuro";
    }
    const prova = diasDeProva.has(iso);
    if (prova) dica = `Prova: meta pela metade${dica ? ` · ${dica}` : ""}`;
    celulas.push(
      <div key={iso} className={`cal-dia cal-dia--${tipo}${iso === hojeTexto ? " cal-dia--hoje" : ""}${prova ? " cal-dia--prova" : ""}`} title={dica} style={{ "--i": dia }}>
        <span>{dia}</span>
        {trabalhados.has(iso) && <small>{formatarHoras(trabalhados.get(iso).horas_trabalhadas)}</small>}
      </div>
    );
  }

  return (
    <>
      <div className="calendario">
        {DIAS_CABECALHO.map((d) => <div key={d} className="cal-cabeca">{d}</div>)}
        {celulas}
      </div>
      <div className="legenda-grafico" style={{ marginTop: 14 }}>
        <span><i className="cal-legenda cal-dia--trabalhado" />Meta cumprida</span>
        <span><i className="cal-legenda cal-dia--curto" />Abaixo da meta</span>
        <span><i className="cal-legenda cal-dia--falta" />Falta</span>
        <span><i className="cal-legenda cal-dia--feriado" />Feriado</span>
        <span><b className="cal-marca-prova">P</b>Dia de prova (meta pela metade)</span>
      </div>
    </>
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
