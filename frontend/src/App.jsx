import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes, useParams } from "react-router-dom";
import { areaDoUsuario, SessaoProvider, useSessao } from "./context/SessaoContext";
import { NotificacoesProvider } from "./components/Notificacoes";
import { CarregandoPagina } from "./components/Ui";
import { Portal } from "./paginas/Portal";
import { EstagiarioArea } from "./paginas/EstagiarioArea";
import { GestorArea } from "./paginas/GestorArea";

// Cada tela e carregada so quando a pessoa entra nela (lazy): o navegador
// nao baixa os graficos do relatorio para quem so abriu o portal. Antes da
// Entrega 3 o frontend inteiro vinha num arquivo so de ~650 kB.
const carregar = (importar, nome) => lazy(() => importar().then((m) => ({ default: m[nome] })));

const Inicio = carregar(() => import("./paginas/estagiario/Inicio"), "Inicio");
const Ponto = carregar(() => import("./paginas/estagiario/Ponto"), "Ponto");
const Solicitacoes = carregar(() => import("./paginas/estagiario/Solicitacoes"), "Solicitacoes");
const Chamados = carregar(() => import("./paginas/estagiario/Chamados"), "Chamados");
const Agenda = carregar(() => import("./paginas/estagiario/Agenda"), "Agenda");
const Estagio = carregar(() => import("./paginas/estagiario/Estagio"), "Estagio");
const Atividades = carregar(() => import("./paginas/estagiario/Atividades"), "Atividades");
const Relatorio = carregar(() => import("./paginas/estagiario/Relatorio"), "Relatorio");
const Simulacao = carregar(() => import("./paginas/estagiario/Simulacao"), "Simulacao");
const Assistente = carregar(() => import("./paginas/estagiario/Assistente"), "Assistente");
const Cracha = carregar(() => import("./paginas/estagiario/Cracha"), "Cracha");
const Configuracoes = carregar(() => import("./paginas/estagiario/Configuracoes"), "Configuracoes");
const Equipe = carregar(() => import("./paginas/gestor/Equipe"), "Equipe");
const Aprovacoes = carregar(() => import("./paginas/gestor/Aprovacoes"), "Aprovacoes");
const ChamadosEquipe = carregar(() => import("./paginas/gestor/ChamadosEquipe"), "ChamadosEquipe");
const RelatoriosEquipe = carregar(() => import("./paginas/gestor/RelatoriosEquipe"), "RelatoriosEquipe");
const Feriados = carregar(() => import("./paginas/gestor/Feriados"), "Feriados");
const Auditoria = carregar(() => import("./paginas/gestor/Auditoria"), "Auditoria");
const ContaGestor = carregar(() => import("./paginas/gestor/ContaGestor"), "ContaGestor");
const VerificarCracha = carregar(() => import("./paginas/VerificarCracha"), "VerificarCracha");

const tela = (Componente) => (
  <Suspense fallback={<CarregandoPagina />}>
    <Componente />
  </Suspense>
);

// Porta de cada area (Entrega 3): sem login, volta para a tela de entrada;
// logado com outro perfil ou com outro id no endereco, vai para a propria
// area. Quem garante de verdade e a API (403) - isto so evita a pessoa cair
// numa tela que nao vai conseguir carregar.
function SoParaQuemPode({ perfil, children }) {
  const { usuario, logado, conferindo } = useSessao();
  const { id } = useParams();
  if (conferindo) return <div className="conteudo"><CarregandoPagina /></div>;
  if (!logado) return <Navigate to="/" replace />;
  const idDaConta = perfil === "gestor" ? usuario.gestor_id : usuario.estagiario_id;
  if (usuario.perfil !== perfil || Number(id) !== idDaConta) {
    return <Navigate to={areaDoUsuario(usuario)} replace />;
  }
  return children;
}

// Mapa de rotas. O id da pessoa fica no endereco (/estagiario/1/ponto),
// entao da para recarregar a pagina sem perder a tela.
export default function App() {
  return (
    <SessaoProvider>
      <NotificacoesProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Portal />} />
            {/* Publica: e o endereco que o QR code do cracha abre. */}
            <Route path="/verificar/:codigo" element={tela(VerificarCracha)} />

            <Route path="/estagiario/:id" element={<SoParaQuemPode perfil="estagiario"><EstagiarioArea /></SoParaQuemPode>}>
              <Route index element={tela(Inicio)} />
              <Route path="ponto" element={tela(Ponto)} />
              <Route path="agenda" element={tela(Agenda)} />
              <Route path="solicitacoes" element={tela(Solicitacoes)} />
              <Route path="chamados" element={tela(Chamados)} />
              <Route path="estagio" element={tela(Estagio)} />
              <Route path="atividades" element={tela(Atividades)} />
              <Route path="relatorio" element={tela(Relatorio)} />
              <Route path="simulacao" element={tela(Simulacao)} />
              <Route path="assistente" element={tela(Assistente)} />
              <Route path="cracha" element={tela(Cracha)} />
              <Route path="configuracoes" element={tela(Configuracoes)} />
              {/* Enderecos da Entrega 2, que viraram parte de outras telas. */}
              <Route path="saldo" element={<Navigate to=".." relative="path" replace />} />
              <Route path="auditoria" element={<Navigate to="../solicitacoes" relative="path" replace />} />
            </Route>

            <Route path="/gestor/:id" element={<SoParaQuemPode perfil="gestor"><GestorArea /></SoParaQuemPode>}>
              <Route index element={tela(Equipe)} />
              <Route path="aprovacoes" element={tela(Aprovacoes)} />
              <Route path="chamados" element={tela(ChamadosEquipe)} />
              <Route path="relatorios" element={tela(RelatoriosEquipe)} />
              <Route path="feriados" element={tela(Feriados)} />
              <Route path="auditoria" element={tela(Auditoria)} />
              <Route path="conta" element={tela(ContaGestor)} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </NotificacoesProvider>
    </SessaoProvider>
  );
}
