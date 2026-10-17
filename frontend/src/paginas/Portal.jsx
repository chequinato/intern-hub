import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Briefcase, CircleAlert, Eye, EyeOff, LoaderCircle, LogIn, UserPlus } from "lucide-react";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { areaDoUsuario, useSessao } from "../context/SessaoContext";
import { Logo } from "../components/Logo";
import { VitrinePainel } from "../components/VitrinePainel";
import { useNotificar } from "../components/Notificacoes";

// Tela de entrada (Entrega 3): login com e-mail e senha e o cadastro do
// estagiario. Ate aqui era um seletor de perfil - qualquer um entrava como
// gestor e aprovava os proprios ajustes. Agora a conta define o perfil.
//
// O cadastro de gestor so aparece aqui enquanto nao existe nenhum gestor
// (o primeiro precisa comecar); depois disso, gestor novo e cadastrado por
// outro gestor, dentro da area dele (ContaGestor).
export function Portal() {
  const { logado, usuario, conferindo } = useSessao();
  const [modo, setModo] = useState("entrar");
  const gestores = useApiState(() => api.get("/gestores"));
  const semGestor = gestores.dados && gestores.dados.length === 0;

  if (logado && !conferindo) return <Navigate to={areaDoUsuario(usuario)} replace />;

  return (
    <div className="portal">
      <main className="portal-acesso">
        <div className="portal-marca-topo">
          <Logo tamanho={34} />
          <span>InternHub<span className="laranja">.</span></span>
        </div>

        <div className="portal-caixa entra">
          <h1>Cada minuto<br />no lugar certo.</h1>
          <p>Ponto, saldo e ajustes do estágio, com a conta feita pelo sistema. Entre com a sua conta.</p>

          <div className="segmentado segmentado--bloco" role="tablist">
            <button type="button" className={modo === "entrar" ? "ativo" : ""} onClick={() => setModo("entrar")}>
              <LogIn />Entrar
            </button>
            <button type="button" className={modo === "cadastro" ? "ativo" : ""} onClick={() => setModo("cadastro")}>
              <UserPlus />Criar conta
            </button>
            {semGestor && (
              <button type="button" className={modo === "gestor" ? "ativo" : ""} onClick={() => setModo("gestor")}>
                <Briefcase />Primeiro gestor
              </button>
            )}
          </div>

          {gestores.erro ? (
            <div className="aviso aviso--alerta" style={{ marginTop: 20 }}>
              <CircleAlert />
              <div>
                <strong>Não foi possível falar com a API.</strong> {gestores.erro}
                <div style={{ marginTop: 10 }}>
                  <button type="button" className="botao botao--pequeno" onClick={gestores.recarregar}>Tentar de novo</button>
                </div>
              </div>
            </div>
          ) : modo === "entrar" ? (
            <FormularioLogin />
          ) : modo === "cadastro" ? (
            <FormularioEstagiario gestores={gestores.dados || []} />
          ) : (
            <FormularioGestor aoCriar={gestores.recarregar} />
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

function CampoSenha({ id, valor, aoMudar, rotulo = "Senha", autoComplete = "current-password", minimo }) {
  const [visivel, setVisivel] = useState(false);
  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <div className="campo-senha">
        <input id={id} type={visivel ? "text" : "password"} value={valor} onChange={(e) => aoMudar(e.target.value)}
          autoComplete={autoComplete} minLength={minimo} maxLength={128} required />
        <button type="button" onClick={() => setVisivel((v) => !v)} aria-label={visivel ? "Esconder senha" : "Mostrar senha"}>
          {visivel ? <EyeOff /> : <Eye />}
        </button>
      </div>
      {minimo && <span className="dica">Pelo menos {minimo} caracteres.</span>}
    </div>
  );
}

// Entra e vai direto para a area do perfil da conta.
function useEntrarENavegar() {
  const { entrar } = useSessao();
  const navegar = useNavigate();
  return async (email, senha) => {
    const usuario = await entrar(email, senha);
    navegar(areaDoUsuario(usuario), { replace: true });
  };
}

function FormularioLogin() {
  const entrarENavegar = useEntrarENavegar();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await entrarENavegar(email.trim(), senha);
    } catch (e2) {
      setErro(e2.message);
      setEnviando(false);
    }
  }

  return (
    <form className="pilha entra" style={{ gap: 14, marginTop: 20 }} onSubmit={enviar}>
      <div className="campo">
        <label htmlFor="login-email">E-mail</label>
        <input id="login-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
          autoComplete="username" placeholder="voce@empresa.com" autoFocus required />
      </div>
      <CampoSenha id="login-senha" valor={senha} aoMudar={setSenha} />
      {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
      <button type="submit" className="botao botao--primario botao--bloco botao--grande" disabled={enviando}>
        {enviando ? <LoaderCircle className="girando" /> : <LogIn />}{enviando ? "Entrando…" : "Entrar"}
      </button>
      <p className="portal-nota">
        Primeira vez? Rode <code>python popular_demo.py</code> na raiz do projeto: ele cria as contas de exemplo
        (estão no README).
      </p>
    </form>
  );
}

function FormularioEstagiario({ gestores }) {
  const notificar = useNotificar();
  const entrarENavegar = useEntrarENavegar();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
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
        email: email.trim(),
        senha,
        meta_horas_diaria: Number(metaDiaria),
        meta_horas_semanal: Number(metaSemanal),
        gestor_id: gestorId ? Number(gestorId) : null,
      });
      notificar.sucesso("Conta criada", `Bem-vindo, ${novo.nome}.`);
      await entrarENavegar(email.trim(), senha);
    } catch (e2) {
      setErro(e2.message);
      setEnviando(false);
    }
  }

  return (
    <form className="pilha entra" style={{ gap: 14, marginTop: 20 }} onSubmit={enviar}>
      <div className="campo">
        <label htmlFor="novo-nome">Nome completo</label>
        <input id="novo-nome" value={nome} onChange={(e) => setNome(e.target.value)} minLength={2} maxLength={120} placeholder="Ana Paula Ribeiro" autoFocus required />
      </div>
      <div className="grade-campos" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="campo">
          <label htmlFor="novo-email">E-mail</label>
          <input id="novo-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required />
        </div>
        <CampoSenha id="novo-senha" valor={senha} aoMudar={setSenha} autoComplete="new-password" minimo={8} />
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
        <span className="dica">Depois do cadastro, só o gestor muda a meta e o vínculo.</span>
      </div>
      {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
      <button type="submit" className="botao botao--primario" disabled={enviando}>
        {enviando ? <LoaderCircle className="girando" /> : <UserPlus />}{enviando ? "Criando conta…" : "Criar conta e entrar"}
      </button>
    </form>
  );
}

