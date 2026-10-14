import { useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { ArrowRight, CalendarPlus, ChevronLeft, ChevronRight, CircleCheck, History, LoaderCircle, TriangleAlert } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { CartaoPonto } from "../../components/CartaoPonto";
import { useNotificar } from "../../components/Notificacoes";
import { Esqueleto, Vazio } from "../../components/Ui";
import {
  diaDaSemana, formatarDataCurta, formatarHoras, hojeIso, hora, horasEMinutos, nomeDoMes, paraData,
} from "../../utils/formato";

const VAZIO = { data: hojeIso(), entrada: "", saida_almoco: "", retorno_almoco: "", saida: "" };

function primeiroEUltimoDia(ano, mes) {
  const fim = new Date(ano, mes, 0).getDate();
  const doisDigitos = (n) => String(n).padStart(2, "0");
  return { inicio: `${ano}-${doisDigitos(mes)}-01`, fim: `${ano}-${doisDigitos(mes)}-${doisDigitos(fim)}` };
}

function minutos(texto) {
  const [h, m] = texto.split(":").map(Number);
  return h * 60 + m;
}

// Quanto de almoco foi descontado no dia - a regra do minimo de 1h fica
// visivel na tela ("1h de almoço descontada"), em vez de escondida no calculo.
function almocoDescontado(r) {
  if (!r.saida) return null;
  if (r.saida_almoco && r.retorno_almoco) {
    const real = (minutos(r.retorno_almoco) - minutos(r.saida_almoco)) / 60;
    return real < 1 ? "mínimo de 1h de almoço aplicado" : `${horasEMinutos(real)} de almoço descontada`;
  }
  return "1h de almoço descontada";
}

// Segunda-feira da semana de uma data, como texto "aaaa-mm-dd".
function segundaDaSemana(iso) {
  const d = paraData(iso);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function Ponto() {
  const { estagiarioId, estagiario, painel, recarregar } = useOutletContext();
  const hoje = new Date();
  const [periodo, setPeriodo] = useState({ ano: hoje.getFullYear(), mes: hoje.getMonth() + 1 });
  const { inicio, fim } = primeiroEUltimoDia(periodo.ano, periodo.mes);

  // Comeca na segunda-feira da semana do dia 1: uma semana que cruza a
  // virada do mes aparece inteira, e o total bate com a regra da API.
  const inicioDaSemana = segundaDaSemana(inicio);
  const registros = useApiState(
    () => api.get(`/registros/${estagiarioId}`, { inicio: inicioDaSemana, fim }),
    [estagiarioId, inicioDaSemana, fim]
  );

  function mudarMes(delta) {
    setPeriodo(({ ano, mes }) => {
      const d = new Date(ano, mes - 1 + delta, 1);
      return { ano: d.getFullYear(), mes: d.getMonth() + 1 };
    });
  }

  function aposMudanca() {
    registros.recarregar();
    recarregar();
  }

  const limiteSemanal = estagiario.configuracao?.limite_maximo_semanal ?? 30;
  const limiteDiario = estagiario.configuracao?.limite_maximo_diario ?? 6;
  const semanas = agruparPorSemana(registros.dados || []);

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Registro de ponto</h1>
          <p>Bata o ponto ao longo do dia ou lance um dia inteiro que ficou para trás.</p>
        </div>
      </div>

      <div className="grade grade-principal">
        {painel ? (
          <CartaoPonto
            i={1}
            estagiarioId={estagiarioId}
            registroHoje={painel.registro_hoje}
            proxima={painel.proxima_marcacao}
            horasDoDia={painel.horas_hoje}
            aoMarcar={aposMudanca}
          />
        ) : <Esqueleto altura={260} style={{ borderRadius: 14 }} />}
        <FormularioDia estagiarioId={estagiarioId} aoSalvar={aposMudanca} />
      </div>

      <div className="espaco" />

      <section className="cartao entra" style={{ "--i": 3 }}>
        <div className="cartao-cabeca">
          <h2>Histórico</h2>
          <div className="navegador-mes">
            <button type="button" className="botao botao--fantasma botao--icone" onClick={() => mudarMes(-1)} aria-label="Mês anterior"><ChevronLeft /></button>
            <span>{nomeDoMes(periodo.mes)} de {periodo.ano}</span>
            <button type="button" className="botao botao--fantasma botao--icone" onClick={() => mudarMes(1)} aria-label="Próximo mês"><ChevronRight /></button>
          </div>
        </div>

        {registros.carregando && !registros.dados ? (
          <div className="cartao-corpo pilha">{[0, 1, 2, 3].map((n) => <Esqueleto key={n} altura={36} />)}</div>
        ) : registros.erro ? (
          <div className="cartao-corpo"><div className="aviso aviso--alerta"><TriangleAlert />{registros.erro}</div></div>
        ) : semanas.length === 0 ? (
          <Vazio icone={History} titulo="Nenhum ponto neste mês">Use o botão de bater ponto ou lance um dia inteiro no formulário acima.</Vazio>
        ) : (
          <div className="tabela-moldura">
            <table className="tabela">
              <thead>
                <tr>
                  <th>Dia</th>
                  <th>Entrada</th>
                  <th>Almoço</th>
                  <th>Saída</th>
                  <th>Trabalhado</th>
                  <th className="direita">Situação</th>
                </tr>
              </thead>
              <tbody>
                {semanas.map((semana) => {
                  const acima = semana.total > limiteSemanal;
                  return [
                    <tr key={semana.segunda} className="linha-semana">
                      <td colSpan={6}>
                        <span style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                          <b style={{ color: "var(--texto)" }}>Semana de {formatarDataCurta(semana.segunda)}</b>
                          <span className="mono">{formatarHoras(semana.total)} de {formatarHoras(limiteSemanal, 0)}</span>
                          <span style={{ width: 120 }}><BarraSemana fracao={semana.total / limiteSemanal} /></span>
                          {acima && <span className="selo selo--alerta">Acima do limite legal</span>}
                        </span>
                      </td>
                    </tr>,
                    ...semana.dias.map((r, i) => (
                      <tr key={r.id} style={{ "--i": i }}>
                        <td>
                          <span className="dia-tabela"><span>{diaDaSemana(r.data)}</span>{formatarDataCurta(r.data)}</span>
                        </td>
                        <td className="mono">{hora(r.entrada)}</td>
                        <td className="mono">
                          {r.saida_almoco || r.retorno_almoco
                            ? <>{hora(r.saida_almoco)} – {r.retorno_almoco ? hora(r.retorno_almoco) : <span className="atencao">?</span>}</>
                            : <span className="texto-3">—</span>}
                        </td>
                        <td className="mono">{r.saida ? hora(r.saida) : <span className="texto-3">—</span>}</td>
                        <td>
                          <div style={{ fontWeight: 620 }} className="numero">{r.saida ? horasEMinutos(r.horas_trabalhadas) : "em andamento"}</div>
                          {almocoDescontado(r) && <div className="texto-3" style={{ fontSize: 12 }}>{almocoDescontado(r)}</div>}
                        </td>
                        <td className="direita">
                          <SituacaoDia registro={r} limiteDiario={limiteDiario} />
                        </td>
                      </tr>
                    )),
                  ];
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

function BarraSemana({ fracao }) {
  const tom = fracao > 1 ? "alerta" : fracao >= 0.85 ? "atencao" : "";
  return (
    <div className={`barra barra--fina${tom ? ` barra--${tom}` : ""}`}>
      <span style={{ width: `${Math.min(1, fracao) * 100}%` }} />
    </div>
  );
}

function SituacaoDia({ registro: r, limiteDiario }) {
  if (r.pendencia) {
    const campo = r.retorno_almoco ? "saida_almoco" : "retorno_almoco";
    return (
      <span style={{ display: "inline-flex", gap: 8, alignItems: "center", flexWrap: "wrap", justifyContent: "flex-end" }}>
        <span className="selo selo--atencao">Pendência de almoço</span>
        <Link className="botao botao--pequeno" to={`../solicitacoes?registro=${r.id}&campo=${campo}`} relative="path">
          Pedir ajuste <ArrowRight />
        </Link>
      </span>
    );
  }
  if (!r.saida) return <span className="selo selo--marca"><span className="ponto ponto--vivo" />Em andamento</span>;
  if (r.horas_trabalhadas > limiteDiario) return <span className="selo selo--atencao">Acima de {formatarHoras(limiteDiario, 0)}</span>;
  if (r.aviso_limite_legal) return <span className="selo selo--atencao">Semana acima do limite</span>;
  return <span className="selo selo--credito"><CircleCheck />Completo</span>;
}

function agruparPorSemana(registros) {
  const grupos = new Map();
  [...registros].reverse().forEach((r) => {
    const chave = segundaDaSemana(r.data);
    if (!grupos.has(chave)) grupos.set(chave, { segunda: chave, dias: [], total: 0 });
    const grupo = grupos.get(chave);
    grupo.dias.push(r);
    grupo.total += r.horas_trabalhadas;
  });
  return [...grupos.values()];
}

function FormularioDia({ estagiarioId, aoSalvar }) {
  const notificar = useNotificar();
  const [form, setForm] = useState(VAZIO);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  const mudar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const criado = await api.post("/registros", {
        estagiario_id: estagiarioId,
        data: form.data,
        entrada: form.entrada,
        saida: form.saida || null,
        saida_almoco: form.saida_almoco || null,
        retorno_almoco: form.retorno_almoco || null,
      });
      notificar.sucesso(
        "Dia registrado",
        criado.saida ? `${horasEMinutos(criado.horas_trabalhadas)} trabalhadas em ${formatarDataCurta(criado.data)}.` : `Entrada de ${formatarDataCurta(criado.data)} salva.`
      );
      if (criado.pendencia) notificar.info("Dia com pendência", "O almoço ficou incompleto. Peça o ajuste para o dia entrar no saldo.");
      if (criado.aviso_limite_legal) notificar.info("Limite legal", criado.aviso_limite_legal);
      setForm({ ...VAZIO, data: form.data });
      aoSalvar();
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao entra" style={{ "--i": 2 }} onSubmit={enviar}>
      <div className="cartao-cabeca">
        <h2>Lançar um dia inteiro</h2>
        <span className="sub">para dias que ficaram para trás</span>
      </div>
      <div className="cartao-corpo pilha" style={{ gap: 14 }}>
        <div className="campo">
          <label htmlFor="dia-data">Data</label>
          <input id="dia-data" type="date" value={form.data} max={hojeIso()} onChange={mudar("data")} required />
        </div>
        <div className="grade-campos" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <div className="campo"><label htmlFor="dia-entrada">Entrada</label><input id="dia-entrada" type="time" value={form.entrada} onChange={mudar("entrada")} required /></div>
          <div className="campo"><label htmlFor="dia-saida">Saída</label><input id="dia-saida" type="time" value={form.saida} onChange={mudar("saida")} /></div>
          <div className="campo"><label htmlFor="dia-sa">Saída para o almoço</label><input id="dia-sa" type="time" value={form.saida_almoco} onChange={mudar("saida_almoco")} /></div>
          <div className="campo"><label htmlFor="dia-ra">Retorno do almoço</label><input id="dia-ra" type="time" value={form.retorno_almoco} onChange={mudar("retorno_almoco")} /></div>
        </div>
        {erro && <div className="aviso aviso--alerta"><TriangleAlert />{erro}</div>}
        <button type="submit" className="botao botao--primario" disabled={enviando}>
          {enviando ? <LoaderCircle className="girando" /> : <CalendarPlus />}
          {enviando ? "Salvando…" : "Salvar dia"}
        </button>
      </div>
    </form>
  );
}
