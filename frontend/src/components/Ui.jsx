// Pecas pequenas de interface usadas em varias telas. Cada uma e so
// apresentacao: recebe dados por props e devolve o pedaco de tela.

import { useEffect } from "react";
import { CircleCheck, CircleX, Clock3, Inbox, X } from "lucide-react";
import { useContagem } from "../useContagem";
import {
  corDoAvatar, formatarHoras, formatarSaldo, iniciais, NOMES_PRIORIDADE, NOMES_STATUS, NOMES_STATUS_CHAMADO,
} from "../utils/formato";

// Numero que conta ate o valor (ver useContagem.js).
// formato: "saldo" (+2,5h), "horas" (6,5h) ou "inteiro" (12)
export function Numero({ valor, formato = "inteiro", casas = 1 }) {
  const animado = useContagem(valor);
  if (formato === "saldo") return <>{formatarSaldo(animado, casas)}</>;
  if (formato === "horas") return <>{formatarHoras(animado, casas)}</>;
  return <>{Math.round(animado)}</>;
}

export function Avatar({ nome, tamanho = 36 }) {
  return (
    <span className="avatar" style={{ "--tam": `${tamanho}px`, "--cor-avatar": corDoAvatar(nome) }} aria-hidden="true">
      {iniciais(nome)}
    </span>
  );
}

const ICONE_STATUS = { pendente: Clock3, aprovado: CircleCheck, rejeitado: CircleX };
const COR_STATUS = { pendente: "atencao", aprovado: "credito", rejeitado: "alerta" };

export function SeloStatus({ status }) {
  const Icone = ICONE_STATUS[status] || Clock3;
  return (
    <span className={`selo selo--${COR_STATUS[status] || "info"}`}>
      <Icone />
      {NOMES_STATUS[status] || status}
    </span>
  );
}

// Um numero da faixa de indicadores: rotulo, valor e uma linha de contexto.
// A faixa inteira e um cartao so, com divisorias entre os numeros - e nao
// quatro cartoes iguais lado a lado. `destaque` deixa o numero principal
// da tela maior que os outros.
export function Indicador({ rotulo, children, rodape, destaque = false }) {
  return (
    <div className={`faixa-item${destaque ? " faixa-item--destaque" : ""}`}>
      <span className="indicador-rotulo">{rotulo}</span>
      <div className="indicador-valor">{children}</div>
      {rodape && <div className="indicador-rodape">{rodape}</div>}
    </div>
  );
}

export function Barra({ fracao, tom = "", fina = false }) {
  const pct = Math.max(0, Math.min(1, Number(fracao) || 0)) * 100;
  return (
    <div className={`barra${tom ? ` barra--${tom}` : ""}${fina ? " barra--fina" : ""}`}>
      <span style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Vazio({ icone: Icone = Inbox, titulo, children, acao }) {
  return (
    <div className="vazio">
      <div className="vazio-icone"><Icone /></div>
      <h3>{titulo}</h3>
      {children && <p>{children}</p>}
      {acao && <div style={{ marginTop: 8 }}>{acao}</div>}
    </div>
  );
}

export function Esqueleto({ altura = 16, largura = "100%", style }) {
  return <div className="esqueleto" style={{ height: altura, width: largura, ...style }} />;
}

// Bloco de carregamento com a forma aproximada da tela, no lugar de um
// "Carregando..." solto - a tela nao "pula" quando os dados chegam.
export function CarregandoPagina() {
  return (
    <div className="pilha" aria-busy="true" aria-label="Carregando">
      <Esqueleto altura={30} largura="38%" />
      <Esqueleto altura={104} style={{ borderRadius: 10 }} />
      <Esqueleto altura={280} style={{ borderRadius: 10 }} />
    </div>
  );
}

export function ErroCarregar({ mensagem, aoTentar }) {
  return (
    <div className="cartao">
      <Vazio icone={CircleX} titulo="Não foi possível carregar" acao={aoTentar && (
        <button type="button" className="botao" onClick={aoTentar}>Tentar de novo</button>
      )}>
        {mensagem}
      </Vazio>
    </div>
  );
}

// Anel de progresso (horas da semana em relacao ao limite legal).
export function AnelProgresso({ fracao, tamanho = 132, espessura = 12, tom = "marca", children }) {
  const raio = (tamanho - espessura) / 2;
  const circunferencia = 2 * Math.PI * raio;
  const pct = Math.max(0, Math.min(1, Number(fracao) || 0));
  const cores = { marca: "var(--marca-500)", atencao: "var(--atencao-forte)", alerta: "var(--alerta)" };
  return (
    <div style={{ position: "relative", width: tamanho, height: tamanho, flex: "none" }}>
      <svg width={tamanho} height={tamanho} style={{ transform: "rotate(-90deg)" }} aria-hidden="true">
        <circle cx={tamanho / 2} cy={tamanho / 2} r={raio} fill="none" stroke="var(--superficie-3)" strokeWidth={espessura} />
        <circle
          cx={tamanho / 2} cy={tamanho / 2} r={raio} fill="none"
          stroke={cores[tom] || cores.marca} strokeWidth={espessura} strokeLinecap="round"
          strokeDasharray={circunferencia}
          strokeDashoffset={circunferencia * (1 - pct)}
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(.2,.8,.2,1)" }}
        />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", textAlign: "center" }}>
        {children}
      </div>
    </div>
  );
}

// --- Entrega 3 -------------------------------------------------------------

const COR_STATUS_CHAMADO = { aberto: "atencao", em_andamento: "info", resolvido: "credito" };

export function SeloChamado({ status }) {
  return (
    <span className={`selo selo--${COR_STATUS_CHAMADO[status] || "info"}`}>
      <span className={`ponto${status === "em_andamento" ? " ponto--vivo" : ""}`} />
      {NOMES_STATUS_CHAMADO[status] || status}
    </span>
  );
}

// Prioridade como tres barrinhas (uma, duas ou tres cheias): le-se de longe
// sem depender so da cor.
export function Prioridade({ nivel }) {
  const cheias = { baixa: 1, media: 2, alta: 3 }[nivel] || 1;
  return (
    <span className={`prioridade prioridade--${nivel}`} title={`Prioridade ${NOMES_PRIORIDADE[nivel]}`}>
      {[1, 2, 3].map((n) => <i key={n} className={n <= cheias ? "cheia" : ""} />)}
      <span>{NOMES_PRIORIDADE[nivel]}</span>
    </span>
  );
}

// Painel que desliza da direita por cima da tela (detalhes de um item sem
// sair da lista). Fecha no X, no Esc ou clicando fora.
export function Gaveta({ aberta, titulo, subtitulo, aoFechar, children }) {
  useEffect(() => {
    if (!aberta) return undefined;
    const tecla = (e) => e.key === "Escape" && aoFechar();
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [aberta, aoFechar]);

  if (!aberta) return null;
  return (
    <div className="gaveta-fundo" onClick={aoFechar}>
      <aside className="gaveta" role="dialog" aria-modal="true" aria-label={titulo} onClick={(e) => e.stopPropagation()}>
        <header className="gaveta-cabeca">
          <div>
            <h2>{titulo}</h2>
            {subtitulo && <span className="sub">{subtitulo}</span>}
          </div>
          <button type="button" className="botao botao--fantasma botao--icone" onClick={aoFechar} aria-label="Fechar"><X /></button>
        </header>
        <div className="gaveta-corpo">{children}</div>
      </aside>
    </div>
  );
}
