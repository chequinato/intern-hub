import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";

function hoje() {
  return new Date().toISOString().slice(0, 10);
}

// Tela de registro de ponto: formulario do dia + historico recente.
// Um dia com almoco incompleto NAO e recusado pela API - ele e salvo e
// volta com pendencia=true e um aviso (mesma regra do README, secao 7).
export function Registro() {
  const { estagiarioId } = useOutletContext();
  const { dados: registros, carregando, erro, recarregar } = useApiState(
    () => api.get(`/registros/${estagiarioId}`),
    [estagiarioId]
  );

  const [form, setForm] = useState({
    data: hoje(),
    entrada: "",
    saida: "",
    saida_almoco: "",
    retorno_almoco: "",
  });
  const [avisoUltimoEnvio, setAvisoUltimoEnvio] = useState(null);
  const [erroEnvio, setErroEnvio] = useState(null);
  const [enviando, setEnviando] = useState(false);

  function atualizarCampo(campo, valor) {
    setForm((atual) => ({ ...atual, [campo]: valor }));
  }

  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    setErroEnvio(null);
    setAvisoUltimoEnvio(null);
    try {
      const payload = {
        estagiario_id: estagiarioId,
        data: form.data,
        entrada: form.entrada,
        saida: form.saida || null,
        saida_almoco: form.saida_almoco || null,
        retorno_almoco: form.retorno_almoco || null,
      };
      const criado = await api.post("/registros", payload);
      const avisos = [criado.aviso, criado.aviso_limite_legal].filter(Boolean);
      if (avisos.length) setAvisoUltimoEnvio(avisos.join(" "));
      setForm({ data: hoje(), entrada: "", saida: "", saida_almoco: "", retorno_almoco: "" });
      recarregar();
    } catch (e2) {
      setErroEnvio(e2.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      <div className="section-mark"><span className="name">Ponto do dia</span></div>

      <form className="form card" onSubmit={enviar}>
        <div className="campo-linha">
          <div className="campo">
            <label>Data</label>
            <input type="date" value={form.data} onChange={(e) => atualizarCampo("data", e.target.value)} required />
          </div>
          <div className="campo">
            <label>Entrada</label>
            <input type="time" value={form.entrada} onChange={(e) => atualizarCampo("entrada", e.target.value)} required />
          </div>
          <div className="campo">
            <label>Saida</label>
            <input type="time" value={form.saida} onChange={(e) => atualizarCampo("saida", e.target.value)} />
          </div>
        </div>
        <div className="campo-linha">
          <div className="campo">
            <label>Saida almoco</label>
            <input type="time" value={form.saida_almoco} onChange={(e) => atualizarCampo("saida_almoco", e.target.value)} />
          </div>
          <div className="campo">
            <label>Retorno almoco</label>
            <input type="time" value={form.retorno_almoco} onChange={(e) => atualizarCampo("retorno_almoco", e.target.value)} />
          </div>
        </div>

        {erroEnvio && <p className="aviso aviso--erro">{erroEnvio}</p>}
        {avisoUltimoEnvio && <p className="aviso">{avisoUltimoEnvio}</p>}

        <button type="submit" className="botao" disabled={enviando}>
          {enviando ? "Salvando..." : "Registrar ponto"}
        </button>
      </form>

      <div className="section-mark" style={{ marginTop: 32 }}><span className="name">Historico recente</span></div>

      {carregando && <p className="empty">Carregando...</p>}
      {erro && <p className="aviso aviso--erro">{erro}</p>}
      {!carregando && !erro && (
        <TabelaHistorico registros={[...(registros || [])].reverse().slice(0, 15)} />
      )}
    </>
  );
}

function TabelaHistorico({ registros }) {
  if (registros.length === 0) return <p className="empty">Nenhum registro ainda.</p>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Entrada</th>
            <th>Saida</th>
            <th>Almoco</th>
            <th>Horas</th>
            <th>Situacao</th>
          </tr>
        </thead>
        <tbody>
          {registros.map((r, i) => (
            <tr key={r.id} style={{ "--i": i }}>
              <td>{r.data}</td>
              <td>{(r.entrada || "-").slice(0, 5)}</td>
              <td>{(r.saida || "-").slice(0, 5)}</td>
              <td>{r.saida_almoco ? `${r.saida_almoco.slice(0, 5)} - ${(r.retorno_almoco || "?").slice(0, 5)}` : "-"}</td>
              <td className="num" style={{ fontSize: 15 }}>{r.horas_trabalhadas.toFixed(2)}h</td>
              <td>
                {r.pendencia && <span className="aviso" style={{ padding: "4px 8px" }}>Pendencia de almoco</span>}
                {!r.pendencia && r.aviso_limite_legal && <span className="aviso" style={{ padding: "4px 8px" }}>Acima do limite legal</span>}
                {!r.pendencia && !r.aviso_limite_legal && <span className="state state--aprovado"><i />OK</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
