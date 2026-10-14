import { useMemo, useState } from "react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { ArrowRight, FileDown, FilePen, Inbox, LoaderCircle, Send, TriangleAlert } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { Esqueleto, SeloStatus, Vazio } from "../../components/Ui";
import {
  diaDaSemana, formatarData, formatarDataCurta, formatarDataHora, hora, NOMES_CAMPOS,
} from "../../utils/formato";

const FILTROS = [
  { valor: "todos", rotulo: "Todos" },
  { valor: "pendente", rotulo: "Pendentes" },
  { valor: "aprovado", rotulo: "Aprovados" },
  { valor: "rejeitado", rotulo: "Rejeitados" },
];

// Pedidos de ajuste do estagiario (funcionalidade 6 da Entrega 1): abrir um
// pedido sobre um dia ja registrado e acompanhar a resposta do gestor.
// Quando a tela abre por um atalho "Pedir ajuste" (painel ou historico), o
// dia e o campo chegam pela URL: ?registro=12&campo=retorno_almoco.
export function Solicitacoes() {
  const { estagiarioId, recarregar } = useOutletContext();
  const registros = useApiState(() => api.get(`/registros/${estagiarioId}`), [estagiarioId]);
  const pedidos = useApiState(() => api.get("/solicitacoes", { estagiario_id: estagiarioId }), [estagiarioId]);
  const [filtro, setFiltro] = useState("todos");

  const lista = (pedidos.dados || []).filter((p) => filtro === "todos" || p.status === filtro);

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Pedidos de ajuste</h1>
          <p>Esqueceu uma marcação ou bateu no horário errado? Peça a correção ao seu gestor.</p>
        </div>
      </div>

      <div className="grade grade-principal">
        <section className="cartao entra" style={{ "--i": 2 }}>
          <div className="cartao-cabeca">
            <h2>Meus pedidos</h2>
            <div className="segmentado">
              {FILTROS.map((f) => (
                <button key={f.valor} type="button" className={filtro === f.valor ? "ativo" : ""} onClick={() => setFiltro(f.valor)}>
                  {f.rotulo}
                </button>
              ))}
            </div>
          </div>
          {pedidos.carregando && !pedidos.dados ? (
            <div className="cartao-corpo pilha">{[0, 1, 2].map((n) => <Esqueleto key={n} altura={74} />)}</div>
          ) : lista.length === 0 ? (
            <Vazio icone={Inbox} titulo={filtro === "todos" ? "Nenhum pedido ainda" : "Nada por aqui"}>
              {filtro === "todos" ? "Quando você pedir um ajuste, ele aparece aqui com a resposta do gestor." : "Nenhum pedido com essa situação."}
            </Vazio>
          ) : (
            <ul className="lista-pedidos">
              {lista.map((p, i) => <ItemPedido key={p.id} pedido={p} i={i} />)}
            </ul>
          )}
        </section>

        <FormularioPedido
          registros={registros.dados || []}
          carregando={registros.carregando && !registros.dados}
          aoCriar={() => {
            pedidos.recarregar();
            recarregar();
          }}
        />
      </div>
    </>
  );
}

function ItemPedido({ pedido: p, i }) {
  const notificar = useNotificar();
  const [baixando, setBaixando] = useState(false);

  async function baixar() {
    setBaixando(true);
    try {
      const blob = await api.baixarArquivo(`/solicitacoes/${p.id}/pdf`);
      const url = URL.createObjectURL(blob);
      const link = Object.assign(document.createElement("a"), { href: url, download: `comprovante_pedido_${p.id}.pdf` });
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      notificar.erro("Não foi possível gerar o comprovante", e.message);
    } finally {
      setBaixando(false);
    }
  }

  return (
    <li className="pedido entra" style={{ "--i": i }}>
      <div className="data-bloco">
        <span>{diaDaSemana(p.data_registro)}</span>
        <b>{formatarDataCurta(p.data_registro)}</b>
      </div>
      <div className="pedido-corpo">
        <div className="pedido-topo">
          <b>{NOMES_CAMPOS[p.campo_alterado]}</b>
          <span className="pedido-mudanca mono">
            {p.status === "aprovado"
              ? <><span className="texto-3">aplicado</span> {hora(p.horario_sugerido)}</>
              : <>{hora(p.horario_atual)} <ArrowRight size={14} /> {hora(p.horario_sugerido)}</>}
          </span>
          <SeloStatus status={p.status} />
        </div>
        <p className="pedido-justificativa">“{p.justificativa}”</p>
        <div className="pedido-rodape">
          Pedido em {formatarDataHora(p.data_solicitacao)}
          {p.data_resposta && <> · respondido por {p.gestor_nome || "gestor"} em {formatarDataHora(p.data_resposta)}</>}
        </div>
      </div>
      <button type="button" className="botao botao--fantasma botao--pequeno" onClick={baixar} disabled={baixando} title="Baixar comprovante em PDF">
        {baixando ? <LoaderCircle className="girando" /> : <FileDown />}PDF
      </button>
    </li>
  );
}

