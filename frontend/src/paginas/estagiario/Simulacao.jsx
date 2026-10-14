import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { ArrowRight, CalendarOff, CircleAlert, CircleCheck, Clock3, Zap } from "lucide-react";
import { api } from "../../api/cliente";
import { formatarHoras, formatarSaldo, plural } from "../../utils/formato";

// Cenarios prontos para um clique: preenchem os deslizantes.
const ATALHOS = [
  { rotulo: "Faltar amanhã", dias: 1, horas: 0 },
  { rotulo: "Folga na sexta e na segunda", dias: 2, horas: 0 },
  { rotulo: "Uma semana de provas", dias: 5, horas: 0 },
  { rotulo: "Atrasar 30 min por 5 dias", dias: 0, horas: 2.5 },
];

// "E se eu faltar / chegar atrasado" (funcionalidade 10 da Entrega 1).
// So projeta: POST /simulacoes nunca grava nada no banco. Os deslizantes
// recalculam sozinhos, um instante depois de parar de mexer.
export function Simulacao() {
  const { estagiarioId, estagiario } = useOutletContext();
  const [dias, setDias] = useState(0);
  const [horas, setHoras] = useState(0);
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    let ativo = true;
    const espera = setTimeout(() => {
      api.post("/simulacoes", { estagiario_id: estagiarioId, dias_falta: dias, horas_atraso: horas })
        .then((r) => ativo && (setResultado(r), setErro(null)))
        .catch((e) => ativo && setErro(e.message));
    }, 220);
    return () => {
      ativo = false;
      clearTimeout(espera);
    };
  }, [estagiarioId, dias, horas]);

  const limite = estagiario.configuracao?.limite_alerta_negativo ?? -5;
  const meta = estagiario.configuracao?.meta_horas_diaria ?? 6;

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Simulador de cenários</h1>
          <p>Veja o efeito de faltas e atrasos no seu saldo antes de acontecerem. Nada é gravado.</p>
        </div>
      </div>

      <div className="grade grade-principal">
        <section className="cartao entra" style={{ "--i": 1 }}>
          <div className="cartao-cabeca">
            <h2>Monte o cenário</h2>
          </div>
          <div className="cartao-corpo pilha" style={{ gap: 26 }}>
            <Deslizante
              icone={CalendarOff}
              rotulo="Dias de falta"
              valor={dias}
              maximo={15}
              passo={1}
              texto={plural(dias, "dia", "dias")}
              dica={`Cada falta desconta a meta de um dia inteiro (${formatarHoras(meta, 0)}).`}
              aoMudar={setDias}
            />
            <Deslizante
              icone={Clock3}
              rotulo="Horas de atraso"
              valor={horas}
              maximo={20}
              passo={0.5}
              texto={formatarHoras(horas)}
              dica="Cada hora de atraso desconta uma hora do saldo."
              aoMudar={setHoras}
            />
            <div>
              <div className="rotulo" style={{ marginBottom: 10 }}><Zap size={15} />Cenários rápidos</div>
              <div className="fichas">
                {ATALHOS.map((a) => (
                  <button key={a.rotulo} type="button" className="ficha" onClick={() => { setDias(a.dias); setHoras(a.horas); }}>
                    {a.rotulo}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="cartao entra" style={{ "--i": 2 }}>
          <div className="cartao-cabeca">
            <h2>Resultado</h2>
            <span className="sub">atualiza enquanto você mexe</span>
          </div>
          <div className="cartao-corpo">
            {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
            {resultado && <Resultado resultado={resultado} limite={limite} />}
          </div>
        </section>
      </div>
    </>
  );
}

function Deslizante({ icone: Icone, rotulo, valor, maximo, passo, texto, dica, aoMudar }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
        <span className="rotulo"><Icone size={15} />{rotulo}</span>
        <b className="numero" style={{ fontSize: 20 }}>{texto}</b>
      </div>
      <input
        type="range" min={0} max={maximo} step={passo} value={valor}
        style={{ "--preenchido": `${(valor / maximo) * 100}%` }}
        onChange={(e) => aoMudar(Number(e.target.value))}
        aria-label={rotulo}
      />
      <div className="texto-3" style={{ fontSize: 12.5, marginTop: 8 }}>{dica}</div>
    </div>
  );
}

function Resultado({ resultado, limite }) {
  const { saldo_atual: atual, saldo_projetado: projetado, impacto_horas: impacto } = resultado;
  const abaixoDoLimite = projetado <= limite;

  // Regua: do menor ao maior entre atual, projetado e limite, com folga.
  const minimo = Math.min(atual, projetado, limite) - 2;
  const maximo = Math.max(atual, projetado, 0) + 2;
  const posicao = (v) => `${((v - minimo) / (maximo - minimo)) * 100}%`;

  return (
    <div className="pilha" style={{ gap: 20 }}>
      <div className="comparacao">
        <div>
          <span>Saldo hoje</span>
          <b className={atual >= 0 ? "credito" : "alerta"}>{formatarSaldo(atual, 2)}</b>
        </div>
        <div className="comparacao-seta">
          <span className="selo selo--alerta">{formatarSaldo(impacto, 2)}</span>
          <ArrowRight />
        </div>
        <div>
          <span>Depois do cenário</span>
          <b className={projetado >= 0 ? "credito" : abaixoDoLimite ? "alerta" : "atencao"}>{formatarSaldo(projetado, 2)}</b>
        </div>
      </div>

      <div className="regua" aria-hidden="true">
        <div className="regua-faixa" />
        <div className="regua-zona" style={{ left: 0, width: posicao(limite) }} />
        <div className="regua-marca regua-marca--limite" style={{ left: posicao(limite) }}><span>alerta {formatarSaldo(limite, 0)}</span></div>
        <div className="regua-marca regua-marca--zero" style={{ left: posicao(0) }}><span>0h</span></div>
        <div className="regua-ponto regua-ponto--atual" style={{ left: posicao(atual) }} title="Saldo hoje" />
        <div className="regua-ponto regua-ponto--projetado" style={{ left: posicao(projetado) }} title="Depois do cenário" />
      </div>

      {impacto === 0 ? (
        <div className="aviso"><CircleCheck />Mexa nos controles ao lado para ver o efeito no saldo.</div>
      ) : abaixoDoLimite ? (
        <div className="aviso aviso--alerta">
          <CircleAlert />
          <div><strong>Esse cenário dispara o alerta.</strong> O saldo ficaria em {formatarSaldo(projetado, 2)}, abaixo do limite de {formatarSaldo(limite, 0)}.</div>
        </div>
      ) : projetado < 0 ? (
        <div className="aviso aviso--atencao">
          <CircleAlert />
          <div><strong>Saldo negativo, mas dentro do limite.</strong> Faltariam {formatarHoras(Math.abs(projetado), 2)} para compensar.</div>
        </div>
      ) : (
        <div className="aviso aviso--credito">
          <CircleCheck />
          <div><strong>O banco de horas aguenta.</strong> Mesmo com o cenário, o saldo continua positivo.</div>
        </div>
      )}
    </div>
  );
}
