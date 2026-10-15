import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Briefcase, ChevronRight, CircleAlert, GraduationCap, LoaderCircle, Search, UserPlus, X } from "lucide-react";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { useSessao } from "../context/SessaoContext";
import { Logo } from "../components/Logo";
import { VitrinePainel } from "../components/VitrinePainel";
import { useNotificar } from "../components/Notificacoes";
import { Avatar, Esqueleto, Vazio } from "../components/Ui";

// Tela de entrada: escolher o perfil (estagiario ou gestor) e a pessoa, ou
// cadastrar alguem novo. Nao e login - nao ha senha por pessoa (decisao da
// Entrega 1); quem protege a API e o token, em api/seguranca.py.
export function Portal() {
  const [perfil, setPerfil] = useState("estagiario");
  const [cadastrando, setCadastrando] = useState(false);
  const [busca, setBusca] = useState("");
  const navegar = useNavigate();
  const { escolherEstagiario, escolherGestor } = useSessao();

  const estagiarios = useApiState(() => api.get("/estagiarios"));
  const gestores = useApiState(() => api.get("/gestores"));
  const atual = perfil === "estagiario" ? estagiarios : gestores;
  const pessoas = (atual.dados || []).filter((p) => p.nome.toLowerCase().includes(busca.trim().toLowerCase()));

  function entrar(pessoa) {
    if (perfil === "estagiario") {
      escolherEstagiario(pessoa.id);
      navegar(`/estagiario/${pessoa.id}`);
    } else {
      escolherGestor(pessoa.id);
      navegar(`/gestor/${pessoa.id}`);
    }
  }

  function trocarPerfil(novo) {
    setPerfil(novo);
    setCadastrando(false);
    setBusca("");
  }

  const equipeDe = (gestorId) => (estagiarios.dados || []).filter((e) => e.gestor_id === gestorId).length;

  return (
    <div className="portal">
      <main className="portal-acesso">
        <div className="portal-marca-topo">
          <Logo tamanho={34} />
          <span>InternHub<span className="laranja">.</span></span>
        </div>

        <div className="portal-caixa entra">
          <h1>Cada minuto<br />no lugar certo.</h1>
          <p>Ponto, saldo e ajustes do estágio, com a conta feita pelo sistema. Escolha o seu perfil para entrar.</p>

          <div className="segmentado segmentado--bloco" role="tablist">
            <button type="button" className={perfil === "estagiario" ? "ativo" : ""} onClick={() => trocarPerfil("estagiario")}>
              <GraduationCap />Sou estagiário
            </button>
            <button type="button" className={perfil === "gestor" ? "ativo" : ""} onClick={() => trocarPerfil("gestor")}>
              <Briefcase />Sou gestor
            </button>
          </div>

          {atual.erro ? (
            <div className="aviso aviso--alerta" style={{ marginTop: 20 }}>
              <CircleAlert />
              <div>
                <strong>Não foi possível falar com a API.</strong> {atual.erro}
                <div style={{ marginTop: 10 }}>
                  <button type="button" className="botao botao--pequeno" onClick={() => { estagiarios.recarregar(); gestores.recarregar(); }}>Tentar de novo</button>
                </div>
              </div>
            </div>
          ) : cadastrando ? (
            perfil === "estagiario" ? (
              <FormularioEstagiario
                gestores={gestores.dados || []}
                aoCancelar={() => setCadastrando(false)}
                aoCriar={(novo) => { estagiarios.recarregar(); entrar(novo); }}
              />
            ) : (
              <FormularioGestor aoCancelar={() => setCadastrando(false)} aoCriar={(novo) => { gestores.recarregar(); entrar(novo); }} />
            )
          ) : (
            <>
              {(atual.dados || []).length > 4 && (
                <div className="campo--com-icone" style={{ marginTop: 16 }}>
                  <Search />
                  <input className="entrada" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar pelo nome" aria-label="Buscar pelo nome" />
                </div>
              )}

              <div className="lista-pessoas">
                {atual.carregando && !atual.dados ? (
                  [0, 1, 2].map((n) => <Esqueleto key={n} altura={58} style={{ borderRadius: 12 }} />)
                ) : pessoas.length === 0 ? (
                  <Vazio icone={perfil === "estagiario" ? GraduationCap : Briefcase} titulo={busca ? "Ninguém com esse nome" : "Ninguém cadastrado ainda"}>
                    {busca ? "Confira a grafia ou cadastre uma pessoa nova." : "Cadastre a primeira pessoa para começar."}
                  </Vazio>
                ) : (
                  pessoas.map((p, i) => (
                    <button key={p.id} type="button" className="pessoa entra" style={{ "--i": i + 2 }} onClick={() => entrar(p)}>
                      <Avatar nome={p.nome} tamanho={38} />
                      <span className="pessoa-texto">
                        <b>{p.nome}</b>
                        <span>
                          {perfil === "estagiario"
                            ? `Meta de ${p.configuracao?.meta_horas_diaria ?? 6}h por dia`
                            : `${equipeDe(p.id)} estagiário(s) na equipe`}
                        </span>
                      </span>
                      <ChevronRight className="pessoa-seta" />
                    </button>
                  ))
                )}
              </div>

              <button type="button" className="botao botao--primario botao--bloco botao--grande" style={{ marginTop: 14 }} onClick={() => setCadastrando(true)}>
                <UserPlus />{perfil === "estagiario" ? "Cadastrar estagiário" : "Cadastrar gestor"}
              </button>
            </>
          )}
        </div>

        <div className="portal-rodape">
          <span>Programação em Python</span>
          <span>UniAnchieta 2026/2</span>
          <span>Lei do Estágio 11.788/2008</span>
        </div>
      </main>

      <section className="portal-vitrine">
        <VitrinePainel />
      </section>
    </div>
  );
}

