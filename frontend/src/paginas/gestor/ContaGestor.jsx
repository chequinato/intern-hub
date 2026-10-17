import { useState } from "react";
import { CircleAlert, LoaderCircle, UserPlus } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useSessao } from "../../context/SessaoContext";
import { useNotificar } from "../../components/Notificacoes";
import { TrocarSenha } from "../../components/TrocarSenha";
import { Avatar } from "../../components/Ui";

// Conta do gestor e cadastro de outros gestores (Entrega 3). Depois do
// primeiro, gestor novo so entra no sistema por aqui - se fosse pela tela
// de entrada, um estagiario criaria um "gestor" para aprovar os proprios
// ajustes (a API recusa com 403; ver api/rotas/gestores.py).
export function ContaGestor() {
  const { usuario } = useSessao();
  const gestores = useApiState(() => api.get("/gestores"), []);

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Conta e gestores</h1>
          <p>Sua senha e o cadastro de outros gestores. Só um gestor logado cadastra outro.</p>
        </div>
      </div>

      <div className="grade grade-2">
        <div className="pilha">
          <section className="cartao entra" style={{ "--i": 1 }}>
            <div className="cartao-cabeca"><h2>Sua conta</h2></div>
            <ul className="lista-regras cartao-corpo">
              <li><span>Nome</span><b>{usuario?.nome}</b></li>
              <li><span>E-mail de acesso</span><b>{usuario?.email}</b></li>
              <li><span>Perfil</span><b>Gestor</b></li>
            </ul>
          </section>
          <TrocarSenha i={2} />
        </div>

        <div className="pilha">
          <NovoGestor aoCriar={gestores.recarregar} />
          <section className="cartao entra" style={{ "--i": 4 }}>
            <div className="cartao-cabeca"><h2>Gestores cadastrados</h2><span className="sub">{(gestores.dados || []).length}</span></div>
            <ul className="lista-pessoas-simples">
              {(gestores.dados || []).map((g) => (
                <li key={g.id}><Avatar nome={g.nome} tamanho={28} /><span>{g.nome}</span>{g.id === usuario?.gestor_id && <span className="selo selo--marca">você</span>}</li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </>
  );
}

function NovoGestor({ aoCriar }) {
  const notificar = useNotificar();
  const [form, setForm] = useState({ nome: "", email: "", senha: "" });
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);
  const mudar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const novo = await api.post("/gestores", { nome: form.nome.trim(), email: form.email.trim(), senha: form.senha });
      notificar.sucesso("Gestor cadastrado", `${novo.nome} já pode entrar com o e-mail ${form.email.trim()}.`);
      setForm({ nome: "", email: "", senha: "" });
      aoCriar();
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao entra" style={{ "--i": 3 }} onSubmit={enviar}>
      <div className="cartao-cabeca"><h2>Cadastrar gestor</h2></div>
      <div className="cartao-corpo pilha" style={{ gap: 14 }}>
        <div className="campo">
          <label htmlFor="ng-nome">Nome completo</label>
          <input id="ng-nome" value={form.nome} onChange={mudar("nome")} minLength={2} maxLength={120} required />
        </div>
        <div className="grade-campos">
          <div className="campo">
            <label htmlFor="ng-email">E-mail</label>
            <input id="ng-email" type="email" value={form.email} onChange={mudar("email")} required />
          </div>
          <div className="campo">
            <label htmlFor="ng-senha">Senha inicial</label>
            <input id="ng-senha" type="password" value={form.senha} onChange={mudar("senha")} minLength={8} maxLength={128} autoComplete="new-password" required />
          </div>
        </div>
        <span className="dica texto-3" style={{ fontSize: 12.5 }}>Passe a senha inicial para a pessoa; ela troca na primeira vez que entrar.</span>
        {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
        <div>
          <button type="submit" className="botao botao--primario" disabled={enviando}>
            {enviando ? <LoaderCircle className="girando" /> : <UserPlus />}Cadastrar gestor
          </button>
        </div>
      </div>
    </form>
  );
}
