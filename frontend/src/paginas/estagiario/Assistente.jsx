import { useEffect, useRef, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Info, MessageCircle, SendHorizontal, ShieldCheck } from "lucide-react";
import { acentuar, api } from "../../api/cliente";
import { Avatar } from "../../components/Ui";
import { primeiroNome } from "../../utils/formato";

const SUGESTOES = [
  "Qual é o meu saldo hoje?",
  "Tenho algum dia com pendência?",
  "E se eu faltar 2 dias?",
  "Como foi o meu mês passado?",
  "Estou perto do limite legal da semana?",
];

// Chat com o assistente de IA (funcionalidade 11 do refinamento). A API
// busca os numeros reais (saldo, semana, pendencias, meses anteriores,
// simulacao) e a IA so escreve a resposta em cima deles - ela nunca calcula.
// O historico vive so nesta tela: recarregar a pagina comeca de novo.
export function Assistente() {
  const { estagiarioId, estagiario } = useOutletContext();
  const [mensagens, setMensagens] = useState([]);
  const [texto, setTexto] = useState("");
  const [pensando, setPensando] = useState(false);
  const fimDaConversa = useRef(null);

  useEffect(() => {
    fimDaConversa.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensagens, pensando]);

  async function perguntar(pergunta) {
    const conteudo = pergunta.trim();
    if (conteudo.length < 3 || pensando) return;
    setMensagens((m) => [...m, { autor: "voce", texto: conteudo }]);
    setTexto("");
    setPensando(true);
    try {
      const { resposta } = await api.post("/assistente/perguntar", { estagiario_id: estagiarioId, pergunta: conteudo });
      // Sem chave de IA a API responde em modo demonstracao (so os numeros,
      // sem IA) ou com um aviso de falha - os dois aparecem como aviso.
      const ehAviso = /Modo demonstração|não está configurado|Não consegui falar/i.test(resposta);
      // No modo demonstracao o texto vem dos dados crus da API (sem acento,
      // decimal com ponto); acentuar() deixa no formato brasileiro.
      setMensagens((m) => [...m, { autor: "assistente", texto: ehAviso ? acentuar(resposta) : resposta, aviso: ehAviso }]);
    } catch (e) {
      setMensagens((m) => [...m, { autor: "assistente", texto: e.message, aviso: true }]);
    } finally {
      setPensando(false);
    }
  }

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Assistente de IA</h1>
          <p>Pergunte sobre seu saldo, sua semana e cenários. As respostas usam só os seus dados.</p>
        </div>
      </div>

      <section className="cartao chat entra" style={{ "--i": 1 }}>
        <div className="chat-mensagens">
          {mensagens.length === 0 && (
            <div className="chat-boas-vindas">
              <div className="vazio-icone"><MessageCircle /></div>
              <h2>Olá, {primeiroNome(estagiario.nome)}. Como posso ajudar?</h2>
              <p>O assistente lê o seu saldo, as horas da semana, as pendências e os últimos meses direto do banco de horas.</p>
              <div className="fichas" style={{ justifyContent: "center", marginTop: 16 }}>
                {SUGESTOES.map((s) => (
                  <button key={s} type="button" className="ficha" onClick={() => perguntar(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {mensagens.map((m, i) => (
            <div key={i} className={`bolha-linha bolha-linha--${m.autor}`}>
              {m.autor === "assistente" ? (
                <span className="bolha-avatar"><MessageCircle size={16} /></span>
              ) : (
                <Avatar nome={estagiario.nome} tamanho={30} />
              )}
              <div className={`bolha bolha--${m.autor}${m.aviso ? " bolha--aviso" : ""}`}>
                {m.aviso && <Info size={15} style={{ display: "inline", verticalAlign: "-2px", marginRight: 6 }} />}
                {m.texto}
              </div>
            </div>
          ))}

          {pensando && (
            <div className="bolha-linha bolha-linha--assistente">
              <span className="bolha-avatar"><MessageCircle size={16} /></span>
              <div className="bolha bolha--assistente digitando" aria-label="Respondendo">
                <i /><i /><i />
              </div>
            </div>
          )}
          <div ref={fimDaConversa} />
        </div>

        <form className="chat-entrada" onSubmit={(e) => { e.preventDefault(); perguntar(texto); }}>
          <input
            className="entrada"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Escreva sua pergunta…"
            maxLength={500}
            aria-label="Sua pergunta"
          />
          <button type="submit" className="botao botao--primario" disabled={pensando || texto.trim().length < 3}>
            <SendHorizontal />Enviar
          </button>
        </form>
        <div className="chat-rodape"><ShieldCheck size={14} />A IA não calcula nada: ela só explica os números que o sistema já calculou.</div>
      </section>
    </>
  );
}
