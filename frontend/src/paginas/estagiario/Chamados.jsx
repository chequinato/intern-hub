import { useState } from "react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { CircleAlert, LifeBuoy, LoaderCircle, Plus, SendHorizontal, X } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { ConversaChamado } from "../../components/ConversaChamado";
import { Esqueleto, Prioridade, SeloChamado, Vazio } from "../../components/Ui";
import { haQuantoTempo, NOMES_CATEGORIA, NOMES_PRIORIDADE } from "../../utils/formato";

// Chamados ao gestor (Entrega 3): o canal para o que nao e ajuste de ponto -
// acesso bloqueado, equipamento, sistema fora do ar, documento. O gestor
// responsavel recebe, encaminha para quem resolve e marca o andamento.
export function Chamados() {
  const { estagiario, recarregar: recarregarArea } = useOutletContext();
  const lista = useApiState(() => api.get("/chamados"), []);
  const [busca, setBusca] = useSearchParams();
  const selecionadoId = Number(busca.get("id")) || null;
  const novo = busca.get("novo") === "1";
  const detalhe = useApiState(
    () => (selecionadoId ? api.get(`/chamados/${selecionadoId}`) : Promise.resolve(null)),
    [selecionadoId]
  );

  const chamados = lista.dados || [];
  const emAberto = chamados.filter((c) => c.status !== "resolvido");
  const resolvidos = chamados.filter((c) => c.status === "resolvido");

  function abrir(id) {
    setBusca(id ? { id: String(id) } : {});
  }

  function atualizar(chamado) {
    detalhe.setDados(chamado);
    lista.recarregar();
    recarregarArea();
  }

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Chamados ao gestor</h1>
          <p>Para o que não é ajuste de ponto: acesso, equipamento, sistema, documentos. Quem recebe é {estagiario.gestor_id ? "o seu gestor" : "o gestor responsável"}.</p>
        </div>
        <div className="acoes">
          <button type="button" className="botao botao--primario" onClick={() => setBusca({ novo: "1" })}>
            <Plus />Novo chamado
          </button>
        </div>
      </div>

      {!estagiario.gestor_id && (
        <div className="aviso aviso--atencao entra" style={{ marginBottom: 16 }}>
          <CircleAlert />Você ainda não tem gestor responsável, então não há quem receba um chamado. Peça para um gestor vincular você à equipe dele.
        </div>
      )}

      <div className="grade grade-chamados">
        <section className="cartao entra" style={{ "--i": 1 }}>
          <div className="cartao-cabeca">
            <h2>Seus chamados</h2>
            <span className="sub">{emAberto.length} em aberto</span>
          </div>
          {lista.carregando && !lista.dados ? (
            <div className="cartao-corpo pilha">{[0, 1, 2].map((n) => <Esqueleto key={n} altura={64} />)}</div>
          ) : chamados.length === 0 ? (
            <Vazio icone={LifeBuoy} titulo="Nenhum chamado ainda">Quando algo travar seu trabalho e não for ponto, abra um chamado.</Vazio>
          ) : (
            <ListaChamados grupos={[["Em aberto", emAberto], ["Resolvidos", resolvidos]]} selecionado={selecionadoId} aoAbrir={abrir} />
          )}
        </section>

        <section className="cartao entra" style={{ "--i": 2 }}>
          {novo ? (
            <NovoChamado aoCancelar={() => abrir(null)} aoCriar={(c) => { lista.recarregar(); recarregarArea(); abrir(c.id); }} />
          ) : selecionadoId && detalhe.dados ? (
            <ConversaChamado chamado={detalhe.dados} aoAtualizar={atualizar} />
          ) : selecionadoId && detalhe.erro ? (
            <Vazio icone={CircleAlert} titulo="Não foi possível abrir">{detalhe.erro}</Vazio>
          ) : selecionadoId ? (
            <div className="cartao-corpo pilha"><Esqueleto altura={30} /><Esqueleto altura={160} /></div>
          ) : (
            <Vazio icone={LifeBuoy} titulo="Escolha um chamado">A conversa com o gestor aparece aqui.</Vazio>
          )}
        </section>
      </div>
    </>
  );
}

