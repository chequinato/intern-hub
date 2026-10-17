// Guarda quem esta logado: o token devolvido por POST /auth/entrar e os
// dados da conta (perfil, id do estagiario ou do gestor, nome).
//
// Ate a Entrega 3 isto era so um seletor de perfil - qualquer um escolhia
// "Sou gestor". Agora so existe sessao depois de e-mail e senha, e quem
// decide o que cada um ve e a API (api/permissoes.py): o frontend so
// esconde o que a pessoa nao pode usar, para nao mostrar botao que daria 403.
//
// Fica no localStorage para sobreviver a um F5. Ao abrir, o token e
// conferido em GET /auth/eu; se ele venceu (12h), volta para a tela de login.

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, CHAVE_LOGIN, quandoSessaoExpirar } from "../api/cliente";

const SessaoContext = createContext(null);

function lerSessaoSalva() {
  try {
    const bruto = localStorage.getItem(CHAVE_LOGIN);
    return bruto ? JSON.parse(bruto) : {};
  } catch {
    return {};
  }
}

function gravar(sessao) {
  try {
    if (sessao.token) localStorage.setItem(CHAVE_LOGIN, JSON.stringify(sessao));
    else localStorage.removeItem(CHAVE_LOGIN);
  } catch {
    // localStorage indisponivel (aba anonima, etc): o login vale ate o F5.
  }
}

export function SessaoProvider({ children }) {
  const [sessao, setSessao] = useState(lerSessaoSalva);
  // "conferindo" enquanto o GET /auth/eu nao volta, para a tela nao piscar
  // a area logada e depois expulsar a pessoa.
  const [conferindo, setConferindo] = useState(() => Boolean(lerSessaoSalva().token));

  const limpar = useCallback(() => {
    gravar({});
    setSessao({});
  }, []);

  useEffect(() => {
    quandoSessaoExpirar(limpar);
  }, [limpar]);

  useEffect(() => {
    if (!sessao.token) {
      setConferindo(false);
      return;
    }
    api.get("/auth/eu")
      .then((usuario) => {
        const atualizada = { token: sessao.token, usuario };
        gravar(atualizada);
        setSessao(atualizada);
      })
      .catch(() => {})
      .finally(() => setConferindo(false));
    // So na abertura: depois disso o token muda apenas por entrar/sair.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const entrar = useCallback(async (email, senha) => {
    const { token, usuario } = await api.post("/auth/entrar", { email, senha });
    const nova = { token, usuario };
    gravar(nova);
    setSessao(nova);
    return usuario;
  }, []);

  const sair = useCallback(async () => {
    try {
      await api.post("/auth/sair");
    } catch {
      // Se a API estiver fora, sai do mesmo jeito: o token vence sozinho.
    }
    limpar();
  }, [limpar]);

  const valor = useMemo(() => {
    const usuario = sessao.usuario || null;
    return {
      usuario,
      logado: Boolean(sessao.token && usuario),
      conferindo,
      perfil: usuario?.perfil ?? null,
      estagiarioId: usuario?.estagiario_id ?? null,
      gestorId: usuario?.gestor_id ?? null,
      entrar,
      sair,
    };
  }, [sessao, conferindo, entrar, sair]);

  return <SessaoContext.Provider value={valor}>{children}</SessaoContext.Provider>;
}

export function useSessao() {
  const contexto = useContext(SessaoContext);
  if (!contexto) throw new Error("useSessao precisa estar dentro de <SessaoProvider>");
  return contexto;
}

// Endereco da area de quem esta logado.
export function areaDoUsuario(usuario) {
  if (!usuario) return "/";
  return usuario.perfil === "gestor" ? `/gestor/${usuario.gestor_id}` : `/estagiario/${usuario.estagiario_id}`;
}
