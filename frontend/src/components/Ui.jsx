// Pecas pequenas de interface usadas em varias telas. Cada uma e so
// apresentacao: recebe dados por props e devolve o pedaco de tela.

import { CircleCheck, CircleX, Clock3, Inbox } from "lucide-react";
import { useContagem } from "../useContagem";
import { corDoAvatar, formatarHoras, formatarSaldo, iniciais, NOMES_STATUS } from "../utils/formato";

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
