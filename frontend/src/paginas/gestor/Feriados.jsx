import { useState } from "react";
import { CalendarX2, LoaderCircle, Plus, Trash2, TriangleAlert } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { Esqueleto, Vazio } from "../../components/Ui";
import { diaDaSemana, formatarData, formatarDataCurta, hojeIso, MESES, paraData } from "../../utils/formato";

// Feriados nacionais fixos e moveis de 2026 e 2027, para cadastrar com um clique.
const NACIONAIS = [
  ["2026-11-02", "Finados"], ["2026-11-15", "Proclamação da República"], ["2026-11-20", "Dia da Consciência Negra"],
  ["2026-12-25", "Natal"], ["2027-01-01", "Confraternização Universal"], ["2027-02-08", "Carnaval"],
  ["2027-02-09", "Carnaval"], ["2027-03-26", "Sexta-feira Santa"], ["2027-04-21", "Tiradentes"],
  ["2027-05-01", "Dia do Trabalho"], ["2027-05-27", "Corpus Christi"],
];

// Calendario de feriados (funcionalidade 15 do refinamento): a API ja
// cadastrava e listava, mas so dava para usar pela pagina /docs. Dia
// cadastrado aqui nao conta como falta no relatorio de ninguem.
export function Feriados() {
  const notificar = useNotificar();
  const feriados = useApiState(() => api.get("/feriados"), []);
  const [data, setData] = useState("");
  const [descricao, setDescricao] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [removendo, setRemovendo] = useState(null);
  const [erro, setErro] = useState(null);

  async function cadastrar(dataFeriado, nome) {
    setEnviando(true);
    setErro(null);
    try {
      await api.post("/feriados", { data: dataFeriado, descricao: nome });
      notificar.sucesso("Feriado cadastrado", `${nome} · ${formatarData(dataFeriado)}`);
      setData("");
      setDescricao("");
      feriados.recarregar();
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  async function remover(feriado) {
    setRemovendo(feriado.id);
    try {
      await api.delete(`/feriados/${feriado.id}`);
      notificar.info("Feriado removido", `${feriado.descricao} volta a ser dia útil.`);
      feriados.setDados((lista) => lista.filter((f) => f.id !== feriado.id));
    } catch (e) {
      notificar.erro("Não foi possível remover", e.message);
    } finally {
      setRemovendo(null);
    }
  }

  const lista = feriados.dados || [];
  const cadastrados = new Set(lista.map((f) => f.data));
  const sugestoes = NACIONAIS.filter(([d]) => d >= hojeIso() && !cadastrados.has(d)).slice(0, 6);
  const hoje = hojeIso();
  const proximos = lista.filter((f) => f.data >= hoje);
  const passados = lista.filter((f) => f.data < hoje).reverse();

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Calendário de feriados</h1>
          <p>Dias cadastrados aqui não cobram ponto e não contam como falta para ninguém.</p>
        </div>
      </div>

      <div className="grade grade-principal">
        <section className="cartao entra" style={{ "--i": 2 }}>
          <div className="cartao-cabeca">
            <h2>Feriados cadastrados</h2>
            <span className="sub">{lista.length} no total</span>
          </div>
          {feriados.carregando && !feriados.dados ? (
            <div className="cartao-corpo pilha">{[0, 1, 2].map((n) => <Esqueleto key={n} altura={52} />)}</div>
          ) : lista.length === 0 ? (
            <Vazio icone={CalendarX2} titulo="Nenhum feriado cadastrado">Use o formulário ao lado ou os atalhos dos feriados nacionais.</Vazio>
          ) : (
            <div className="cartao-corpo pilha" style={{ gap: 18 }}>
              {proximos.length > 0 && <ListaFeriados titulo="Próximos" itens={proximos} aoRemover={remover} removendo={removendo} />}
              {passados.length > 0 && <ListaFeriados titulo="Já passaram" itens={passados} aoRemover={remover} removendo={removendo} passados />}
            </div>
          )}
        </section>

        <div className="pilha">
          <form className="cartao entra" style={{ "--i": 1 }} onSubmit={(e) => { e.preventDefault(); cadastrar(data, descricao.trim()); }}>
            <div className="cartao-cabeca"><h2>Novo feriado</h2></div>
            <div className="cartao-corpo pilha" style={{ gap: 14 }}>
              <div className="campo">
                <label htmlFor="feriado-data">Data</label>
                <input id="feriado-data" type="date" value={data} onChange={(e) => setData(e.target.value)} required />
              </div>
              <div className="campo">
                <label htmlFor="feriado-nome">Descrição</label>
                <input id="feriado-nome" value={descricao} onChange={(e) => setDescricao(e.target.value)} minLength={2} maxLength={120}
                  placeholder="Aniversário da cidade" required />
              </div>
              {erro && <div className="aviso aviso--alerta"><TriangleAlert />{erro}</div>}
              <button type="submit" className="botao botao--primario" disabled={enviando}>
                {enviando ? <LoaderCircle className="girando" /> : <Plus />}Cadastrar
              </button>
            </div>
          </form>

          {sugestoes.length > 0 && (
            <section className="cartao entra" style={{ "--i": 3 }}>
              <div className="cartao-cabeca"><h2>Feriados nacionais</h2><span className="sub">um clique para cadastrar</span></div>
              <ul className="lista-sugestoes">
                {sugestoes.map(([d, nome]) => (
                  <li key={d}>
                    <div className="data-bloco"><span>{diaDaSemana(d)}</span><b>{formatarDataCurta(d)}</b></div>
                    <span style={{ flex: 1 }}>{nome}</span>
                    <button type="button" className="botao botao--pequeno" onClick={() => cadastrar(d, nome)} disabled={enviando}>
                      <Plus />Adicionar
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

function ListaFeriados({ titulo, itens, aoRemover, removendo, passados = false }) {
  const hoje = paraData(hojeIso());
  return (
    <div>
      <div className="divisor" style={{ marginBottom: 10 }}>{titulo}</div>
      <ul className="lista-feriados">
        {itens.map((f, i) => {
          const dias = Math.round((paraData(f.data) - hoje) / 86400000);
          return (
            <li key={f.id} className="entra" style={{ "--i": i }}>
              <div className={`data-bloco${passados ? " data-bloco--apagado" : ""}`}>
                <span>{MESES[paraData(f.data).getMonth()].slice(0, 3)}</span>
                <b>{paraData(f.data).getDate()}</b>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600 }}>{f.descricao}</div>
                <div className="texto-3" style={{ fontSize: 12.5 }}>
                  {diaDaSemana(f.data, false)}, {formatarData(f.data)}
                  {!passados && (dias === 0 ? " · hoje" : dias === 1 ? " · amanhã" : ` · em ${dias} dias`)}
                </div>
              </div>
              {diaDaSemana(f.data) === "sáb" || diaDaSemana(f.data) === "dom"
                ? <span className="selo">fim de semana</span>
                : null}
              <button type="button" className="botao botao--fantasma botao--icone" onClick={() => aoRemover(f)} disabled={removendo === f.id}
                aria-label={`Remover ${f.descricao}`} title="Remover">
                {removendo === f.id ? <LoaderCircle className="girando" /> : <Trash2 />}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
