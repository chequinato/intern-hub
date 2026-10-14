import { useState } from "react";
import { ArrowRight, Clock3, FileDown, History, LoaderCircle, Search } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { Avatar, Esqueleto, Indicador, Numero, SeloStatus, Vazio } from "../../components/Ui";
import { formatarData, formatarDataHora, hora, NOMES_CAMPOS } from "../../utils/formato";

const FILTROS = [
  { valor: "todos", rotulo: "Todos" },
  { valor: "pendente", rotulo: "Pendentes" },
  { valor: "aprovado", rotulo: "Aprovados" },
  { valor: "rejeitado", rotulo: "Rejeitados" },
];

// Auditoria (funcionalidade 17): todo pedido de ajuste ja feito, com quem
// pediu, quem decidiu e quando. A mesma tabela de solicitacoes serve de
// historico - nada e apagado quando o gestor responde.
export function Auditoria() {
  const notificar = useNotificar();
  const historico = useApiState(() => api.get("/solicitacoes"), []);
  const [filtro, setFiltro] = useState("todos");
  const [busca, setBusca] = useState("");
  const [baixando, setBaixando] = useState(null);

  const todos = historico.dados || [];
  const contagem = (status) => todos.filter((p) => p.status === status).length;
  const respondidos = contagem("aprovado") + contagem("rejeitado");
  const taxa = respondidos ? (contagem("aprovado") / respondidos) * 100 : 0;

  const lista = todos
    .filter((p) => filtro === "todos" || p.status === filtro)
    .filter((p) => p.estagiario_nome.toLowerCase().includes(busca.trim().toLowerCase()));

  async function baixar(p) {
    setBaixando(p.id);
    try {
      const blob = await api.baixarArquivo(`/solicitacoes/${p.id}/pdf`);
      const url = URL.createObjectURL(blob);
      const link = Object.assign(document.createElement("a"), { href: url, download: `comprovante_pedido_${p.id}.pdf` });
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      notificar.erro("Não foi possível gerar o comprovante", e.message);
    } finally {
      setBaixando(null);
    }
  }

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Histórico de pedidos</h1>
          <p>Todo ajuste pedido, com quem decidiu e quando. Nada é apagado.</p>
        </div>
      </div>

      <div className="cartao faixa entra">
        <Indicador rotulo="Pedidos no total"><Numero valor={todos.length} /></Indicador>
        <Indicador rotulo="Aprovados"><Numero valor={contagem("aprovado")} /></Indicador>
        <Indicador rotulo="Rejeitados"><Numero valor={contagem("rejeitado")} /></Indicador>
        <Indicador rotulo="Taxa de aprovação" rodape={`${contagem("pendente")} ainda pendente(s)`}>
          <Numero valor={taxa} /><small>%</small>
        </Indicador>
      </div>

      <div className="espaco" />

      <section className="cartao entra" style={{ "--i": 5 }}>
        <div className="cartao-cabeca" style={{ flexWrap: "wrap" }}>
          <div className="segmentado">
            {FILTROS.map((f) => (
              <button key={f.valor} type="button" className={filtro === f.valor ? "ativo" : ""} onClick={() => setFiltro(f.valor)}>
                {f.rotulo}
              </button>
            ))}
          </div>
          <div className="campo--com-icone" style={{ width: 260, maxWidth: "100%" }}>
            <Search />
            <input className="entrada" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar estagiário" aria-label="Buscar estagiário" />
          </div>
        </div>

        {historico.carregando && !historico.dados ? (
          <div className="cartao-corpo pilha">{[0, 1, 2, 3].map((n) => <Esqueleto key={n} altura={40} />)}</div>
        ) : lista.length === 0 ? (
          <Vazio icone={History} titulo="Nada encontrado">Mude o filtro ou a busca.</Vazio>
        ) : (
          <div className="tabela-moldura">
            <table className="tabela">
              <thead>
                <tr>
                  <th>Estagiário</th>
                  <th>Dia</th>
                  <th>Ajuste</th>
                  <th>Pedido</th>
                  <th>Decisão</th>
                  <th>Status</th>
                  <th className="direita">Comprovante</th>
                </tr>
              </thead>
              <tbody>
                {lista.map((p, i) => (
                  <tr key={p.id} style={{ "--i": i }}>
                    <td>
                      <span style={{ display: "flex", alignItems: "center", gap: 9 }}>
                        <Avatar nome={p.estagiario_nome} tamanho={28} />
                        <span style={{ fontWeight: 600 }}>{p.estagiario_nome}</span>
                      </span>
                    </td>
                    <td>{formatarData(p.data_registro)}</td>
                    <td>
                      <div style={{ fontWeight: 560 }}>{NOMES_CAMPOS[p.campo_alterado]}</div>
                      <div className="texto-3 mono" style={{ fontSize: 12.5, display: "flex", alignItems: "center", gap: 5 }}>
                        {p.status === "aprovado" ? "aplicado" : hora(p.horario_atual)} <ArrowRight size={12} /> {hora(p.horario_sugerido)}
                      </div>
                    </td>
                    <td className="texto-2" style={{ fontSize: 13 }}>{formatarDataHora(p.data_solicitacao)}</td>
                    <td className="texto-2" style={{ fontSize: 13 }}>
                      {p.data_resposta ? <>{p.gestor_nome}<div className="texto-3">{formatarDataHora(p.data_resposta)}</div></> : <span className="texto-3"><Clock3 size={13} style={{ display: "inline", verticalAlign: "-2px" }} /> aguardando</span>}
                    </td>
                    <td><SeloStatus status={p.status} /></td>
                    <td className="direita">
                      <button type="button" className="botao botao--fantasma botao--pequeno" onClick={() => baixar(p)} disabled={baixando === p.id}>
                        {baixando === p.id ? <LoaderCircle className="girando" /> : <FileDown />}PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