export function ListaChamados({ grupos, selecionado, aoAbrir, mostrarEstagiario = false }) {
  return (
    <div className="lista-chamados">
      {grupos.filter(([, itens]) => itens.length > 0).map(([titulo, itens]) => (
        <div key={titulo}>
          {titulo && <div className="lista-chamados-grupo">{titulo}</div>}
          <ul>
            {itens.map((c, i) => (
              <li key={c.id} style={{ "--i": i }}>
                <button type="button" className={`chamado-linha${c.id === selecionado ? " ativo" : ""}`} onClick={() => aoAbrir(c.id)}>
                  <span className="chamado-linha-topo">
                    <span className="mono">#{String(c.id).padStart(4, "0")}</span>
                    <Prioridade nivel={c.prioridade} />
                    <span className="chamado-tempo">{haQuantoTempo(c.atualizado_em)}</span>
                  </span>
                  <b>{c.titulo}</b>
                  <span className="chamado-linha-rodape">
                    <SeloChamado status={c.status} />
                    <span>{mostrarEstagiario ? c.estagiario_nome : NOMES_CATEGORIA[c.categoria]}</span>
                    {c.status !== "resolvido" && c.ultima_mensagem_de === (mostrarEstagiario ? "estagiario" : "gestor") && (
                      <span className="chamado-novidade">resposta nova</span>
                    )}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function NovoChamado({ aoCancelar, aoCriar }) {
  const notificar = useNotificar();
  const [form, setForm] = useState({ titulo: "", categoria: "acesso", prioridade: "media", descricao: "" });
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);
  const mudar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const criado = await api.post("/chamados", form);
      notificar.sucesso("Chamado aberto", "O gestor já pode ver na fila dele.");
      aoCriar(criado);
    } catch (e2) {
      setErro(e2.message);
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar}>
      <div className="cartao-cabeca">
        <h2>Novo chamado</h2>
        <button type="button" className="botao botao--fantasma botao--pequeno" onClick={aoCancelar}><X />Cancelar</button>
      </div>
      <div className="cartao-corpo pilha" style={{ gap: 14 }}>
        <div className="campo">
          <label htmlFor="ch-titulo">Assunto</label>
          <input id="ch-titulo" value={form.titulo} onChange={mudar("titulo")} minLength={3} maxLength={120} placeholder="Sem acesso à VPN" autoFocus required />
        </div>
        <div className="grade-campos">
          <div className="campo">
            <label htmlFor="ch-categoria">Categoria</label>
            <select id="ch-categoria" value={form.categoria} onChange={mudar("categoria")}>
              {Object.entries(NOMES_CATEGORIA).map(([valor, nome]) => <option key={valor} value={valor}>{nome}</option>)}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="ch-prioridade">Prioridade</label>
            <select id="ch-prioridade" value={form.prioridade} onChange={mudar("prioridade")}>
              {Object.entries(NOMES_PRIORIDADE).map(([valor, nome]) => <option key={valor} value={valor}>{nome}</option>)}
            </select>
          </div>
        </div>
        <div className="campo">
          <label htmlFor="ch-descricao">O que está acontecendo</label>
          <textarea id="ch-descricao" value={form.descricao} onChange={mudar("descricao")} minLength={5} maxLength={1000} rows={5}
            placeholder="Desde quando, o que você já tentou, o que está parado por causa disso." required />
          <span className="dica">Alta: o trabalho parou. Média: atrapalha, mas dá para seguir. Baixa: pode esperar.</span>
        </div>
        {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
        <button type="submit" className="botao botao--primario" disabled={enviando}>
          {enviando ? <LoaderCircle className="girando" /> : <SendHorizontal />}Abrir chamado
        </button>
      </div>
    </form>
  );
}
