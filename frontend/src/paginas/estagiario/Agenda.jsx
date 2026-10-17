import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { CalendarDays, CalendarPlus, CircleAlert, Download, ExternalLink, GraduationCap, LoaderCircle, MapPin, Trash2 } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { Esqueleto, Vazio } from "../../components/Ui";
import {
  diaDaSemana, formatarData, formatarHoras, hojeIso, hora, linkGoogleAgenda, MESES, NOMES_TIPO_COMPROMISSO, paraData,
} from "../../utils/formato";

// Agenda do estagiario (Entrega 3). Alem de organizar o dia, ela muda a
// conta: num dia com PROVA a meta cai pela metade - Lei 11.788/2008, art. 10,
// paragrafo 2o (a carga horaria do estagio e reduzida pelo menos a metade
// nos periodos de avaliacao). A regra mora na API (servicos/agenda.py).
//
// Para o Google Agenda: cada compromisso tem o link "Google Agenda", que
// abre o evento ja preenchido, e o botao "Baixar .ics" exporta todos de uma
// vez (Google, Outlook e o calendario do celular importam esse arquivo).
export function Agenda() {
  const { estagiario, estagiarioId, recarregar } = useOutletContext();
  const notificar = useNotificar();
  const hoje = hojeIso();
  const agenda = useApiState(() => api.get(`/agenda/${estagiarioId}`), [estagiarioId]);
  const [removendo, setRemovendo] = useState(null);

  const itens = agenda.dados || [];
  const proximos = itens.filter((c) => c.data >= hoje);
  const passados = itens.filter((c) => c.data < hoje).reverse().slice(0, 8);
  const provas = proximos.filter((c) => c.tipo === "prova");
  const meta = estagiario.configuracao?.meta_horas_diaria ?? 6;

  async function remover(c) {
    setRemovendo(c.id);
    try {
      await api.delete(`/agenda/${c.id}`);
      agenda.setDados((lista) => lista.filter((x) => x.id !== c.id));
      notificar.info("Compromisso removido", c.titulo);
      recarregar();
    } catch (e) {
      notificar.erro("Não foi possível remover", e.message);
    } finally {
      setRemovendo(null);
    }
  }

  async function baixarIcs() {
    try {
      const arquivo = await api.baixarArquivo(`/agenda/${estagiarioId}/ics`);
      const url = URL.createObjectURL(arquivo);
      const link = document.createElement("a");
      link.href = url;
      link.download = "agenda-internhub.ics";
      link.click();
      URL.revokeObjectURL(url);
      notificar.sucesso("Agenda exportada", "Abra o arquivo ou importe no Google Agenda (Configurações › Importar).");
    } catch (e) {
      notificar.erro("Não foi possível exportar", e.message);
    }
  }

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Agenda e provas</h1>
          <p>Aulas, reuniões e provas no mesmo lugar do ponto. Em dia de prova, a sua meta cai pela metade.</p>
        </div>
        <div className="acoes">
          <button type="button" className="botao" onClick={baixarIcs} disabled={proximos.length === 0}>
            <Download />Baixar .ics
          </button>
        </div>
      </div>

      <div className="grade grade-principal">
        <section className="cartao entra" style={{ "--i": 1 }}>
          <div className="cartao-cabeca">
            <h2>Próximos compromissos</h2>
            <span className="sub">{proximos.length} na agenda</span>
          </div>
          {agenda.carregando && !agenda.dados ? (
            <div className="cartao-corpo pilha">{[0, 1, 2].map((n) => <Esqueleto key={n} altura={58} />)}</div>
          ) : proximos.length === 0 ? (
            <Vazio icone={CalendarDays} titulo="Agenda vazia">Cadastre suas provas: nesses dias a meta do estágio cai pela metade.</Vazio>
          ) : (
            <ListaAgenda itens={proximos} hoje={hoje} aoRemover={remover} removendo={removendo} />
          )}
          {passados.length > 0 && (
            <div className="cartao-corpo" style={{ paddingTop: 0 }}>
              <div className="divisor" style={{ margin: "6px 0 10px" }}>Já passaram</div>
              <ListaAgenda itens={passados} hoje={hoje} aoRemover={remover} removendo={removendo} passados />
            </div>
          )}
        </section>

        <div className="pilha">
          <NovoCompromisso aoCriar={(c) => { agenda.setDados((l) => [...(l || []), c].sort((a, b) => (a.data + (a.inicio || "")).localeCompare(b.data + (b.inicio || "")))); recarregar(); }} />

          <section className="cartao regra-prova entra" style={{ "--i": 3 }}>
            <div className="regra-prova-numero">
              <span>meta em dia de prova</span>
              <b className="numero">{formatarHoras(meta / 2)}</b>
              <small>em vez de {formatarHoras(meta)}</small>
            </div>
            <p>
              <GraduationCap size={15} /> Lei 11.788/2008, art. 10, § 2º: nos períodos de avaliação, a carga horária do estágio
              cai pelo menos à metade. O saldo, o relatório e o limite legal do dia já usam essa conta.
            </p>
            {provas.length > 0 && (
              <div className="regra-prova-lista">
                {provas.slice(0, 3).map((p) => (
                  <span key={p.id}><b className="mono">{formatarData(p.data).slice(0, 5)}</b> {p.titulo}</span>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </>
  );
}

function ListaAgenda({ itens, hoje, aoRemover, removendo, passados = false }) {
  return (
    <ul className="lista-agenda">
      {itens.map((c, i) => {
        const d = paraData(c.data);
        const ehHoje = c.data === hoje;
        return (
          <li key={c.id} className={`agenda-item agenda-item--${c.tipo}${passados ? " agenda-item--passado" : ""}`} style={{ "--i": i }}>
            <div className={`data-bloco${passados ? " data-bloco--apagado" : ""}`}>
              <span>{ehHoje ? "hoje" : MESES[d.getMonth()].slice(0, 3)}</span>
              <b>{d.getDate()}</b>
            </div>
            <div className="agenda-corpo">
              <div className="agenda-topo">
                <span className={`agenda-tipo agenda-tipo--${c.tipo}`}>{NOMES_TIPO_COMPROMISSO[c.tipo]}</span>
                <span className="mono texto-3">{c.inicio ? `${hora(c.inicio)}${c.fim ? `–${hora(c.fim)}` : ""}` : "dia inteiro"}</span>
                <span className="texto-3">{diaDaSemana(c.data, false)}</span>
              </div>
              <b>{c.titulo}</b>
              {(c.local || c.observacao) && (
                <span className="agenda-detalhe">
                  {c.local && <><MapPin size={12} />{c.local}</>}
                  {c.local && c.observacao && " · "}
                  {c.observacao}
                </span>
              )}
            </div>
            {!passados && (
              <a className="botao botao--pequeno" href={linkGoogleAgenda(c)} target="_blank" rel="noreferrer" title="Abrir no Google Agenda">
                <ExternalLink />Google Agenda
              </a>
            )}
            <button type="button" className="botao botao--fantasma botao--icone" onClick={() => aoRemover(c)} disabled={removendo === c.id}
              aria-label={`Remover ${c.titulo}`} title="Remover">
              {removendo === c.id ? <LoaderCircle className="girando" /> : <Trash2 />}
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function NovoCompromisso({ aoCriar }) {
  const notificar = useNotificar();
  const vazio = { titulo: "", tipo: "prova", data: hojeIso(), inicio: "", fim: "", local: "" };
  const [form, setForm] = useState(vazio);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);
  const mudar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const criado = await api.post("/agenda", {
        titulo: form.titulo.trim(),
        tipo: form.tipo,
        data: form.data,
        inicio: form.inicio || null,
        fim: form.fim || null,
        local: form.local.trim() || null,
      });
      notificar.sucesso(
        form.tipo === "prova" ? "Prova cadastrada" : "Compromisso cadastrado",
        form.tipo === "prova" ? `A meta de ${formatarData(form.data)} caiu pela metade.` : criado.titulo
      );
      setForm({ ...vazio, tipo: form.tipo });
      aoCriar(criado);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao entra" style={{ "--i": 2 }} onSubmit={enviar}>
      <div className="cartao-cabeca"><h2>Novo compromisso</h2></div>
      <div className="cartao-corpo pilha" style={{ gap: 14 }}>
        <div className="segmentado segmentado--bloco segmentado--quebra">
          {Object.entries(NOMES_TIPO_COMPROMISSO).map(([valor, nome]) => (
            <button key={valor} type="button" className={form.tipo === valor ? "ativo" : ""} onClick={() => setForm((f) => ({ ...f, tipo: valor }))}>{nome}</button>
          ))}
        </div>
        <div className="campo">
          <label htmlFor="ag-titulo">Título</label>
          <input id="ag-titulo" value={form.titulo} onChange={mudar("titulo")} minLength={2} maxLength={120}
            placeholder={form.tipo === "prova" ? "Prova de Banco de Dados" : "Reunião de acompanhamento"} required />
        </div>
        <div className="grade-campos">
          <div className="campo">
            <label htmlFor="ag-data">Data</label>
            <input id="ag-data" type="date" value={form.data} onChange={mudar("data")} required />
          </div>
          <div className="campo">
            <label htmlFor="ag-inicio">Início</label>
            <input id="ag-inicio" type="time" value={form.inicio} onChange={mudar("inicio")} />
          </div>
          <div className="campo">
            <label htmlFor="ag-fim">Fim</label>
            <input id="ag-fim" type="time" value={form.fim} onChange={mudar("fim")} disabled={!form.inicio} />
          </div>
        </div>
        <div className="campo">
          <label htmlFor="ag-local">Local (opcional)</label>
          <input id="ag-local" value={form.local} onChange={mudar("local")} maxLength={120} placeholder="UniAnchieta, bloco B" />
        </div>
        {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
        <button type="submit" className="botao botao--primario" disabled={enviando}>
          {enviando ? <LoaderCircle className="girando" /> : <CalendarPlus />}Adicionar à agenda
        </button>
      </div>
    </form>
  );
}
