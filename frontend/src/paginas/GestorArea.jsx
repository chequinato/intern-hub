import { useParams } from "react-router-dom";
import { CalendarX2, ClipboardCheck, History, Users } from "lucide-react";
import { api } from "../api/cliente";
import { useApiState } from "../useApiState";
import { Estrutura } from "../components/Estrutura";
import { CarregandoPagina, ErroCarregar } from "../components/Ui";

// Area do gestor: visao da equipe, fila de aprovacoes, feriados e
// auditoria. O painel da equipe (GET /painel/gestor/{id}) alimenta o
// contador de pedidos na barra lateral.
export function GestorArea() {
  const { id } = useParams();
  const gestorId = Number(id);

  const gestor = useApiState(
    () => api.get("/gestores").then((lista) => {
      const encontrado = lista.find((g) => g.id === gestorId);
      if (!encontrado) throw new Error(`Gestor ${gestorId} não encontrado.`);
      return encontrado;
    }),
    [gestorId]
  );
  const painel = useApiState(() => api.get(`/painel/gestor/${gestorId}`), [gestorId]);

  if (gestor.erro) {
    return <div className="conteudo"><ErroCarregar mensagem={gestor.erro} aoTentar={gestor.recarregar} /></div>;
  }
  if (!gestor.dados) {
    return <div className="conteudo"><CarregandoPagina /></div>;
  }

  const itens = [
    { rota: "", rotulo: "Equipe", titulo: "Visão da equipe", icone: Users, grupo: "Visão geral" },
    { rota: "aprovacoes", rotulo: "Aprovações", titulo: "Fila de aprovações", icone: ClipboardCheck, grupo: "Gestão", contador: painel.dados?.pedidos_na_fila },
    { rota: "feriados", rotulo: "Feriados", titulo: "Calendário de feriados", icone: CalendarX2, grupo: "Gestão" },
    { rota: "auditoria", rotulo: "Auditoria", titulo: "Histórico de pedidos", icone: History, grupo: "Gestão" },
  ];

  const contexto = {
    gestor: gestor.dados,
    gestorId,
    painel: painel.dados,
    painelErro: painel.erro,
    recarregar: painel.recarregar,
  };

  return (
    <Estrutura
      base={`/gestor/${gestorId}`}
      pessoa={gestor.dados.nome}
      papel="Gestor"
      itens={itens}
      contexto={contexto}
    />
  );
}
