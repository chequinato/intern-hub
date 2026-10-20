import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { ChevronLeft, ChevronRight, CircleAlert, LoaderCircle, NotebookPen, Plus, ShieldCheck, Trash2 } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { CarregandoPagina, ErroCarregar, Vazio } from "../../components/Ui";
import {
  BotaoPdfSemestre, EtapasDoSemestre, mudarSemestre, NumerosDoSemestre, semestreAtual,
} from "../../components/RelatorioSemestral";
import { diaDaSemana, formatarData, formatarDataCurta, formatarDataHora, hojeIso } from "../../utils/formato";

// Diario de atividades e relatorio semestral (Entrega 3). A Lei 11.788/2008,
// art. 9o, VII manda a empresa enviar a faculdade, a cada 6 meses no minimo,
// um relatorio de atividades com vista obrigatoria ao estagiario. Aqui o
// estagiario registra o que fez; o gestor avalia e valida; o estagiario da
// ciencia; o PDF sai pronto para entregar.
export function Atividades() {
  const { estagiarioId } = useOutletContext();
  const notificar = useNotificar();
  const [periodo, setPeriodo] = useState(semestreAtual);
  const semestre = useApiState(
    () => api.get(`/estagio/${estagiarioId}/semestre/${periodo.ano}/${periodo.semestre}`),
    [estagiarioId, periodo.ano, periodo.semestre]
  );
  const [removendo, setRemovendo] = useState(null);
  const [ciente, setCiente] = useState(false);

  async function remover(atividade) {
    setRemovendo(atividade.id);
    try {
      await api.delete(`/estagio/atividades/${atividade.id}`);
      semestre.recarregar();
    } catch (e) {
      notificar.erro("Não foi possível remover", e.message);
    } finally {
      setRemovendo(null);
    }
  }

  async function darCiencia() {
    setCiente(true);
    try {
      semestre.setDados(await api.post(`/estagio/${estagiarioId}/semestre/${periodo.ano}/${periodo.semestre}/ciencia`));
      notificar.sucesso("Ciência registrada", "O relatório está pronto para ir para a faculdade.");
    } catch (e) {
      notificar.erro("Não foi possível registrar", e.message);
    } finally {
      setCiente(false);
    }
  }

  if (semestre.erro) return <ErroCarregar mensagem={semestre.erro} aoTentar={semestre.recarregar} />;
  if (!semestre.dados) return <CarregandoPagina />;
  const s = semestre.dados;
  const fechado = s.status === "validado";
  const ehAtual = periodo.ano === semestreAtual().ano && periodo.semestre === semestreAtual().semestre;

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Atividades do estágio</h1>
          <p>O que você fez, semana a semana. No fim do semestre vira o relatório que a empresa manda para a faculdade.</p>
        </div>
        <div className="navegador-mes navegador-mes--destaque">
          <button type="button" className="botao botao--fantasma botao--icone" onClick={() => setPeriodo((p) => mudarSemestre(p, -1))} aria-label="Semestre anterior"><ChevronLeft /></button>
          <span>{s.semestre}º semestre de {s.ano}</span>
          <button type="button" className="botao botao--fantasma botao--icone" onClick={() => setPeriodo((p) => mudarSemestre(p, 1))} disabled={ehAtual} aria-label="Próximo semestre"><ChevronRight /></button>
        </div>
      </div>

      {fechado && !s.ciente_em && (
        <div className="aviso aviso--credito entra" style={{ marginBottom: 16 }}>
          <ShieldCheck />
          <div><strong>O gestor validou este semestre.</strong> Leia a avaliação e confirme que está ciente (a lei exige a sua vista).</div>
          <div className="acoes">
            <button type="button" className="botao botao--pequeno botao--sucesso" onClick={darCiencia} disabled={ciente}>
              {ciente ? <LoaderCircle className="girando" /> : <ShieldCheck />}Estou ciente
            </button>
          </div>
        </div>
      )}

      <div className="grade grade-principal">
        <section className="cartao entra" style={{ "--i": 1 }}>
          <div className="cartao-cabeca"><h2><NotebookPen />Diário</h2><span className="sub">{s.atividades.length} registro(s)</span></div>
          {!fechado && <NovaAtividade key={`${s.ano}-${s.semestre}`} periodo={s} aoCriar={semestre.recarregar} />}
          {s.atividades.length === 0 ? (
            <Vazio icone={NotebookPen} titulo="Nada registrado neste semestre">Uma linha por semana já basta: o que você fez e o que aprendeu.</Vazio>
          ) : (
            <ol className="diario">
              {[...s.atividades].reverse().map((a, i) => (
                <li key={a.id} style={{ "--i": i }}>
                  <div className="data-bloco"><span>{diaDaSemana(a.data)}</span><b>{formatarDataCurta(a.data)}</b></div>
                  <p>{a.descricao}</p>
                  {!fechado && (
                    <button type="button" className="botao botao--fantasma botao--icone" onClick={() => remover(a)} disabled={removendo === a.id}
                      aria-label="Remover atividade" title="Remover">
                      {removendo === a.id ? <LoaderCircle className="girando" /> : <Trash2 />}
                    </button>
                  )}
                </li>
              ))}
            </ol>
          )}
        </section>

        <section className="cartao entra" style={{ "--i": 2 }}>
          <div className="cartao-cabeca"><h2>Relatório do semestre</h2><span className="sub">Lei 11.788/2008, art. 9º, VII</span></div>
          <div className="cartao-corpo pilha" style={{ gap: 18 }}>
            <EtapasDoSemestre semestre={s} />
            <NumerosDoSemestre semestre={s} />
            {s.avaliacao_gestor && fechado && (
              <div className="pilha" style={{ gap: 8 }}>
                <div className="divisor">Avaliação do supervisor</div>
                <blockquote className="citacao"><ShieldCheck size={14} />{s.avaliacao_gestor}</blockquote>
                <span className="texto-3" style={{ fontSize: 12.5 }}>{s.gestor_nome} · {formatarDataHora(s.validado_em)}</span>
              </div>
            )}
            <div style={{ marginTop: "auto" }}><BotaoPdfSemestre semestre={s} /></div>
          </div>
        </section>
      </div>
    </>
  );
}

function NovaAtividade({ periodo, aoCriar }) {
  const notificar = useNotificar();
  const hoje = hojeIso();
  const fimPermitido = periodo.fim < hoje ? periodo.fim : hoje;
  const [data, setData] = useState(fimPermitido);
  const [descricao, setDescricao] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await api.post("/estagio/atividades", { data, descricao: descricao.trim() });
      notificar.sucesso("Atividade registrada", formatarData(data));
      setDescricao("");
      aoCriar();
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="nova-atividade" onSubmit={enviar}>
      <input type="date" value={data} min={periodo.inicio} max={fimPermitido} onChange={(e) => setData(e.target.value)} aria-label="Data" required />
      <textarea value={descricao} onChange={(e) => setDescricao(e.target.value)} minLength={5} maxLength={1000} rows={2}
        placeholder="O que você fez: tarefa, ferramenta, o que aprendeu." aria-label="Descrição" required />
      {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
      <button type="submit" className="botao botao--primario botao--pequeno" disabled={enviando}>
        {enviando ? <LoaderCircle className="girando" /> : <Plus />}Registrar
      </button>
    </form>
  );
}