function FormularioEstagiario({ gestores, aoCancelar, aoCriar }) {
  const notificar = useNotificar();
  const [nome, setNome] = useState("");
  const [metaDiaria, setMetaDiaria] = useState(6);
  const [metaSemanal, setMetaSemanal] = useState(30);
  const [gestorId, setGestorId] = useState(gestores[0]?.id ?? "");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const novo = await api.post("/estagiarios", {
        nome: nome.trim(),
        meta_horas_diaria: Number(metaDiaria),
        meta_horas_semanal: Number(metaSemanal),
        gestor_id: gestorId ? Number(gestorId) : null,
      });
      notificar.sucesso("Cadastro feito", `Bem-vindo, ${novo.nome}.`);
      aoCriar(novo);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="pilha entra" style={{ gap: 14, marginTop: 20 }} onSubmit={enviar}>
      <CabecalhoForm titulo="Novo estagiário" aoCancelar={aoCancelar} />
      <div className="campo">
        <label htmlFor="novo-nome">Nome completo</label>
        <input id="novo-nome" value={nome} onChange={(e) => setNome(e.target.value)} minLength={2} maxLength={120} placeholder="Ana Paula Ribeiro" autoFocus required />
      </div>
      <div className="grade-campos" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="campo">
          <label htmlFor="novo-dia">Meta por dia (h)</label>
          <input id="novo-dia" type="number" step="0.5" min="0.5" max="24" value={metaDiaria} onChange={(e) => setMetaDiaria(e.target.value)} required />
        </div>
        <div className="campo">
          <label htmlFor="novo-semana">Meta por semana (h)</label>
          <input id="novo-semana" type="number" step="1" min="1" max="168" value={metaSemanal} onChange={(e) => setMetaSemanal(e.target.value)} required />
        </div>
      </div>
      <div className="campo">
        <label htmlFor="novo-gestor">Gestor responsável</label>
        <select id="novo-gestor" value={gestorId} onChange={(e) => setGestorId(e.target.value)}>
          <option value="">Sem gestor por enquanto</option>
          {gestores.map((g) => <option key={g.id} value={g.id}>{g.nome}</option>)}
        </select>
      </div>
      {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
      <button type="submit" className="botao botao--primario" disabled={enviando}>
        {enviando ? <LoaderCircle className="girando" /> : <UserPlus />}{enviando ? "Cadastrando…" : "Cadastrar e entrar"}
      </button>
    </form>
  );
}

function FormularioGestor({ aoCancelar, aoCriar }) {
  const notificar = useNotificar();
  const [nome, setNome] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const novo = await api.post("/gestores", { nome: nome.trim() });
      notificar.sucesso("Cadastro feito", `Bem-vindo, ${novo.nome}.`);
      aoCriar(novo);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="pilha entra" style={{ gap: 14, marginTop: 20 }} onSubmit={enviar}>
      <CabecalhoForm titulo="Novo gestor" aoCancelar={aoCancelar} />
      <div className="campo">
        <label htmlFor="gestor-nome">Nome completo</label>
        <input id="gestor-nome" value={nome} onChange={(e) => setNome(e.target.value)} minLength={2} maxLength={120} placeholder="Marcos Albuquerque" autoFocus required />
      </div>
      {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
      <button type="submit" className="botao botao--primario" disabled={enviando}>
        {enviando ? <LoaderCircle className="girando" /> : <UserPlus />}{enviando ? "Cadastrando…" : "Cadastrar e entrar"}
      </button>
    </form>
  );
}

function CabecalhoForm({ titulo, aoCancelar }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <h3>{titulo}</h3>
      <button type="button" className="botao botao--fantasma botao--pequeno" onClick={aoCancelar}><X />Voltar</button>
    </div>
  );
}
