import { useOutletContext } from "react-router-dom";
import { Lock } from "lucide-react";
import { useSessao } from "../../context/SessaoContext";
import { TrocarSenha } from "../../components/TrocarSenha";
import { formatarHoras } from "../../utils/formato";

// Meta, limites e conta do estagiario.
//
// Ate a Entrega 3 o proprio estagiario editava a meta aqui. Com o login, a
// meta passou a ser alterada so pelo gestor responsavel (na tela Equipe):
// ela e contratual, e quem pudesse baixar a propria meta ganharia saldo sem
// trabalhar. Aqui o estagiario ve os valores e troca a propria senha.
export function Configuracoes() {
  const { estagiario } = useOutletContext();
  const { usuario } = useSessao();
  const c = estagiario.configuracao || {};

  const linhas = [
    ["Meta por dia", formatarHoras(c.meta_horas_diaria ?? 6)],
    ["Meta por semana", formatarHoras(c.meta_horas_semanal ?? 30, 0)],
    ["Máximo legal por dia", formatarHoras(c.limite_maximo_diario ?? 6)],
    ["Máximo legal por semana", formatarHoras(c.limite_maximo_semanal ?? 30, 0)],
    ["Alerta de saldo negativo", formatarHoras(c.limite_alerta_negativo ?? -5)],
    ["Crédito vence em", `${c.prazo_vencimento_meses ?? 2} meses`],
  ];

  return (
    <>
      <div className="cabecalho-pagina entra">
        <div>
          <h1>Meta, limites e senha</h1>
          <p>A meta é o que você deve cumprir; o limite legal é o que você não pode passar.</p>
        </div>
      </div>

      <div className="grade grade-2">
        <section className="cartao entra" style={{ "--i": 1 }}>
          <div className="cartao-cabeca">
            <h2>Contrato de estágio</h2>
            <span className="sub"><Lock size={12} style={{ display: "inline", verticalAlign: "-1px" }} /> definido pelo gestor</span>
          </div>
          <ul className="lista-regras cartao-corpo">
            {linhas.map(([rotulo, valor]) => (
              <li key={rotulo}><span>{rotulo}</span><b className="numero">{valor}</b></li>
            ))}
          </ul>
          <div className="cartao-rodape texto-3" style={{ fontSize: 12.5 }}>
            Em dia de prova cadastrado na agenda, a meta do dia cai pela metade (Lei 11.788/2008, art. 10).
          </div>
        </section>

        <div className="pilha">
          <section className="cartao entra" style={{ "--i": 2 }}>
            <div className="cartao-cabeca"><h2>Conta</h2></div>
            <ul className="lista-regras cartao-corpo">
              <li><span>E-mail de acesso</span><b>{usuario?.email}</b></li>
              <li><span>Gestor responsável</span><b>{estagiario.gestor_id ? "vinculado" : "nenhum ainda"}</b></li>
            </ul>
            <div className="cartao-rodape texto-3" style={{ fontSize: 12.5 }}>
              Para mudar a meta ou o gestor, fale com o gestor responsável (ou abra um chamado).
            </div>
          </section>
          <TrocarSenha i={3} />
        </div>
      </div>
    </>
  );
}
