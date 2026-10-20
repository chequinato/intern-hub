import { useState } from "react";
import { Check, CircleAlert, Download, LoaderCircle, Save, ShieldCheck } from "lucide-react";
import { api } from "../api/cliente";
import { useNotificar } from "./Notificacoes";
import { baixarBlob } from "../utils/arquivo";
import { formatarData, formatarDataHora, formatarHoras } from "../utils/formato";

// O fechamento do semestre (Lei 11.788/2008, art. 9o, VII), nas duas pontas:
// o gestor escreve a avaliacao e valida; o estagiario da ciencia ("vista
// obrigatoria ao estagiario"). As tres etapas aparecem como uma linha de
// progresso, igual a linha do ponto do dia.
export function EtapasDoSemestre({ semestre }) {
  const etapas = [
    { rotulo: "Atividades registradas", feita: semestre.atividades.length > 0, detalhe: `${semestre.atividades.length} registro(s)` },
    { rotulo: "Validado pelo gestor", feita: semestre.status === "validado", detalhe: semestre.validado_em ? formatarData(semestre.validado_em) : "pendente" },
    { rotulo: "Ciência do estagiário", feita: Boolean(semestre.ciente_em), detalhe: semestre.ciente_em ? formatarData(semestre.ciente_em) : "pendente" },
  ];
  return (
    <ol className="etapas-semestre">
      {etapas.map((e, i) => (
        <li key={e.rotulo} className={e.feita ? "feita" : ""}>
          <span className="etapa-numero">{e.feita ? <Check /> : i + 1}</span>
          <div><b>{e.rotulo}</b><span>{e.detalhe}</span></div>
        </li>
      ))}
    </ol>
  );
}

export function NumerosDoSemestre({ semestre }) {
  return (
    <ul className="lista-regras">
      <li><span>Período</span><b className="mono">{formatarData(semestre.inicio).slice(0, 5)} a {formatarData(semestre.fim).slice(0, 5)}</b></li>
      <li><span>Horas trabalhadas</span><b>{formatarHoras(semestre.horas_trabalhadas)}</b></li>
      <li><span>Dias com ponto completo</span><b>{semestre.dias_trabalhados}</b></li>
      <li><span>Atividades</span><b>{semestre.atividades.length}</b></li>
    </ul>
  );
}

export function BotaoPdfSemestre({ semestre }) {
  const notificar = useNotificar();
  const [baixando, setBaixando] = useState(false);
  async function baixar() {
    setBaixando(true);
    try {
      const blob = await api.baixarArquivo(`/estagio/${semestre.estagiario_id}/semestre/${semestre.ano}/${semestre.semestre}/pdf`);
      baixarBlob(blob, `relatorio_atividades_${semestre.ano}_${semestre.semestre}.pdf`);
    } catch (e) {
      notificar.erro("Não foi possível gerar o PDF", e.message);
    } finally {
      setBaixando(false);
    }
  }
  return (
    <button type="button" className="botao" onClick={baixar} disabled={baixando}>
      {baixando ? <LoaderCircle className="girando" /> : <Download />}PDF para a faculdade
    </button>
  );
}

// Formulario do gestor: salvar rascunho ou validar (fecha o semestre).
export function AvaliacaoDoGestor({ semestre, aoSalvar }) {
  const notificar = useNotificar();
  const [texto, setTexto] = useState(semestre.avaliacao_gestor || "");
  const [enviando, setEnviando] = useState(null);
  const [erro, setErro] = useState(null);
  const validado = semestre.status === "validado";

  async function salvar(validar) {
    setEnviando(validar ? "validar" : "salvar");
    setErro(null);
    try {
      const novo = await api.put(`/estagio/${semestre.estagiario_id}/semestre/${semestre.ano}/${semestre.semestre}`, { avaliacao: texto, validar });
      notificar.sucesso(validar ? "Semestre validado" : "Avaliação salva", validar ? "O estagiário já pode dar ciência." : "Ainda dá para editar antes de validar.");
      aoSalvar(novo);
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(null);
    }
  }

  if (validado) {
    return (
      <div className="pilha" style={{ gap: 10 }}>
        <div className="divisor">Avaliação do supervisor</div>
        <blockquote className="citacao"><ShieldCheck size={14} />{semestre.avaliacao_gestor}</blockquote>
        <p className="texto-3" style={{ fontSize: 12.5 }}>Validado em {formatarDataHora(semestre.validado_em)}. O semestre está fechado.</p>
      </div>
    );
  }
  return (
    <div className="pilha" style={{ gap: 10 }}>
      <div className="divisor">Avaliação do supervisor</div>
      <div className="campo">
        <textarea value={texto} onChange={(e) => setTexto(e.target.value)} maxLength={1500} rows={5} aria-label="Avaliação"
          placeholder="Como foi o desempenho no semestre: entregas, aprendizado, pontos a desenvolver." />
      </div>
      {erro && <div className="aviso aviso--alerta"><CircleAlert />{erro}</div>}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button type="button" className="botao" onClick={() => salvar(false)} disabled={Boolean(enviando)}>
          {enviando === "salvar" ? <LoaderCircle className="girando" /> : <Save />}Salvar rascunho
        </button>
        <button type="button" className="botao botao--primario" onClick={() => salvar(true)} disabled={Boolean(enviando) || !texto.trim()}>
          {enviando === "validar" ? <LoaderCircle className="girando" /> : <ShieldCheck />}Validar semestre
        </button>
      </div>
      <p className="texto-3" style={{ fontSize: 12.5 }}>Validar fecha o semestre: as atividades não mudam mais.</p>
    </div>
  );
}

// Navegador de semestre: "2º semestre de 2026" com setas.
export function semestreAtual() {
  const hoje = new Date();
  return { ano: hoje.getFullYear(), semestre: hoje.getMonth() < 6 ? 1 : 2 };
}

export function mudarSemestre({ ano, semestre }, delta) {
  const indice = ano * 2 + (semestre - 1) + delta;
  return { ano: Math.floor(indice / 2), semestre: (indice % 2) + 1 };
}
