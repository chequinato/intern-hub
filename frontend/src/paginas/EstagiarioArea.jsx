import { useParams } from "react-router-dom";
import {
  Calculator, ChartColumnBig, Clock, FileText, LayoutDashboard, MessageCircle, Settings,
} from "lucide-react";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { Estrutura } from "../components/Estrutura";
import { CarregandoPagina, ErroCarregar } from "../components/Ui";

// Area do estagiario: busca a pessoa e o painel (GET /painel/estagiario/{id})
// uma vez aqui e entrega para as telas pelo contexto da rota. O painel
// tambem alimenta os contadores da barra lateral (pendencias sem pedido).
export function EstagiarioArea() {
  const { id } = useParams();
  const estagiarioId = Number(id);

  const pessoa = useApiState(() => api.get(`/estagiarios/${estagiarioId}`), [estagiarioId]);
  const painel = useApiState(() => api.get(`/painel/estagiario/${estagiarioId}`), [estagiarioId]);

  if (pessoa.erro) {
    return <div className="conteudo"><ErroCarregar mensagem={pessoa.erro} aoTentar={pessoa.recarregar} /></div>;
  }
  if (!pessoa.dados) {
    return <div className="conteudo"><CarregandoPagina /></div>;
  }

  const pendenciasSemPedido = (painel.dados?.pendencias || []).filter((p) => !p.pedido_aberto).length;

  const itens = [
    { rota: "", rotulo: "Início", titulo: "Painel", icone: LayoutDashboard, grupo: "Visão geral" },
    { rota: "ponto", rotulo: "Ponto", titulo: "Registro de ponto", icone: Clock, grupo: "Dia a dia" },
    { rota: "solicitacoes", rotulo: "Solicitações", titulo: "Pedidos de ajuste", icone: FileText, grupo: "Dia a dia", contador: pendenciasSemPedido },
    { rota: "relatorio", rotulo: "Relatório", titulo: "Relatório mensal", icone: ChartColumnBig, grupo: "Análise" },
    { rota: "simulacao", rotulo: "Simulação", titulo: "Simulador de cenários", icone: Calculator, grupo: "Análise" },
    { rota: "assistente", rotulo: "Assistente", titulo: "Assistente de IA", icone: MessageCircle, grupo: "Análise" },
    { rota: "configuracoes", rotulo: "Configurações", titulo: "Meta e limites", icone: Settings, grupo: "Conta" },
  ];

  const contexto = {
    estagiario: pessoa.dados,
    estagiarioId,
    painel: painel.dados,
    painelErro: painel.erro,
    // As telas chamam depois de uma acao (bater ponto, pedir ajuste, mudar
    // a meta) para os numeros e os contadores da lateral se atualizarem.
    recarregar: () => {
      painel.recarregar();
      pessoa.recarregar();
    },
  };

  return (
    <Estrutura
      base={`/estagiario/${estagiarioId}`}
      pessoa={pessoa.dados.nome}
      papel="Estagiário"
      itens={itens}
      contexto={contexto}
    />
  );
}
