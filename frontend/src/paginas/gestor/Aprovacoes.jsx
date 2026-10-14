import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { ArrowRight, Check, ClipboardCheck, LoaderCircle, Quote, X } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { Avatar, Esqueleto, Vazio } from "../../components/Ui";
import { diaDaSemana, formatarData, formatarDataHora, formatarSaldo, hora, NOMES_CAMPOS } from "../../utils/formato";

// Fila do gestor: pedidos pendentes dos estagiarios sob a gestao dele.
// Aprovar aplica o horario no registro e devolve o saldo novo; rejeitar so
// fecha o pedido, sem mexer no registro (servicos/solicitacao.py).
export function Aprovacoes() {
  const { gestorId, recarregar } = useOutletContext();
  const notificar = useNotificar();
  const fila = useApiState(() => api.get("/solicitacoes/pendentes", { gestor_id: gestorId }), [gestorId]);
  const [decidindo, setDecidindo] = useState(null);

  async function decidir(pedido, status) {
    setDecidindo({ id: pedido.id, status });
    try {
      const resultado = await api.patch(`/solicitacoes/${pedido.id}`, { status, gestor_id: gestorId });
      if (status === "aprovado") {
        notificar.sucesso(
          `Ajuste de ${pedido.estagiario_nome} aprovado`,
          `${NOMES_CAMPOS[pedido.campo_alterado]} de ${formatarData(pedido.data_registro)} agora é ${hora(pedido.horario_sugerido)}. Saldo atual: ${formatarSaldo(resultado.saldo_acumulado, 2)}.`
        );
      } else {
        notificar.info(`Pedido de ${pedido.estagiario_nome} rejeitado`, "O registro de ponto continua como estava.");
      }
      fila.setDados((lista) => lista.filter((p) => p.id !== pedido.id));
      recarregar();
    } catch (e) {
      notificar.erro("Não foi possível registrar a decisão", e.message);
    } finally {
      setDecidindo(null);
    }
  }

  const pedidos = fila.dados || [];

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Fila de aprovações</h1>
          <p>Pedidos de ajuste de ponto esperando a sua decisão.</p>
        </div>
        {pedidos.length > 0 && <span className="selo selo--atencao" style={{ height: 30, fontSize: 13 }}>{pedidos.length} pendente(s)</span>}
      </div>

      {fila.carregando && !fila.dados ? (
        <div className="pilha">{[0, 1].map((n) => <Esqueleto key={n} altura={170} style={{ borderRadius: 14 }} />)}</div>
      ) : fila.erro ? (
        <div className="aviso aviso--alerta">{fila.erro}</div>
      ) : pedidos.length === 0 ? (
        <section className="cartao entra">
          <Vazio icone={ClipboardCheck} titulo="Fila zerada">
            Nenhum pedido esperando decisão. Quando um estagiário pedir um ajuste, ele aparece aqui.
          </Vazio>
        </section>
      ) : (
        <div className="grade grade-2">
          {pedidos.map((p, i) => {
            const ocupado = decidindo?.id === p.id;
            return (
              <article key={p.id} className="cartao pedido-gestor entra" style={{ "--i": i }}>
                <div className="cartao-cabeca">
                  <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <Avatar nome={p.estagiario_nome} tamanho={36} />
                    <span>
                      <b style={{ display: "block" }}>{p.estagiario_nome}</b>
                      <span className="texto-3" style={{ fontSize: 12.5 }}>pediu em {formatarDataHora(p.data_solicitacao)}</span>
                    </span>
                  </span>
                  <span className="selo">{diaDaSemana(p.data_registro)}, {formatarData(p.data_registro)}</span>
                </div>
                <div className="cartao-corpo pilha" style={{ gap: 14 }}>
                  <div>
                    <div className="rotulo">{NOMES_CAMPOS[p.campo_alterado]}</div>
                    <div className="mudanca-grande">
                      <span className={p.horario_atual ? "" : "texto-3"}>{hora(p.horario_atual)}</span>
                      <ArrowRight />
                      <span className="credito">{hora(p.horario_sugerido)}</span>
                    </div>
                  </div>
                  <blockquote className="citacao"><Quote size={14} />{p.justificativa}</blockquote>
                </div>
                <div className="cartao-rodape" style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                  <button type="button" className="botao botao--perigo" onClick={() => decidir(p, "rejeitado")} disabled={ocupado}>
                    {ocupado && decidindo.status === "rejeitado" ? <LoaderCircle className="girando" /> : <X />}Rejeitar
                  </button>
                  <button type="button" className="botao botao--sucesso" onClick={() => decidir(p, "aprovado")} disabled={ocupado}>
                    {ocupado && decidindo.status === "aprovado" ? <LoaderCircle className="girando" /> : <Check />}Aprovar
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}
