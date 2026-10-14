import { Link, useNavigate, useOutletContext } from "react-router-dom";
import { ArrowRight, CalendarRange, CircleAlert, Info, TriangleAlert } from "lucide-react";
import { acentuar } from "../../api/cliente";
import { CartaoPonto } from "../../components/CartaoPonto";
import { GraficoTendencia, GraficoUltimosDias } from "../../components/Graficos";
import { AnelProgresso, CarregandoPagina, ErroCarregar, Indicador, Numero } from "../../components/Ui";
import {
  diaDaSemana, formatarData, formatarDataCurta, formatarHoras, formatarSaldo, horasEMinutos,
  NOMES_CAMPOS, primeiroNome, saudacao,
} from "../../utils/formato";

// Painel inicial do estagiario (Entrega 3): tudo que o sistema calcula,
// visivel numa tela so - saldo, semana em relacao ao limite legal, ponto
// de hoje, pendencias, pedidos e a tendencia dos ultimos meses.
export function Inicio() {
  const { estagiarioId, painel, painelErro, recarregar } = useOutletContext();
  const navegar = useNavigate();

  if (painelErro) return <ErroCarregar mensagem={painelErro} aoTentar={recarregar} />;
  if (!painel) return <CarregandoPagina />;

  const saldo = painel.saldo_acumulado;
  const fracaoSemana = painel.horas_semana / painel.limite_maximo_semanal;
  const tomSemana = fracaoSemana > 1 ? "alerta" : fracaoSemana >= 0.85 ? "atencao" : "marca";
  const pendenciasSemPedido = painel.pendencias.filter((p) => !p.pedido_aberto);

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>{saudacao()}, {primeiroNome(painel.nome)}</h1>
          <p>{resumoEmTexto(painel)}</p>
        </div>
        <div className="acoes">
          <Link className="botao" to="relatorio"><CalendarRange />Relatório do mês</Link>
        </div>
      </div>

      <div className="pilha" style={{ marginBottom: 16 }}>
        {painel.em_alerta && (
          <div className="aviso aviso--alerta entra">
            <CircleAlert />
            <div>
              <strong>Saldo abaixo do limite de alerta.</strong> Você está com {formatarSaldo(saldo)} e o limite é{" "}
              {formatarSaldo(painel.limite_alerta)}. Combine com seu gestor como compensar as horas.
            </div>
          </div>
        )}
        {pendenciasSemPedido.length > 0 && (
          <div className="aviso aviso--atencao entra">
            <TriangleAlert />
            <div>
              <strong>{pendenciasSemPedido.length === 1 ? "Um dia" : `${pendenciasSemPedido.length} dias`} sem a marcação do almoço.</strong>{" "}
              Enquanto não for corrigido, o dia fica fora do saldo.
            </div>
            <div className="acoes">
              <button
                type="button"
                className="botao botao--pequeno"
                onClick={() => navegar(`solicitacoes?registro=${pendenciasSemPedido[0].registro_id}&campo=${pendenciasSemPedido[0].campos_faltando.at(-1)}`)}
              >
                Pedir ajuste <ArrowRight />
              </button>
            </div>
          </div>
        )}
        {painel.aviso_vencimento && (
          <div className="aviso entra"><Info /><div>{acentuar(painel.aviso_vencimento)}</div></div>
        )}
      </div>

      <div className="cartao faixa entra">
        <Indicador
          destaque
          rotulo="Saldo do banco de horas"
          rodape={saldo >= 0 ? "Crédito acumulado" : `Alerta em ${formatarSaldo(painel.limite_alerta)}`}
        >
          <span className={saldo >= 0 ? "credito" : painel.em_alerta ? "alerta" : "atencao"}>
            <Numero valor={saldo} formato="saldo" />
          </span>
        </Indicador>
        <Indicador rotulo="Horas nesta semana"
          rodape={`de ${formatarHoras(painel.limite_maximo_semanal, 0)} do limite legal`}>
          <Numero valor={painel.horas_semana} formato="horas" />
        </Indicador>
        <Indicador rotulo="Dias com pendência"
          rodape={painel.pendencias.length ? "Fora do saldo até corrigir" : "Tudo em dia"}>
          <Numero valor={painel.pendencias.length} />
        </Indicador>
        <Indicador rotulo="Pedidos aguardando"
          rodape={painel.pedidos_pendentes ? "Na fila do gestor" : "Nenhum pedido aberto"}>
          <Numero valor={painel.pedidos_pendentes} />
        </Indicador>
      </div>

      <div className="espaco" />

      <div className="grade grade-principal">
        <CartaoPonto
          i={5}
          estagiarioId={estagiarioId}
          registroHoje={painel.registro_hoje}
          proxima={painel.proxima_marcacao}
          horasDoDia={painel.horas_hoje}
          aoMarcar={recarregar}
        />

        <section className="cartao entra" style={{ "--i": 6 }}>
          <div className="cartao-cabeca">
            <h2>Semana e limite legal</h2>
            <span className="sub">Lei 11.788/2008</span>
          </div>
          <div className="cartao-corpo semana">
            <AnelProgresso fracao={fracaoSemana} tom={tomSemana}>
              <div>
                <div className="anel-valor numero">{formatarHoras(painel.horas_semana)}</div>
                <div className="anel-legenda">de {formatarHoras(painel.limite_maximo_semanal, 0)}</div>
              </div>
            </AnelProgresso>
            <ul className="lista-regras">
              <li><span>Meta semanal</span><b>{formatarHoras(painel.meta_horas_semanal, 0)}</b></li>
              <li><span>Limite por dia</span><b>{formatarHoras(painel.limite_maximo_diario, 0)}</b></li>
              <li>
                <span>{fracaoSemana > 1 ? "Acima do limite" : "Até o limite"}</span>
                <b className={fracaoSemana > 1 ? "alerta" : ""}>
                  {horasEMinutos(Math.abs(painel.limite_maximo_semanal - painel.horas_semana))}
                </b>
              </li>
            </ul>
          </div>
        </section>
      </div>

      <div className="espaco" />

      <div className="grade grade-principal">
        <section className="cartao entra" style={{ "--i": 7 }}>
          <div className="cartao-cabeca">
            <h2>Tendência do saldo</h2>
            <span className="sub">saldo de cada mês e acumulado</span>
          </div>
          <div className="cartao-corpo">
            <GraficoTendencia tendencia={painel.tendencia} />
          </div>
        </section>

        <section className="cartao entra" style={{ "--i": 8 }}>
          <div className="cartao-cabeca">
            <h2>Últimos dias</h2>
            <span className="sub">meta de {formatarHoras(painel.meta_horas_diaria, 0)} por dia</span>
          </div>
          <div className="cartao-corpo">
            <GraficoUltimosDias dias={painel.ultimos_dias} meta={painel.meta_horas_diaria} limite={painel.limite_maximo_diario} />
          </div>
        </section>
      </div>

      {painel.pendencias.length > 0 && (
        <>
          <div className="espaco" />
          <section className="cartao entra" style={{ "--i": 9 }}>
            <div className="cartao-cabeca">
              <h2>Dias com pendência</h2>
              <span className="sub">o almoço ficou sem marcação</span>
            </div>
            <ul className="lista-pendencias">
              {painel.pendencias.map((p) => (
                <li key={p.registro_id}>
                  <div className="data-bloco">
                    <span>{diaDaSemana(p.data)}</span>
                    <b>{formatarDataCurta(p.data)}</b>
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600 }}>{formatarData(p.data)}</div>
                    <div className="texto-3" style={{ fontSize: 13 }}>
                      Falta: {p.campos_faltando.map((c) => NOMES_CAMPOS[c].toLowerCase()).join(" e ")}
                    </div>
                  </div>
                  {p.pedido_aberto ? (
                    <span className="selo selo--info">Pedido enviado</span>
                  ) : (
                    <Link className="botao botao--pequeno" to={`solicitacoes?registro=${p.registro_id}&campo=${p.campos_faltando.at(-1)}`}>
                      Pedir ajuste <ArrowRight />
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </>
  );
}

// Uma frase com a situacao da pessoa hoje, montada com os numeros do
// painel - no lugar de um subtitulo generico que serviria para qualquer um.
function resumoEmTexto(painel) {
  const saldo = painel.saldo_acumulado;
  const partes = [
    saldo >= 0
      ? `Você tem ${formatarHoras(saldo)} de crédito no banco de horas`
      : `Você está devendo ${formatarHoras(Math.abs(saldo))} ao banco de horas`,
    `${formatarHoras(painel.horas_semana)} trabalhadas nesta semana`,
  ];
  const pendentes = painel.pendencias.filter((p) => !p.pedido_aberto).length;
  const fim = pendentes
    ? ` ${pendentes === 1 ? "Um dia precisa" : `${pendentes} dias precisam`} de ajuste.`
    : painel.pedidos_pendentes ? " Seu pedido de ajuste está com o gestor." : "";
  return `${partes.join(" e ")}.${fim}`;
}
