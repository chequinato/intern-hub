import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { CalendarClock, CircleAlert, FileSignature, LoaderCircle, Palmtree, Send, Trash2 } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { Barra, CarregandoPagina, ErroCarregar, Numero, Vazio } from "../../components/Ui";
import { formatarData, formatarDataHora, hojeIso, paraData } from "../../utils/formato";

const COR_STATUS = { pendente: "atencao", aprovado: "credito", rejeitado: "alerta" };
const NOME_STATUS = { pendente: "Esperando o gestor", aprovado: "Aprovado", rejeitado: "Recusado" };

// Contrato e recesso do estagiario (Entrega 3) - o que a Lei 11.788/2008
// garante e que ate aqui o sistema nao mostrava:
//   - o termo de compromisso tem fim e nao passa de 2 anos (art. 11);
//   - 30 dias de recesso por ano, proporcional: 2,5 por mes completo (art. 13).
// O termo e cadastrado pelo gestor; o recesso, o estagiario pede aqui.
export function Estagio() {
  const { estagiarioId, recarregar } = useOutletContext();
  const notificar = useNotificar();
  const estagio = useApiState(() => api.get(`/estagio/${estagiarioId}`), [estagiarioId]);
  const [cancelando, setCancelando] = useState(null);

  async function cancelar(pedido) {
    setCancelando(pedido.id);
    try {
      await api.delete(`/estagio/recessos/${pedido.id}`);
      notificar.info("Pedido cancelado", "Os dias voltaram para o seu saldo de recesso.");
      estagio.recarregar();
      recarregar();
    } catch (e) {
      notificar.erro("Não foi possível cancelar", e.message);
    } finally {
      setCancelando(null);
    }
  }

  if (estagio.erro) return <ErroCarregar mensagem={estagio.erro} aoTentar={estagio.recarregar} />;
  if (!estagio.dados) return <CarregandoPagina />;
  const { contrato, recesso, pedidos } = estagio.dados;

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Contrato e recesso</h1>
          <p>O seu termo de compromisso e os dias de recesso que a Lei do Estágio garante.</p>
        </div>
      </div>

      {contrato.vencendo && (
        <div className="aviso aviso--atencao entra" style={{ marginBottom: 16 }}>
          <CalendarClock />
          <div><strong>O seu contrato termina em {contrato.dias_restantes} dia(s).</strong> Converse com o gestor sobre renovação ou encerramento.</div>
        </div>
      )}

      <div className="grade grade-2">
        <CartaoContrato contrato={contrato} />

        <section className="cartao entra" style={{ "--i": 2 }}>
          <div className="cartao-cabeca"><h2><Palmtree />Recesso</h2><span className="sub">Lei 11.788/2008, art. 13</span></div>
          <div className="cartao-corpo pilha" style={{ gap: 16 }}>
            <div className="recesso-numeros">
              <div className="recesso-principal">
                <span>disponíveis</span>
                <b className="numero"><Numero valor={recesso.disponiveis} /></b>
                <small>dia(s) corridos</small>
              </div>
              <ul className="lista-regras">
                <li><span>Direito acumulado</span><b>{recesso.direito} dias</b></li>
                <li><span>Já aprovados</span><b>{recesso.aprovados} dias</b></li>
                <li><span>Pedidos esperando</span><b>{recesso.pendentes} dias</b></li>
              </ul>
            </div>
            <p className="texto-3" style={{ fontSize: 12.5 }}>
              {recesso.meses_completos} mês(es) completo(s) de estágio × 2,5 dias. Dia de recesso aprovado não conta como falta.
            </p>
          </div>
        </section>
      </div>

      <div className="espaco" />

      <div className="grade grade-principal">
        <section className="cartao entra" style={{ "--i": 3 }}>
          <div className="cartao-cabeca"><h2>Seus pedidos de recesso</h2><span className="sub">{pedidos.length} no total</span></div>
          {pedidos.length === 0 ? (
            <Vazio icone={Palmtree} titulo="Nenhum pedido ainda">Peça o recesso com antecedência: o gestor aprova antes de você sair.</Vazio>
          ) : (
            <ul className="lista-recessos">
              {pedidos.map((p, i) => (
                <li key={p.id} style={{ "--i": i }}>
                  <div className="recesso-periodo">
                    <b className="mono">{formatarData(p.data_inicio).slice(0, 5)} → {formatarData(p.data_fim).slice(0, 5)}</b>
                    <span>{p.dias} dia(s) · pedido em {formatarDataHora(p.pedido_em)}</span>
                    {p.observacao && <span className="texto-3">{p.observacao}</span>}
                  </div>
                  <span className={`selo selo--${COR_STATUS[p.status]}`}>{NOME_STATUS[p.status]}</span>
                  {p.status === "pendente" && (
                    <button type="button" className="botao botao--fantasma botao--icone" onClick={() => cancelar(p)} disabled={cancelando === p.id}
                      aria-label="Cancelar pedido" title="Cancelar pedido">
                      {cancelando === p.id ? <LoaderCircle className="girando" /> : <Trash2 />}
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        <PedirRecesso disponiveis={recesso.disponiveis} aoPedir={() => { estagio.recarregar(); recarregar(); }} />
      </div>
    </>
  );
}

export function CartaoContrato({ contrato, i = 1 }) {
  if (!contrato.cadastrado) {
    return (
      <section className="cartao entra" style={{ "--i": i }}>
        <div className="cartao-cabeca"><h2><FileSignature />Termo de compromisso</h2></div>
        <Vazio icone={FileSignature} titulo="Termo ainda não cadastrado">O gestor cadastra as datas do seu contrato de estágio.</Vazio>
      </section>
    );
  }
  const inicio = paraData(contrato.data_inicio);
  const fim = paraData(contrato.data_fim);
  const total = Math.max(1, (fim - inicio) / 86400000);
  const passados = Math.min(total, Math.max(0, (paraData(hojeIso()) - inicio) / 86400000));
  return (
    <section className="cartao entra" style={{ "--i": i }}>
      <div className="cartao-cabeca"><h2><FileSignature />Termo de compromisso</h2><span className="sub">Lei 11.788/2008, art. 11</span></div>
      <div className="cartao-corpo pilha" style={{ gap: 16 }}>
        <div className="contrato-restante">
          <b className={`numero${contrato.vencendo ? " atencao" : contrato.encerrado ? " alerta" : ""}`}>
            {contrato.encerrado ? "encerrado" : <Numero valor={contrato.dias_restantes} />}
          </b>
          {!contrato.encerrado && <span>dia(s) até o fim do contrato</span>}
        </div>
        <div>
          <Barra fracao={passados / total} tom={contrato.vencendo ? "atencao" : ""} />
          <div className="contrato-datas mono"><span>{formatarData(contrato.data_inicio)}</span><span>{formatarData(contrato.data_fim)}</span></div>
        </div>
        <ul className="lista-regras">
          <li><span>Instituição de ensino</span><b>{contrato.instituicao_ensino || "—"}</b></li>
          <li><span>Curso</span><b>{contrato.curso || "—"}</b></li>
        </ul>
      </div>
    </section>
  );
}

function PedirRecesso({ disponiveis, aoPedir }) {
  const notificar = useNotificar();
  const [inicio, setInicio] = useState("");
  const [fim, setFim] = useState("");
  const [observacao, setObservacao] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);
  const dias = inicio && fim && fim >= inicio ? Math.round((paraData(fim) - paraData(inicio)) / 86400000) + 1 : 0;

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await api.post("/estagio/recessos", { data_inicio: inicio, data_fim: fim, observacao: observacao.trim() || null });
      notificar.sucesso("Recesso pedido", `${dias} dia(s) a partir de ${formatarData(inicio)}. Agora é com o gestor.`);
      setInicio("");
      setFim("");
      setObservacao("");
      aoPedir();
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao entra" style={{ "--i": 4 }} onSubmit={enviar}>
      <div className="cartao-cabeca"><h2>Pedir recesso</h2><span className="sub">{disponiveis} dia(s) disponíveis</span></div>
      <div className="cartao-corpo pilha" style={{ gap: 14 }}>
        <div className="grade-campos">
          <div className="campo">
            <label htmlFor="rec-inicio">Primeiro dia</label>
            <input id="rec-inicio" type="date" min={hojeIso()} value={inicio} onChange={(e) => setInicio(e.target.value)} required />
          </div>
          <div className="campo">
            <label htmlFor="rec-fim">Último dia</label>
            <input id="rec-fim" type="date" min={inicio || hojeIso()} value={fim} onChange={(e) => setFim(e.target.value)} required />
          </div>
        </div>
        <div className="campo">
          <label htmlFor="rec-obs">Observação (opcional)</label>
          <input id="rec-obs" value={observacao} onChange={(e) => setObservacao(e.target.value)} maxLength={300} placeholder="Férias da faculdade" />
        </div>
        {dias > 0 && (
          <div className={`previa-mudanca${dias > disponiveis ? " previa-mudanca--alerta" : ""}`}>
            <b>{dias}</b> dia(s) corridos{dias > disponiveis ? ` — mais do que os ${disponiveis} disponíveis` : ` · sobram ${disponiveis - dias}`}
          </div>
        )}
        {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
        <button type="submit" className="botao botao--primario" disabled={enviando || disponiveis === 0}>
          {enviando ? <LoaderCircle className="girando" /> : <Send />}Enviar pedido
        </button>
      </div>
    </form>
  );
}
