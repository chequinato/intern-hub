import { useState } from "react";
import { CircleAlert, KeyRound, LoaderCircle } from "lucide-react";
import { api } from "../api/cliente";
import { useNotificar } from "./Notificacoes";

// Troca da propria senha (PATCH /auth/senha). Os outros logins abertos da
// pessoa sao derrubados pela API - se a senha vazou, quem entrou com ela sai.
export function TrocarSenha({ i = 0 }) {
  const notificar = useNotificar();
  const [atual, setAtual] = useState("");
  const [nova, setNova] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      await api.patch("/auth/senha", { senha_atual: atual, senha_nova: nova });
      notificar.sucesso("Senha trocada", "Os outros aparelhos conectados foram desconectados.");
      setAtual("");
      setNova("");
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao entra" style={{ "--i": i }} onSubmit={enviar}>
      <div className="cartao-cabeca"><h2><KeyRound />Senha</h2><span className="sub">mínimo de 8 caracteres</span></div>
      <div className="cartao-corpo pilha" style={{ gap: 14 }}>
        <div className="grade-campos">
          <div className="campo">
            <label htmlFor="senha-atual">Senha atual</label>
            <input id="senha-atual" type="password" value={atual} onChange={(e) => setAtual(e.target.value)} autoComplete="current-password" required />
          </div>
          <div className="campo">
            <label htmlFor="senha-nova">Nova senha</label>
            <input id="senha-nova" type="password" value={nova} onChange={(e) => setNova(e.target.value)} minLength={8} maxLength={128} autoComplete="new-password" required />
          </div>
        </div>
        {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
        <div>
          <button type="submit" className="botao" disabled={enviando}>
            {enviando ? <LoaderCircle className="girando" /> : <KeyRound />}Trocar senha
          </button>
        </div>
      </div>
    </form>
  );
}