function FormularioGestor({ aoCriar }) {
  const notificar = useNotificar();
  const entrarENavegar = useEntrarENavegar();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const novo = await api.post("/gestores", { nome: nome.trim(), email: email.trim(), senha });
      notificar.sucesso("Conta criada", `Bem-vindo, ${novo.nome}.`);
      aoCriar();
      await entrarENavegar(email.trim(), senha);
    } catch (e2) {
      setErro(e2.message);
      setEnviando(false);
    }
  }

  return (
    <form className="pilha entra" style={{ gap: 14, marginTop: 20 }} onSubmit={enviar}>
      <div className="aviso"><Briefcase />Ainda não existe nenhum gestor. O primeiro se cadastra aqui; os próximos são cadastrados por um gestor, dentro do sistema.</div>
      <div className="campo">
        <label htmlFor="gestor-nome">Nome completo</label>
        <input id="gestor-nome" value={nome} onChange={(e) => setNome(e.target.value)} minLength={2} maxLength={120} placeholder="Marcos Albuquerque" autoFocus required />
      </div>
      <div className="campo">
        <label htmlFor="gestor-email">E-mail</label>
        <input id="gestor-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required />
      </div>
      <CampoSenha id="gestor-senha" valor={senha} aoMudar={setSenha} autoComplete="new-password" minimo={8} />
      {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
      <button type="submit" className="botao botao--primario" disabled={enviando}>
        {enviando ? <LoaderCircle className="girando" /> : <UserPlus />}{enviando ? "Criando conta…" : "Criar conta de gestor"}
      </button>
    </form>
  );
}
