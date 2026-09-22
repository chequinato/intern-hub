import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { useSessao } from "../context/SessaoContext";

// Tela inicial: escolher quem esta usando o sistema. Equivalente ao topo
// de app.py no Streamlit - o seletor de perfil (estagiario/gestor) e,
// dentro de cada um, o "Selecione seu nome" ou o formulario de cadastro.
export function Portal() {
  const [perfil, setPerfil] = useState("estagiario");
  const navegar = useNavigate();
  const { escolherEstagiario, escolherGestor } = useSessao();

  const { dados: estagiarios, carregando: carregandoEst, erro: erroEst, recarregar: recarregarEst } =
    useApiState(() => api.get("/estagiarios"));
  const { dados: gestores, carregando: carregandoGes, erro: erroGes, recarregar: recarregarGes } =
    useApiState(() => api.get("/gestores"));

  const carregando = perfil === "estagiario" ? carregandoEst : carregandoGes;
  const erro = perfil === "estagiario" ? erroEst : erroGes;

  return (
    <div className="portal">
      <div className="portal-folha rv">
        <h1 className="portal-titulo">InternHub</h1>
        <p className="portal-sub">Banco de horas do estagio</p>

        <div className="perfil-toggle">
          <button type="button" className={perfil === "estagiario" ? "on" : ""} onClick={() => setPerfil("estagiario")}>
            Sou estagiario
          </button>
          <button type="button" className={perfil === "gestor" ? "on" : ""} onClick={() => setPerfil("gestor")}>
            Sou gestor
          </button>
        </div>

        {erro && <p className="aviso aviso--erro" style={{ marginTop: 20 }}>{erro}</p>}
        {carregando && !erro && <p className="empty">Carregando...</p>}

        {!carregando && !erro && perfil === "estagiario" && (
          <SelecaoEstagiario
            estagiarios={estagiarios || []}
            gestores={gestores || []}
            aoEscolher={(id) => { escolherEstagiario(id); navegar(`/estagiario/${id}`); }}
            aoCadastrar={recarregarEst}
          />
        )}

        {!carregando && !erro && perfil === "gestor" && (
          <SelecaoGestor
            gestores={gestores || []}
            aoEscolher={(id) => { escolherGestor(id); navegar(`/gestor/${id}`); }}
            aoCadastrar={recarregarGes}
          />
        )}
      </div>
    </div>
  );
}

function SelecaoEstagiario({ estagiarios, gestores, aoEscolher, aoCadastrar }) {
  const [mostrarForm, setMostrarForm] = useState(estagiarios.length === 0);

  return (
    <div style={{ marginTop: 24 }}>
      {estagiarios.length > 0 && (
        <div className="campo">
          <label>Selecione seu nome</label>
          <select onChange={(e) => e.target.value && aoEscolher(Number(e.target.value))} defaultValue="">
            <option value="" disabled>Escolha...</option>
            {estagiarios.map((pessoa) => (
              <option key={pessoa.id} value={pessoa.id}>{pessoa.nome}</option>
            ))}
          </select>
        </div>
      )}

      {estagiarios.length > 0 && (
        <button type="button" className="botao" style={{ marginTop: 14 }} onClick={() => setMostrarForm((v) => !v)}>
          {mostrarForm ? "Cancelar" : "Cadastrar novo estagiario"}
        </button>
      )}

      {mostrarForm && (
        <FormularioEstagiario
          gestores={gestores}
          onCriado={(criado) => { aoCadastrar(); aoEscolher(criado.id); }}
        />
      )}
    </div>
  );
}

function FormularioEstagiario({ gestores, onCriado }) {
  const [nome, setNome] = useState("");
  const [metaDiaria, setMetaDiaria] = useState(6);
  const [metaSemanal, setMetaSemanal] = useState(30);
  const [gestorId, setGestorId] = useState("");
  const [erro, setErro] = useState(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e) {
    e.preventDefault();
    if (nome.trim().length < 2) {
      setErro("Digite um nome com pelo menos 2 caracteres.");
      return;
    }
    setEnviando(true);
    setErro(null);
    try {
      const criado = await api.post("/estagiarios", {
        nome: nome.trim(),
        meta_horas_diaria: Number(metaDiaria),
        meta_horas_semanal: Number(metaSemanal),
        gestor_id: gestorId ? Number(gestorId) : null,
      });
      onCriado(criado);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="form" style={{ marginTop: 18 }} onSubmit={enviar}>
      <div className="campo">
        <label>Nome</label>
        <input value={nome} onChange={(e) => setNome(e.target.value)} maxLength={120} />
      </div>
      <div className="campo-linha">
        <div className="campo">
          <label>Meta diaria (h)</label>
          <input type="number" step="0.5" min="1" max="24" value={metaDiaria} onChange={(e) => setMetaDiaria(e.target.value)} />
        </div>
        <div className="campo">
          <label>Meta semanal (h)</label>
          <input type="number" step="1" min="1" max="168" value={metaSemanal} onChange={(e) => setMetaSemanal(e.target.value)} />
        </div>
      </div>
      <div className="campo">
        <label>Gestor responsavel</label>
        <select value={gestorId} onChange={(e) => setGestorId(e.target.value)}>
          <option value="">Sem gestor por enquanto</option>
          {gestores.map((g) => (
            <option key={g.id} value={g.id}>{g.nome}</option>
          ))}
        </select>
      </div>
      {erro && <p className="aviso aviso--erro">{erro}</p>}
      <button type="submit" className="botao" disabled={enviando}>
        {enviando ? "Cadastrando..." : "Cadastrar"}
      </button>
    </form>
  );
}

function SelecaoGestor({ gestores, aoEscolher, aoCadastrar }) {
  const [mostrarForm, setMostrarForm] = useState(gestores.length === 0);
  const [nome, setNome] = useState("");
  const [erro, setErro] = useState(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e) {
    e.preventDefault();
    if (nome.trim().length < 2) {
      setErro("Digite um nome com pelo menos 2 caracteres.");
      return;
    }
    setEnviando(true);
    setErro(null);
    try {
      const criado = await api.post("/gestores", { nome: nome.trim() });
      aoCadastrar();
      aoEscolher(criado.id);
    } catch (e2) {
      setErro(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={{ marginTop: 24 }}>
      {gestores.length > 0 && (
        <div className="campo">
          <label>Selecione seu nome</label>
          <select onChange={(e) => e.target.value && aoEscolher(Number(e.target.value))} defaultValue="">
            <option value="" disabled>Escolha...</option>
            {gestores.map((g) => (
              <option key={g.id} value={g.id}>{g.nome}</option>
            ))}
          </select>
        </div>
      )}

      {gestores.length > 0 && (
        <button type="button" className="botao" style={{ marginTop: 14 }} onClick={() => setMostrarForm((v) => !v)}>
          {mostrarForm ? "Cancelar" : "Cadastrar novo gestor"}
        </button>
      )}

      {mostrarForm && (
        <form className="form" style={{ marginTop: 18 }} onSubmit={enviar}>
          <div className="campo">
            <label>Nome do gestor</label>
            <input value={nome} onChange={(e) => setNome(e.target.value)} maxLength={120} />
          </div>
          {erro && <p className="aviso aviso--erro">{erro}</p>}
          <button type="submit" className="botao" disabled={enviando}>
            {enviando ? "Cadastrando..." : "Cadastrar gestor"}
          </button>
        </form>
      )}
    </div>
  );
}