function FormularioPedido({ registros, carregando, aoCriar }) {
  const notificar = useNotificar();
  const [busca] = useSearchParams();
  const [registroId, setRegistroId] = useState(busca.get("registro") || "");
  const [campo, setCampo] = useState(busca.get("campo") || "retorno_almoco");
  const [horario, setHorario] = useState("");
  const [justificativa, setJustificativa] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  // Dias com pendencia primeiro, depois os mais recentes.
  const opcoes = useMemo(() => {
    const recentes = [...registros].reverse().slice(0, 45);
    return [...recentes.filter((r) => r.pendencia), ...recentes.filter((r) => !r.pendencia)];
  }, [registros]);
  const escolhido = registros.find((r) => String(r.id) === String(registroId));

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await api.post("/solicitacoes", {
        registro_id: Number(registroId),
        campo_alterado: campo,
        horario_sugerido: horario,
        justificativa: justificativa.trim(),
      });
      notificar.sucesso("Pedido enviado ao gestor", `${NOMES_CAMPOS[campo]} de ${formatarData(escolhido?.data)} para ${horario}.`);
      setHorario("");
      setJustificativa("");
      aoCriar();
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao entra" style={{ "--i": 1 }} onSubmit={enviar}>
      <div className="cartao-cabeca">
        <h2>Novo pedido</h2>
      </div>
      <div className="cartao-corpo pilha" style={{ gap: 14 }}>
        {carregando ? <Esqueleto altura={200} /> : opcoes.length === 0 ? (
          <Vazio icone={FilePen} titulo="Nenhum dia registrado">Bata o ponto primeiro; depois dá para pedir ajuste de qualquer horário.</Vazio>
        ) : (
          <>
            <div className="campo">
              <label htmlFor="pedido-dia">Dia</label>
              <select id="pedido-dia" value={registroId} onChange={(e) => setRegistroId(e.target.value)} required>
                <option value="" disabled>Escolha o dia…</option>
                {opcoes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {diaDaSemana(r.data)}, {formatarData(r.data)}{r.pendencia ? " · pendência de almoço" : ""}
                  </option>
                ))}
              </select>
            </div>
            <div className="campo">
              <label htmlFor="pedido-campo">Horário a corrigir</label>
              <select id="pedido-campo" value={campo} onChange={(e) => setCampo(e.target.value)}>
                {Object.entries(NOMES_CAMPOS).map(([valor, rotulo]) => <option key={valor} value={valor}>{rotulo}</option>)}
              </select>
            </div>
            <div className="campo">
              <label htmlFor="pedido-horario">Horário correto</label>
              <input id="pedido-horario" type="time" value={horario} onChange={(e) => setHorario(e.target.value)} required />
            </div>
            {escolhido && (
              <div className="previa-mudanca">
                <span>Hoje está</span><b className="mono">{hora(escolhido[campo])}</b>
                <ArrowRight size={15} />
                <span>vai ficar</span><b className="mono credito">{horario || "—"}</b>
              </div>
            )}
            <div className="campo">
              <label htmlFor="pedido-just">Justificativa</label>
              <textarea id="pedido-just" rows={3} value={justificativa} onChange={(e) => setJustificativa(e.target.value)}
                minLength={5} maxLength={300} placeholder="Esqueci de bater o retorno do almoço." required />
              <span className="dica">{justificativa.length}/300 · o gestor vê esse texto ao decidir</span>
            </div>
            {erro && <div className="aviso aviso--alerta"><TriangleAlert />{erro}</div>}
            <button type="submit" className="botao botao--primario" disabled={enviando}>
              {enviando ? <LoaderCircle className="girando" /> : <Send />}
              {enviando ? "Enviando…" : "Enviar pedido"}
            </button>
          </>
        )}
      </div>
    </form>
  );
}
