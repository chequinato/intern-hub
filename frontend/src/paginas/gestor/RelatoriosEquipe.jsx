import { useState } from "react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { ChevronLeft, ChevronRight, NotebookPen, Users } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { Avatar, Esqueleto, Vazio } from "../../components/Ui";
import {
  AvaliacaoDoGestor, BotaoPdfSemestre, EtapasDoSemestre, mudarSemestre, NumerosDoSemestre, semestreAtual,
} from "../../components/RelatorioSemestral";
import { diaDaSemana, formatarDataCurta } from "../../utils/formato";

const SITUACAO = {
  vazio: ["Sem atividades", "selo"],
  aberto: ["Para avaliar", "selo selo--atencao"],
  validado: ["Validado", "selo selo--info"],
  ciente: ["Concluído", "selo selo--credito"],
};

// Relatorios semestrais da equipe (Entrega 3, Lei 11.788/2008, art. 9o, VII):
// o gestor le as atividades de cada estagiario, escreve a avaliacao e valida
// o semestre. Depois disso o estagiario da ciencia e o PDF vai para a
// faculdade.
export function RelatoriosEquipe() {
  const { painel } = useOutletContext();
  const [periodo, setPeriodo] = useState(semestreAtual);
  const [busca, setBusca] = useSearchParams();
  const equipe = painel?.equipe || [];

  // Um GET por estagiario da equipe: o resumo do semestre de cada um.
  const resumos = useApiState(
    () => Promise.all(equipe.map((e) => api.get(`/estagio/${e.estagiario_id}/semestre/${periodo.ano}/${periodo.semestre}`))),
    [equipe.length, periodo.ano, periodo.semestre]
  );
  const porId = new Map((resumos.dados || []).map((r) => [r.estagiario_id, r]));
  // Sem escolha no endereco, abre em quem esta esperando avaliacao.
  const primeiroParaAvaliar = (resumos.dados || []).find((r) => r.status !== "validado" && r.atividades.length > 0);
  const selecionado = Number(busca.get("estagiario")) || primeiroParaAvaliar?.estagiario_id || equipe[0]?.estagiario_id || null;
  const atual = porId.get(selecionado);
  const ehAtual = periodo.ano === semestreAtual().ano && periodo.semestre === semestreAtual().semestre;

  function situacao(r) {
    if (!r) return "vazio";
    if (r.ciente_em) return "ciente";
    if (r.status === "validado") return "validado";
    return r.atividades.length ? "aberto" : "vazio";
  }

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Relatórios semestrais</h1>
          <p>Avalie as atividades de cada estagiário e valide o semestre. O PDF é o relatório que vai para a faculdade.</p>
        </div>
        <div className="navegador-mes navegador-mes--destaque">
          <button type="button" className="botao botao--fantasma botao--icone" onClick={() => setPeriodo((p) => mudarSemestre(p, -1))} aria-label="Semestre anterior"><ChevronLeft /></button>
          <span>{periodo.semestre}º semestre de {periodo.ano}</span>
          <button type="button" className="botao botao--fantasma botao--icone" onClick={() => setPeriodo((p) => mudarSemestre(p, 1))} disabled={ehAtual} aria-label="Próximo semestre"><ChevronRight /></button>
        </div>
      </div>

      {equipe.length === 0 ? (
        <section className="cartao"><Vazio icone={Users} titulo="Nenhum estagiário na equipe" /></section>
      ) : (
        <div className="grade grade-chamados">
          <section className="cartao entra" style={{ "--i": 1 }}>
            <div className="cartao-cabeca"><h2>Equipe</h2><span className="sub">situação do semestre</span></div>
            <ul className="lista-pessoas-simples lista-pessoas-simples--clicavel">
              {equipe.map((e) => {
                const [rotulo, classe] = SITUACAO[situacao(porId.get(e.estagiario_id))];
                return (
                  <li key={e.estagiario_id}>
                    <button type="button" className={e.estagiario_id === selecionado ? "ativo" : ""}
                      onClick={() => setBusca({ estagiario: String(e.estagiario_id) })}>
                      <Avatar nome={e.nome} tamanho={30} />
                      <span>{e.nome}</span>
                      {resumos.dados ? <span className={classe}>{rotulo}</span> : <Esqueleto altura={22} largura={80} />}
                    </button>
                  </li>
                );
              })}
            </ul>
          </section>

          <section className="cartao entra" style={{ "--i": 2 }}>
            {!atual ? (
              <div className="cartao-corpo pilha"><Esqueleto altura={30} /><Esqueleto altura={200} /></div>
            ) : (
              <>
                <div className="cartao-cabeca">
                  <h2>{atual.estagiario_nome}</h2>
                  <BotaoPdfSemestre semestre={atual} />
                </div>
                <div className="cartao-corpo pilha" style={{ gap: 18 }}>
                  <EtapasDoSemestre semestre={atual} />
                  <NumerosDoSemestre semestre={atual} />
                  <div className="pilha" style={{ gap: 8 }}>
                    <div className="divisor">Atividades registradas</div>
                    {atual.atividades.length === 0 ? (
                      <p className="texto-3" style={{ fontSize: 13 }}>
                        <NotebookPen size={13} style={{ display: "inline", verticalAlign: "-2px" }} /> Nada registrado neste semestre.
                      </p>
                    ) : (
                      <ol className="diario diario--compacto">
                        {atual.atividades.map((a) => (
                          <li key={a.id}>
                            <div className="data-bloco"><span>{diaDaSemana(a.data)}</span><b>{formatarDataCurta(a.data)}</b></div>
                            <p>{a.descricao}</p>
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                  <AvaliacaoDoGestor
                    key={`${atual.estagiario_id}-${atual.ano}-${atual.semestre}`}
                    semestre={atual}
                    aoSalvar={(novo) => {
                      // Fixa a escolha no endereco: sem isso, depois de validar a tela
                      // pularia para o proximo que ainda esta "para avaliar".
                      setBusca({ estagiario: String(novo.estagiario_id) });
                      resumos.setDados((lista) => lista.map((r) => (r.estagiario_id === novo.estagiario_id ? novo : r)));
                    }}
                  />
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </>
  );
}
