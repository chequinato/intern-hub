import { useEffect, useState } from "react";
import { Check, Clock3, FileText } from "lucide-react";
import { useAgora } from "../useAgora";
import { Numero } from "./Ui";

// Vitrine da tela de entrada: um pedaco do painel do sistema, inclinado em
// perspectiva. E so ilustracao (numeros de exemplo, sem dados de ninguem).
//
// Animacao: o painel entra girando ate a posicao inclinada, as barras crescem
// uma de cada vez e os numeros contam. Depois ele fica parado nessa posicao,
// mas vivo: o relogio corre, as barras se rearranjam devagar e as
// notificacoes se alternam.

const DIAS = ["seg", "ter", "qua", "qui", "sex", "seg", "ter", "qua", "qui", "sex"];
const AVISOS = [
  { icone: Check, titulo: "Ajuste aprovado", texto: "Carla aprovou o retorno das 13:00" },
  { icone: Clock3, titulo: "Entrada registrada", texto: "Hoje às 09:02 · próxima: almoço" },
  { icone: FileText, titulo: "Relatório exportado", texto: "Setembro de 2026 · PDF" },
];

// Alturas de uma quinzena "realista": a maioria perto da meta, alguns dias
// acima. O ultimo e o dia de hoje, ainda em andamento.
function novaQuinzena() {
  return DIAS.map((_, i) => (i === DIAS.length - 1 ? 38 + Math.random() * 14 : 58 + Math.random() * 40));
}

const semMovimento = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export function VitrinePainel() {
  const agora = useAgora(1000);
  const [alturas, setAlturas] = useState(() => DIAS.map(() => 0));
  const [aviso, setAviso] = useState(0);

  useEffect(() => {
    // Primeiro quadro com as barras zeradas; logo depois, crescem.
    const inicio = setTimeout(() => setAlturas(novaQuinzena()), 450);
    if (semMovimento()) return () => clearTimeout(inicio);
    const barras = setInterval(() => setAlturas(novaQuinzena()), 3600);
    const avisos = setInterval(() => setAviso((n) => (n + 1) % AVISOS.length), 4200);
    return () => {
      clearTimeout(inicio);
      clearInterval(barras);
      clearInterval(avisos);
    };
  }, []);

  const relogio = agora.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const Icone = AVISOS[aviso].icone;

  return (
    <div className="vitrine-cena" aria-hidden="true">
      <div className="vitrine-painel">
        <div className="vitrine-topo">
          <span className="vitrine-pontos"><i /><i /><i /></span>
          <span>Painel · Lucas Andrade</span>
        </div>

        <div className="vitrine-numeros">
          <div className="vitrine-cartao vitrine-cartao--destaque">
            <small>Saldo do banco de horas</small>
            <b className="vitrine-laranja"><Numero valor={4.8} formato="saldo" /></b>
            <span>crédito acumulado</span>
          </div>
          <div className="vitrine-cartao">
            <small>Semana</small>
            <b><Numero valor={28} />/30h</b>
            <div className="vitrine-barra"><span style={{ width: alturas[0] ? "93%" : "0%" }} /></div>
          </div>
          <div className="vitrine-cartao">
            <small>Pendências</small>
            <b><Numero valor={1} /></b>
            <span>almoço sem retorno</span>
          </div>
        </div>

        <div className="vitrine-grafico">
          <div className="vitrine-grafico-topo">
            <small>Horas por dia · últimas duas semanas</small>
            <span><i className="vitrine-legenda-meta" />meta 6h</span>
          </div>
          <div className="vitrine-barras">
            <div className="vitrine-meta" />
            {alturas.map((altura, i) => {
              const hoje = i === alturas.length - 1;
              const acima = !hoje && altura > 86;
              return (
                <div key={i} className="vitrine-coluna">
                  <span
                    className={`vitrine-coluna-barra${acima ? " acima" : ""}${hoje ? " hoje" : ""}`}
                    style={{ height: `${altura}%`, transitionDelay: `${i * 60}ms` }}
                  />
                  <small>{DIAS[i]}</small>
                </div>
              );
            })}
          </div>
        </div>

        <div className="vitrine-rodape">
          <div className="vitrine-cartao vitrine-ponto">
            <small>Ponto de hoje <em>● trabalhando</em></small>
            <b className="mono">{relogio}</b>
            <div className="vitrine-linha">
              <i className="feito" /><i className="feito" /><i className="proximo" /><i />
            </div>
          </div>
          <div className="vitrine-cartao vitrine-aviso" key={aviso}>
            <span className="vitrine-aviso-icone"><Icone /></span>
            <div>
              <b>{AVISOS[aviso].titulo}</b>
              <span>{AVISOS[aviso].texto}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
