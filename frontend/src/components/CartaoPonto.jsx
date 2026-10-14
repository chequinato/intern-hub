import { useState } from "react";
import { Check, Coffee, LoaderCircle, LogIn, LogOut, Utensils } from "lucide-react";
import { api } from "../api/cliente";
import { useAgora } from "../useAgora";
import { useNotificar } from "./Notificacoes";
import { ACAO_DO_PONTO, hora, horasEMinutos, NOMES_CAMPOS } from "../utils/formato";

const ETAPAS = [
  { campo: "entrada", rotulo: "Entrada", icone: LogIn },
  { campo: "saida_almoco", rotulo: "Almoço", icone: Utensils },
  { campo: "retorno_almoco", rotulo: "Retorno", icone: Coffee },
  { campo: "saida", rotulo: "Saída", icone: LogOut },
];

const MARCADO = {
  entrada: "Entrada registrada",
  saida_almoco: "Saída para o almoço registrada",
  retorno_almoco: "Retorno do almoço registrado",
  saida: "Saída registrada",
};

function emMinutos(texto) {
  if (!texto) return null;
  const [h, m] = texto.split(":").map(Number);
  return h * 60 + m;
}

// Quanto tempo ja foi trabalhado hoje, contando ate agora se o dia esta
// aberto. Almoco em andamento nao conta; almoco ja feito e descontado.
function trabalhadoAteAgora(registro, agora) {
  if (!registro) return 0;
  const agoraMin = agora.getHours() * 60 + agora.getMinutes();
  const fim = emMinutos(registro.saida) ?? (registro.saida_almoco && !registro.retorno_almoco ? emMinutos(registro.saida_almoco) : agoraMin);
  let total = fim - emMinutos(registro.entrada);
  if (registro.saida_almoco && registro.retorno_almoco) {
    total -= emMinutos(registro.retorno_almoco) - emMinutos(registro.saida_almoco);
  }
  return Math.max(0, total) / 60;
}

// Cartao "Ponto de hoje": relogio, linha do tempo das quatro marcacoes e o
// botao que bate o ponto (POST /ponto/{id}). Depois de marcar, chama
// aoMarcar() para a tela recarregar o painel.
export function CartaoPonto({ estagiarioId, registroHoje, proxima, horasDoDia, aoMarcar, i = 0 }) {
  const agora = useAgora(1000);
  const notificar = useNotificar();
  const [enviando, setEnviando] = useState(null);

  async function marcar(marcacao) {
    setEnviando(marcacao || proxima);
    try {
      const resposta = await api.post(`/ponto/${estagiarioId}`, marcacao ? { marcacao } : undefined);
      const horario = hora(resposta.registro[resposta.campo_marcado]);
      notificar.sucesso(
        `${MARCADO[resposta.campo_marcado]} às ${horario}`,
        resposta.proxima_marcacao ? `Próxima marcação: ${NOMES_CAMPOS[resposta.proxima_marcacao].toLowerCase()}.` : `Dia encerrado com ${horasEMinutos(resposta.registro.horas_trabalhadas)} trabalhadas.`);
      if (resposta.registro.aviso_limite_legal) notificar.info("Limite legal", resposta.registro.aviso_limite_legal);
      if (resposta.registro.pendencia) notificar.info("Dia com pendência", "O almoço ficou sem marcação. Abra um pedido de ajuste para o dia entrar no saldo.");
      aoMarcar?.();
    } catch (erro) {
      notificar.erro("Não foi possível bater o ponto", erro.message);
    } finally {
      setEnviando(null);
    }
  }

  const relogio = agora.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const trabalhado = registroHoje ? trabalhadoAteAgora(registroHoje, agora) : 0;
  const diaFechado = registroHoje && !proxima;
  const emAlmoco = registroHoje?.saida_almoco && !registroHoje?.retorno_almoco && !registroHoje?.saida;
  const indiceProxima = ETAPAS.findIndex((e) => e.campo === proxima);

  return (
    <section className="cartao cartao-ponto entra" style={{ "--i": i }}>
      <div className="cartao-cabeca">
        <h2>Ponto de hoje</h2>
        {diaFechado ? (
          <span className="selo selo--credito"><Check />Dia encerrado</span>
        ) : emAlmoco ? (
          <span className="selo selo--atencao"><span className="ponto ponto--vivo" />No almoço</span>
        ) : registroHoje ? (
          <span className="selo selo--marca"><span className="ponto ponto--vivo" />Trabalhando</span>
        ) : (
          <span className="selo">Ainda sem ponto</span>
        )}
      </div>

      <div className="cartao-corpo">
        <div className="ponto-topo">
          <div>
            <div className="ponto-relogio mono">{relogio}</div>
            <div className="ponto-legenda">
              {registroHoje
                ? <>Trabalhado hoje: <b>{horasEMinutos(diaFechado ? horasDoDia : trabalhado)}</b></>
                : "Nenhuma marcação registrada hoje"}
            </div>
          </div>
          {!diaFechado && (
            <div className="ponto-acoes">
              <button
                type="button"
                className="botao botao--primario botao--grande botao-ponto"
                onClick={() => marcar(null)}
                disabled={Boolean(enviando)}
              >
                {enviando && enviando === proxima ? <LoaderCircle className="girando" /> : <Fingerprint />}
                {ACAO_DO_PONTO[proxima]}
              </button>
              {proxima === "saida_almoco" && (
                <button type="button" className="botao botao--fantasma botao--pequeno" onClick={() => marcar("saida")} disabled={Boolean(enviando)}>
                  Encerrar o dia sem almoço
                </button>
              )}
            </div>
          )}
        </div>

        <ol className="linha-ponto">
          {ETAPAS.map((etapa, indice) => {
            const valor = registroHoje?.[etapa.campo];
            const pulada = diaFechado && !valor;
            const estado = valor ? "feita" : indice === indiceProxima ? "proxima" : pulada ? "pulada" : "futura";
            const Icone = valor ? Check : etapa.icone;
            return (
              <li key={etapa.campo} className={`etapa etapa--${estado}`}>
                <span className="etapa-marcador"><Icone /></span>
                <span className="etapa-rotulo">{etapa.rotulo}</span>
                <span className="etapa-hora mono">{valor ? hora(valor) : pulada ? "não marcado" : "—"}</span>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}

// Icone de "digital" desenhado a mao (o gesto de bater ponto).
function Fingerprint() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4" />
      <path d="M14 13.12c0 2.38 0 6.38-1 8.88" />
      <path d="M17.29 21.02c.12-.6.43-2.3.5-3.02" />
      <path d="M2 12a10 10 0 0 1 18-6" />
      <path d="M2 16h.01" />
      <path d="M21.8 16c.2-2 .131-5.354 0-6" />
      <path d="M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2" />
      <path d="M8.65 22c.21-.66.45-1.32.57-2" />
      <path d="M9 6.8a6 6 0 0 1 9 5.2v2" />
    </svg>
  );
}
