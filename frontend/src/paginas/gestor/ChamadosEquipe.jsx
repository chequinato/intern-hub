import { useState } from "react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { CircleAlert, LifeBuoy } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { ConversaChamado } from "../../components/ConversaChamado";
import { Esqueleto, Vazio } from "../../components/Ui";
import { ListaChamados } from "../estagiario/Chamados";

const FILTROS = [
  ["abertos", "Em aberto"],
  ["resolvidos", "Resolvidos"],
  ["todos", "Todos"],
];

// Fila de chamados do gestor (Entrega 3). A API ja devolve na ordem de
// atendimento: em aberto antes dos resolvidos, prioridade alta primeiro e,
// empatando, quem espera ha mais tempo (servicos/chamados.py, com case()).
export function ChamadosEquipe() {
  const { recarregar: recarregarArea } = useOutletContext();
  const lista = useApiState(() => api.get("/chamados"), []);
  const [filtro, setFiltro] = useState("abertos");
  const [busca, setBusca] = useSearchParams();
  const selecionadoId = Number(busca.get("id")) || null;
  const detalhe = useApiState(
    () => (selecionadoId ? api.get(`/chamados/${selecionadoId}`) : Promise.resolve(null)),
    [selecionadoId]
  );

  const todos = lista.dados || [];
  const visiveis = todos.filter((c) =>
    filtro === "todos" ? true : filtro === "resolvidos" ? c.status === "resolvido" : c.status !== "resolvido"
  );
  const semResposta = todos.filter((c) => c.status === "aberto").length;

  function atualizar(chamado) {
    detalhe.setDados(chamado);
    lista.recarregar();
    recarregarArea();
  }

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Chamados da equipe</h1>
          <p>
            {semResposta
              ? `${semResposta} chamado(s) ainda sem resposta. Responder já coloca o chamado em andamento.`
              : "Nenhum chamado esperando a primeira resposta."}
          </p>
        </div>
        <div className="segmentado">
          {FILTROS.map(([valor, rotulo]) => (
            <button key={valor} type="button" className={filtro === valor ? "ativo" : ""} onClick={() => setFiltro(valor)}>{rotulo}</button>
          ))}
        </div>
      </div>

      <div className="grade grade-chamados">
        <section className="cartao entra" style={{ "--i": 1 }}>
          <div className="cartao-cabeca">
            <h2>Fila de atendimento</h2>
            <span className="sub">prioridade alta primeiro</span>
          </div>
          {lista.carregando && !lista.dados ? (
            <div className="cartao-corpo pilha">{[0, 1, 2].map((n) => <Esqueleto key={n} altura={64} />)}</div>
          ) : visiveis.length === 0 ? (
            <Vazio icone={LifeBuoy} titulo={filtro === "resolvidos" ? "Nenhum chamado resolvido" : "Fila vazia"}>
              Os chamados que a equipe abrir aparecem aqui.
            </Vazio>
          ) : (
            <ListaChamados grupos={[["", visiveis]]} selecionado={selecionadoId} aoAbrir={(id) => setBusca({ id: String(id) })} mostrarEstagiario />
          )}
        </section>

        <section className="cartao entra" style={{ "--i": 2 }}>
          {selecionadoId && detalhe.dados ? (
            <ConversaChamado chamado={detalhe.dados} souGestor aoAtualizar={atualizar} />
          ) : selecionadoId && detalhe.erro ? (
            <Vazio icone={CircleAlert} titulo="Não foi possível abrir">{detalhe.erro}</Vazio>
          ) : selecionadoId ? (
            <div className="cartao-corpo pilha"><Esqueleto altura={30} /><Esqueleto altura={160} /></div>
          ) : (
            <Vazio icone={LifeBuoy} titulo="Escolha um chamado">A conversa com o estagiário e as ações aparecem aqui.</Vazio>
          )}
        </section>
      </div>
    </>
  );
}
