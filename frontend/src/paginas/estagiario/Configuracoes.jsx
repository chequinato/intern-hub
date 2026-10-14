import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { CircleAlert, LoaderCircle, Save } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { Avatar } from "../../components/Ui";

// Meta e limites do estagiario (Entrega 3 - antes so dava para definir a
// meta no cadastro). Salva com PATCH /estagiarios/{id}/configuracao; o
// gestor responsavel usa a rota PATCH /estagiarios/{id} que ja existia.
export function Configuracoes() {
  const { estagiario, estagiarioId, recarregar } = useOutletContext();
  const notificar = useNotificar();
  const gestores = useApiState(() => api.get("/gestores"), []);
  const c = estagiario.configuracao || {};

  const [form, setForm] = useState({
    meta_horas_diaria: c.meta_horas_diaria ?? 6,
    meta_horas_semanal: c.meta_horas_semanal ?? 30,
    limite_alerta_negativo: c.limite_alerta_negativo ?? -5,
    prazo_vencimento_meses: c.prazo_vencimento_meses ?? 2,
    limite_maximo_diario: c.limite_maximo_diario ?? 6,
    limite_maximo_semanal: c.limite_maximo_semanal ?? 30,
  });
  const [gestorId, setGestorId] = useState(estagiario.gestor_id ?? "");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState(null);

  const mudar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));
  const metaAcimaDoLimite = Number(form.meta_horas_diaria) > Number(form.limite_maximo_diario);

  async function salvar(e) {
    e.preventDefault();
    setSalvando(true);
    setErro(null);
    try {
      const numeros = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, Number(v)]));
      await api.patch(`/estagiarios/${estagiarioId}/configuracao`, numeros);
      if (String(gestorId) !== String(estagiario.gestor_id ?? "")) {
        await api.patch(`/estagiarios/${estagiarioId}`, { gestor_id: gestorId ? Number(gestorId) : null });
      }
      notificar.sucesso("Configurações salvas", "O saldo já foi recalculado com a nova meta.");
      recarregar();
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <form onSubmit={salvar}>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Meta e limites</h1>
          <p>A meta é o que você deve cumprir; o limite legal é o que você não pode passar.</p>
        </div>
        <div className="acoes">
          <button type="submit" className="botao botao--primario" disabled={salvando}>
            {salvando ? <LoaderCircle className="girando" /> : <Save />}
            {salvando ? "Salvando…" : "Salvar alterações"}
          </button>
        </div>
      </div>

      {erro && <div className="aviso aviso--alerta" style={{ marginBottom: 16 }}><CircleAlert />{erro}</div>}

      <div className="grade grade-2">
        <section className="cartao entra" style={{ "--i": 1 }}>
          <div className="cartao-cabeca"><h2>Meta contratada</h2></div>
          <div className="cartao-corpo pilha" style={{ gap: 16 }}>
            <div className="grade-campos">
              <Campo id="meta-dia" rotulo="Meta por dia (h)" valor={form.meta_horas_diaria} aoMudar={mudar("meta_horas_diaria")} passo="0.5" min="0.5" max="24" />
              <Campo id="meta-semana" rotulo="Meta por semana (h)" valor={form.meta_horas_semanal} aoMudar={mudar("meta_horas_semanal")} passo="1" min="1" max="168" />
            </div>
            <p className="texto-3" style={{ fontSize: 13 }}>Cada dia completo soma ao saldo o que passar da meta diária, ou desconta o que faltar.</p>
            {metaAcimaDoLimite && (
              <div className="aviso aviso--atencao"><CircleAlert />A meta diária está acima do limite legal por dia: todo dia cumprido vai gerar aviso.</div>
            )}
          </div>
        </section>

        <section className="cartao entra" style={{ "--i": 2 }}>
          <div className="cartao-cabeca"><h2>Limite legal</h2><span className="sub">Lei 11.788/2008</span></div>
          <div className="cartao-corpo pilha" style={{ gap: 16 }}>
            <div className="grade-campos">
              <Campo id="lim-dia" rotulo="Máximo por dia (h)" valor={form.limite_maximo_diario} aoMudar={mudar("limite_maximo_diario")} passo="0.5" min="1" max="24" />
              <Campo id="lim-semana" rotulo="Máximo por semana (h)" valor={form.limite_maximo_semanal} aoMudar={mudar("limite_maximo_semanal")} passo="1" min="1" max="168" />
            </div>
            <p className="texto-3" style={{ fontSize: 13 }}>O padrão é 6h por dia e 30h por semana. Em períodos sem aula a lei permite até 8h e 40h.</p>
          </div>
        </section>

        <section className="cartao entra" style={{ "--i": 3 }}>
          <div className="cartao-cabeca"><h2>Alertas do banco de horas</h2></div>
          <div className="cartao-corpo pilha" style={{ gap: 16 }}>
            <div className="grade-campos">
              <Campo id="alerta" rotulo="Alerta de saldo negativo (h)" valor={form.limite_alerta_negativo} aoMudar={mudar("limite_alerta_negativo")} passo="0.5" max="0" />
              <Campo id="vencimento" rotulo="Crédito vence em (meses)" valor={form.prazo_vencimento_meses} aoMudar={mudar("prazo_vencimento_meses")} passo="1" min="1" max="24" />
            </div>
            <p className="texto-3" style={{ fontSize: 13 }}>O alerta aparece quando o saldo chega ao valor acima. O crédito antigo avisa antes de vencer.</p>
          </div>
        </section>

        <section className="cartao entra" style={{ "--i": 4 }}>
          <div className="cartao-cabeca"><h2>Gestor responsável</h2></div>
          <div className="cartao-corpo pilha" style={{ gap: 14 }}>
            <div className="campo">
              <label htmlFor="gestor">Quem aprova seus pedidos de ajuste</label>
              <select id="gestor" value={gestorId} onChange={(e) => setGestorId(e.target.value)}>
                <option value="">Sem gestor</option>
                {(gestores.dados || []).map((g) => <option key={g.id} value={g.id}>{g.nome}</option>)}
              </select>
            </div>
            {gestorId && gestores.dados && (
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Avatar nome={gestores.dados.find((g) => String(g.id) === String(gestorId))?.nome || ""} tamanho={30} />
                <span className="texto-2" style={{ fontSize: 13 }}>Seus pedidos aparecem na fila de aprovação dessa pessoa.</span>
              </div>
            )}
          </div>
        </section>
      </div>
    </form>
  );
}

function Campo({ id, rotulo, valor, aoMudar, passo, min, max }) {
  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <input id={id} type="number" step={passo} min={min} max={max} value={valor} onChange={aoMudar} required />
    </div>
  );
}
