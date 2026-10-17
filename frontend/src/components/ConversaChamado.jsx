import { useState } from "react";
import { CircleAlert, CircleCheck, LoaderCircle, Play, SendHorizontal } from "lucide-react";
import { api } from "../api/cliente";
import { useNotificar } from "./Notificacoes";
import { Avatar, Prioridade, SeloChamado } from "./Ui";
import { formatarDataHora, NOMES_CATEGORIA } from "../utils/formato";

// Um chamado aberto na tela: cabecalho, conversa e caixa de resposta. Serve
// as duas pontas - o estagiario (que so escreve) e o gestor (que tambem
// muda o andamento). Quem escreveu cada mensagem vem da API ("estagiario" ou
// "gestor"); a API tira isso do login, e nao do que a tela manda.
export function ConversaChamado({ chamado, souGestor = false, aoAtualizar }) {
  const notificar = useNotificar();
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);
  const fechado = chamado.status === "resolvido";

  async function enviar(e) {
    e.preventDefault();
    if (!texto.trim()) return;
    setEnviando(true);
    setErro(null);
    try {
      const atualizado = await api.post(`/chamados/${chamado.id}/mensagens`, { texto: texto.trim() });
      setTexto("");
      aoAtualizar(atualizado);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  async function mudarStatus(status) {
    setEnviando(true);
    setErro(null);
    try {
      const atualizado = await api.patch(`/chamados/${chamado.id}`, { status });
      notificar.sucesso(status === "resolvido" ? "Chamado resolvido" : "Chamado em andamento", chamado.titulo);
      aoAtualizar(atualizado);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="conversa">
      <div className="conversa-cabeca">
        <div className="conversa-meta">
          <span className="mono">#{String(chamado.id).padStart(4, "0")}</span>
          <span>{NOMES_CATEGORIA[chamado.categoria]}</span>
          <Prioridade nivel={chamado.prioridade} />
        </div>
        <h3>{chamado.titulo}</h3>
        <div className="conversa-meta">
          <SeloChamado status={chamado.status} />
          <span>aberto em {formatarDataHora(chamado.aberto_em)}</span>
          {chamado.resolvido_em && <span>· resolvido em {formatarDataHora(chamado.resolvido_em)}</span>}
        </div>
      </div>

      <ol className="conversa-linha">
        {chamado.mensagens.map((m, i) => {
          const nome = m.autor === "gestor" ? chamado.gestor_nome : chamado.estagiario_nome;
          return (
            <li key={m.id} className={`conversa-msg conversa-msg--${m.autor}`} style={{ "--i": i }}>
              <Avatar nome={nome} tamanho={28} />
              <div>
                <div className="conversa-autor">
                  <b>{nome}</b>
                  <span>{m.autor === "gestor" ? "gestor" : "estagiário"} · {formatarDataHora(m.enviada_em)}</span>
                </div>
                <p>{m.texto}</p>
              </div>
            </li>
          );
        })}
      </ol>

      {erro && <div className="aviso aviso--alerta" style={{ margin: "0 20px 12px" }}><CircleAlert />{erro}</div>}

      {fechado ? (
        <div className="conversa-fechada"><CircleCheck />Chamado resolvido. Se o problema voltar, abra um novo.</div>
      ) : (
        <form className="conversa-resposta" onSubmit={enviar}>
          <textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            maxLength={1000}
            rows={2}
            placeholder={souGestor ? "Responda ao estagiário ou registre o encaminhamento…" : "Acrescente uma informação…"}
            aria-label="Mensagem"
          />
          <div className="conversa-acoes">
            {souGestor && chamado.status === "aberto" && (
              <button type="button" className="botao botao--pequeno" onClick={() => mudarStatus("em_andamento")} disabled={enviando}>
                <Play />Assumir
              </button>
            )}
            {souGestor && (
              <button type="button" className="botao botao--pequeno botao--sucesso" onClick={() => mudarStatus("resolvido")} disabled={enviando}>
                <CircleCheck />Marcar resolvido
              </button>
            )}
            <button type="submit" className="botao botao--primario botao--pequeno" disabled={enviando || !texto.trim()}>
              {enviando ? <LoaderCircle className="girando" /> : <SendHorizontal />}Enviar
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
