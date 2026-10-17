import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { CircleAlert, Copy, LoaderCircle, Printer, RefreshCw, ShieldCheck } from "lucide-react";
import { api } from "../../api/cliente";
import { useApiState } from "../../useApiState";
import { useNotificar } from "../../components/Notificacoes";
import { CrachaArte } from "../../components/CrachaArte";
import { CarregandoPagina, ErroCarregar } from "../../components/Ui";

// Cracha virtual (Entrega 3). Serve para comprovar o vinculo de estagio -
// na portaria, no RH, na faculdade - sem mostrar o banco de horas: o QR
// code abre uma pagina publica que diz so o nome, o gestor e se o cracha
// esta ativo. Perdeu o cracha impresso? "Reemitir" troca o codigo e o QR
// antigo para de valer na hora.
export function Cracha() {
  const { estagiarioId } = useOutletContext();
  const notificar = useNotificar();
  const cracha = useApiState(() => api.get(`/cracha/${estagiarioId}`), [estagiarioId]);
  const [reemitindo, setReemitindo] = useState(false);
  const [confirmar, setConfirmar] = useState(false);

  async function reemitir() {
    setReemitindo(true);
    try {
      cracha.setDados(await api.post(`/cracha/${estagiarioId}/reemitir`));
      notificar.sucesso("Crachá reemitido", "O QR code antigo não vale mais.");
      setConfirmar(false);
    } catch (e) {
      notificar.erro("Não foi possível reemitir", e.message);
    } finally {
      setReemitindo(false);
    }
  }

  async function copiar() {
    try {
      await navigator.clipboard.writeText(cracha.dados.url_verificacao);
      notificar.sucesso("Endereço copiado", "Cole onde precisar comprovar o vínculo.");
    } catch {
      notificar.erro("Não foi possível copiar", cracha.dados.url_verificacao);
    }
  }

  if (cracha.erro) return <ErroCarregar mensagem={cracha.erro} aoTentar={cracha.recarregar} />;
  if (!cracha.dados) return <CarregandoPagina />;
  const dados = cracha.dados;

  return (
    <>
      <div className="cabecalho-pagina entra nao-imprimir">
        <div>
          <h1>Crachá virtual</h1>
          <p>Mostre no celular ou imprima. Quem ler o QR code vê só o seu nome, o gestor e se o crachá está ativo.</p>
        </div>
        <div className="acoes">
          <button type="button" className="botao" onClick={() => window.print()}><Printer />Imprimir</button>
        </div>
      </div>

      <div className="cracha-palco">
        <div className="cracha-moldura entra" style={{ "--i": 1 }}>
          <CrachaArte cracha={dados} />
        </div>

        <div className="pilha nao-imprimir" style={{ maxWidth: 420 }}>
          {!dados.ativo && (
            <div className="aviso aviso--alerta entra"><CircleAlert />O gestor desativou este crachá. A verificação mostra "inativo" para quem ler o QR code.</div>
          )}
          <section className="cartao entra" style={{ "--i": 2 }}>
            <div className="cartao-cabeca"><h2><ShieldCheck />O que a verificação mostra</h2></div>
            <ul className="lista-regras cartao-corpo">
              <li><span>Nome e gestor</span><b>sim</b></li>
              <li><span>Situação (ativo ou inativo)</span><b>sim</b></li>
              <li><span>Início do estágio</span><b>sim</b></li>
              <li><span>Saldo, horários e pendências</span><b className="alerta">nunca</b></li>
            </ul>
            <div className="cartao-rodape cracha-endereco">
              <code>{dados.url_verificacao}</code>
              <button type="button" className="botao botao--fantasma botao--icone" onClick={copiar} aria-label="Copiar endereço"><Copy /></button>
            </div>
          </section>

          <section className="cartao entra" style={{ "--i": 3 }}>
            <div className="cartao-cabeca"><h2>Perdeu o crachá?</h2></div>
            <div className="cartao-corpo pilha" style={{ gap: 12 }}>
              <p className="texto-2" style={{ fontSize: 13.5 }}>
                Reemitir gera um código novo. O QR code impresso antigo passa a dar "crachá não encontrado".
              </p>
              {confirmar ? (
                <div style={{ display: "flex", gap: 8 }}>
                  <button type="button" className="botao botao--perigo" onClick={reemitir} disabled={reemitindo}>
                    {reemitindo ? <LoaderCircle className="girando" /> : <RefreshCw />}Confirmar reemissão
                  </button>
                  <button type="button" className="botao botao--fantasma" onClick={() => setConfirmar(false)}>Cancelar</button>
                </div>
              ) : (
                <button type="button" className="botao" onClick={() => setConfirmar(true)}><RefreshCw />Reemitir crachá</button>
              )}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
