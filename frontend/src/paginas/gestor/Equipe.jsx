import { Link, useOutletContext } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ArrowRight, ClipboardCheck, Users, Wallet } from "lucide-react";
import { DicaGrafico } from "../../components/DicaGrafico";
import { Avatar, Barra, CarregandoPagina, ErroCarregar, Indicador, Numero, Vazio } from "../../components/Ui";
import { formatarData, formatarHoras, formatarSaldo, primeiroNome, saudacao } from "../../utils/formato";

// Painel do gestor (Entrega 3): a equipe inteira numa tela - quem esta em
// alerta, quem passou do limite legal e quantos pedidos esperam decisao.
export function Equipe() {
  const { gestor, painel, painelErro, recarregar } = useOutletContext();

  if (painelErro) return <ErroCarregar mensagem={painelErro} aoTentar={recarregar} />;
  if (!painel) return <CarregandoPagina />;

  const maiorSaldo = Math.max(1, ...painel.equipe.map((l) => Math.abs(l.saldo_acumulado)));

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>{saudacao()}, {primeiroNome(gestor.nome)}</h1>
          <p>{resumoDaEquipe(painel)}</p>
        </div>
        {painel.pedidos_na_fila > 0 && (
          <div className="acoes">
            <Link className="botao botao--primario" to="aprovacoes">
              <ClipboardCheck />Revisar {painel.pedidos_na_fila} pedido(s)
            </Link>
          </div>
        )}
      </div>

      <div className="cartao faixa entra">
        <Indicador rotulo="Estagiários" rodape={`saldo médio ${formatarSaldo(painel.saldo_medio)}`}>
          <Numero valor={painel.total_estagiarios} />
        </Indicador>
        <Indicador rotulo="Em alerta de saldo"
          rodape={painel.em_alerta ? "abaixo do limite negativo" : "ninguém em alerta"}>
          <span className={painel.em_alerta ? "alerta" : ""}><Numero valor={painel.em_alerta} /></span>
        </Indicador>
        <Indicador rotulo="Acima do limite legal"
          rodape="nos últimos 7 dias">
          <span className={painel.acima_limite_legal ? "atencao" : ""}><Numero valor={painel.acima_limite_legal} /></span>
        </Indicador>
        <Indicador rotulo="Pedidos na fila" rodape={painel.pedidos_na_fila ? "esperando sua decisão" : "fila vazia"}>
          <Numero valor={painel.pedidos_na_fila} />
        </Indicador>
      </div>

      <div className="espaco" />

      <section className="cartao entra" style={{ "--i": 5 }}>
        <div className="cartao-cabeca">
          <h2>Equipe</h2>
          <span className="sub">saldo do banco de horas e horas da semana</span>
        </div>
        {painel.equipe.length === 0 ? (
          <Vazio icone={Users} titulo="Nenhum estagiário na equipe">
            O estagiário escolhe o gestor responsável no cadastro ou em Configurações.
          </Vazio>
        ) : (
          <div className="tabela-moldura">
            <table className="tabela">
              <thead>
                <tr>
                  <th>Estagiário</th>
                  <th>Saldo</th>
                  <th style={{ minWidth: 170 }}>Semana atual</th>
                  <th>Situação</th>
                  <th className="direita">Pedidos</th>
                </tr>
              </thead>
              <tbody>
                {painel.equipe.map((l, i) => (
                  <tr key={l.estagiario_id} style={{ "--i": i }}>
                    <td>
                      <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <Avatar nome={l.nome} tamanho={34} />
                        <span>
                          <span style={{ fontWeight: 620, display: "block" }}>{l.nome}</span>
                          <span className="texto-3" style={{ fontSize: 12.5 }}>
                            {l.ultimo_ponto ? `último ponto em ${formatarData(l.ultimo_ponto)}` : "sem ponto ainda"}
                          </span>
                        </span>
                      </span>
                    </td>
                    <td>
                      <div className={`numero ${l.saldo_acumulado >= 0 ? "credito" : l.em_alerta ? "alerta" : "atencao"}`} style={{ fontWeight: 680, fontSize: 15 }}>
                        {formatarSaldo(l.saldo_acumulado)}
                      </div>
                      <SaldoDivergente valor={l.saldo_acumulado} maximo={maiorSaldo} />
                    </td>
                    <td>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5, marginBottom: 6 }}>
                        <span className="numero" style={{ fontWeight: 600 }}>{formatarHoras(l.horas_semana)}</span>
                        <span className="texto-3">de {formatarHoras(l.limite_maximo_semanal, 0)}</span>
                      </div>
                      <Barra fracao={l.horas_semana / l.limite_maximo_semanal}
                        tom={l.acima_limite_semanal ? "alerta" : l.horas_semana / l.limite_maximo_semanal >= 0.85 ? "atencao" : ""} fina />
                    </td>
                    <td>
                      <span style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {l.em_alerta && <span className="selo selo--alerta">Saldo em alerta</span>}
                        {(l.acima_limite_semanal || l.dias_acima_limite_diario > 0) && (
                          <span className="selo selo--atencao">
                            {l.acima_limite_semanal ? "Semana acima de 30h" : `${l.dias_acima_limite_diario} dia(s) acima de 6h`}
                          </span>
                        )}
                        {l.pendencias > 0 && <span className="selo selo--info">{l.pendencias} pendência(s)</span>}
                        {!l.em_alerta && !l.acima_limite_semanal && !l.dias_acima_limite_diario && !l.pendencias && (
                          <span className="selo selo--credito">Em dia</span>
                        )}
                      </span>
                    </td>
                    <td className="direita">
                      {l.pedidos_pendentes > 0 ? (
                        <Link to="aprovacoes" className="selo selo--atencao" style={{ textDecoration: "none" }}>{l.pedidos_pendentes} na fila <ArrowRight size={12} /></Link>
                      ) : <span className="texto-3">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {painel.equipe.length > 0 && (
        <>
          <div className="espaco" />
          <section className="cartao entra" style={{ "--i": 6 }}>
            <div className="cartao-cabeca">
              <h2>Saldo por estagiário</h2>
              <span className="sub"><Wallet size={13} style={{ display: "inline", verticalAlign: "-2px" }} /> a linha vermelha é o limite de alerta</span>
            </div>
            <div className="cartao-corpo">
              <GraficoSaldos equipe={painel.equipe} />
            </div>
          </section>
        </>
      )}
    </>
  );
}

// Barrinha que cresce para a direita (credito) ou esquerda (debito) a
// partir do meio - o zero fica sempre no centro.
function SaldoDivergente({ valor, maximo }) {
  const pct = Math.min(1, Math.abs(valor) / maximo) * 50;
  return (
    <div className="divergente" aria-hidden="true">
      <span
        className={valor >= 0 ? "pos" : "neg"}
        style={valor >= 0 ? { left: "50%", width: `${pct}%` } : { right: "50%", width: `${pct}%` }}
      />
    </div>
  );
}

function GraficoSaldos({ equipe }) {
  const dados = equipe.map((l) => ({ ...l, rotulo: primeiroNome(l.nome) }));
  const limite = equipe[0]?.limite_alerta ?? -5;
  return (
    <div style={{ height: Math.max(180, dados.length * 56 + 40) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={dados} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
          <CartesianGrid stroke="var(--borda)" horizontal={false} />
          <XAxis type="number" tickLine={false} axisLine={false} tick={{ fill: "var(--texto-3)", fontSize: 12 }} tickFormatter={(v) => `${v}h`}
            allowDecimals={false}
            domain={[(min) => Math.floor(Math.min(min, limite - 1) / 2) * 2, (max) => Math.ceil(Math.max(max, 2) / 2) * 2]} />
          <YAxis type="category" dataKey="rotulo" tickLine={false} axisLine={false} width={80} tick={{ fill: "var(--texto-2)", fontSize: 13 }} />
          <ReferenceLine x={0} stroke="var(--borda-forte)" />
          <ReferenceLine x={limite} stroke="var(--alerta)" strokeDasharray="4 4" />
          <Tooltip
            cursor={{ fill: "var(--superficie-3)" }}
            content={<DicaGrafico titulo={(p) => p.nome} linhas={[
              { rotulo: "Saldo", valor: (p) => formatarSaldo(p.saldo_acumulado, 2) },
              { rotulo: "Semana", valor: (p) => formatarHoras(p.horas_semana) },
            ]} />}
          />
          <Bar dataKey="saldo_acumulado" radius={[4, 4, 4, 4]} barSize={22} animationDuration={900}>
            {dados.map((l) => <Cell key={l.estagiario_id} fill={l.em_alerta ? "var(--alerta)" : l.saldo_acumulado >= 0 ? "var(--marca-500)" : "var(--atencao-forte)"} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function resumoDaEquipe(painel) {
  if (!painel.total_estagiarios) return "Você ainda não tem estagiários vinculados.";
  const partes = [`${painel.total_estagiarios} estagiário(s) na equipe`];
  if (painel.em_alerta) partes.push(`${painel.em_alerta} em alerta de saldo`);
  if (painel.pedidos_na_fila) partes.push(`${painel.pedidos_na_fila} pedido(s) esperando você`);
  if (partes.length === 1) partes.push("ninguém em alerta e a fila está vazia");
  return partes.join(" · ") + ".";
}
