import { useParams } from "react-router-dom";
import { BadgeCheck, CircleX, LoaderCircle, ShieldAlert } from "lucide-react";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { Logo } from "../components/Logo";
import { formatarData, formatarDataHora, iniciais } from "../utils/formato";

// Pagina publica que o QR code do cracha abre (Entrega 3). Nao pede login:
// quem confere o cracha na portaria nao tem conta no sistema. Mostra so o
// minimo para comprovar o vinculo - nome, gestor, situacao e desde quando.
export function VerificarCracha() {
  const { codigo } = useParams();
  const verificacao = useApiState(() => api.get(`/cracha/verificar/${encodeURIComponent(codigo)}`), [codigo]);
  const agora = new Date().toISOString();
  const dados = verificacao.dados;

  let estado = "carregando";
  if (verificacao.erro) estado = "invalido";
  else if (dados) estado = dados.ativo ? "ativo" : "inativo";

  return (
    <div className="verificacao">
      <div className="verificacao-folha entra">
        <div className="verificacao-marca"><Logo tamanho={26} /><span>InternHub<span className="laranja">.</span></span><span className="mono">verificação de crachá</span></div>

        <div className={`verificacao-selo verificacao-selo--${estado}`}>
          {estado === "carregando" && <LoaderCircle className="girando" />}
          {estado === "ativo" && <BadgeCheck />}
          {estado === "inativo" && <ShieldAlert />}
          {estado === "invalido" && <CircleX />}
          <b>
            {estado === "carregando" && "Conferindo…"}
            {estado === "ativo" && "Vínculo de estágio ativo"}
            {estado === "inativo" && "Crachá desativado"}
            {estado === "invalido" && "Crachá não encontrado"}
          </b>
        </div>

        {dados ? (
          <>
            <div className="verificacao-pessoa">
              <div className="cracha-iniciais">{iniciais(dados.nome)}</div>
              <div>
                <h1>{dados.nome}</h1>
                <span>Estagiário{dados.gestor_nome ? ` · gestor ${dados.gestor_nome}` : ""}</span>
              </div>
            </div>
            <dl className="cracha-campos verificacao-campos">
              <div><dt>Desde</dt><dd>{dados.inicio_estagio ? formatarData(dados.inicio_estagio) : "—"}</dd></div>
              <div><dt>Emitido</dt><dd>{formatarData(dados.emitido_em)}</dd></div>
              <div><dt>Conferido</dt><dd>{formatarDataHora(agora)}</dd></div>
            </dl>
            {!dados.ativo && <p className="verificacao-nota">O gestor desativou este crachá - normalmente é o fim do estágio.</p>}
          </>
        ) : estado === "invalido" ? (
          <p className="verificacao-nota">
            O código não existe ou foi reemitido (o crachá antigo deixa de valer quando um novo é gerado). Peça para a pessoa mostrar o crachá atual.
          </p>
        ) : null}

        <footer className="verificacao-rodape mono">código {codigo.slice(0, 8).toUpperCase()}… · esta página não mostra horários nem banco de horas</footer>
      </div>
    </div>
  );
}
