import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { SessaoProvider } from "./context/SessaoContext";
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
const Relatorio = carregar(() => import("./paginas/estagiario/Relatorio"), "Relatorio");
const Simulacao = carregar(() => import("./paginas/estagiario/Simulacao"), "Simulacao");
const Assistente = carregar(() => import("./paginas/estagiario/Assistente"), "Assistente");
const Configuracoes = carregar(() => import("./paginas/estagiario/Configuracoes"), "Configuracoes");
const Equipe = carregar(() => import("./paginas/gestor/Equipe"), "Equipe");
const Aprovacoes = carregar(() => import("./paginas/gestor/Aprovacoes"), "Aprovacoes");
const Feriados = carregar(() => import("./paginas/gestor/Feriados"), "Feriados");
const Auditoria = carregar(() => import("./paginas/gestor/Auditoria"), "Auditoria");

const tela = (Componente) => (
  <Suspense fallback={<CarregandoPagina />}>
    <Componente />
  </Suspense>
);

// Mapa de rotas. O id da pessoa fica no endereco (/estagiario/1/ponto),
// entao da para recarregar a pagina ou mandar o link sem perder a tela.
export default function App() {
  return (
    <SessaoProvider>
      <NotificacoesProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Portal />} />

            <Route path="/estagiario/:id" element={<EstagiarioArea />}>
              <Route index element={tela(Inicio)} />
              <Route path="ponto" element={tela(Ponto)} />
              <Route path="solicitacoes" element={tela(Solicitacoes)} />
              <Route path="relatorio" element={tela(Relatorio)} />
              <Route path="simulacao" element={tela(Simulacao)} />
              <Route path="assistente" element={tela(Assistente)} />
              <Route path="configuracoes" element={tela(Configuracoes)} />
              {/* Enderecos da Entrega 2, que viraram parte de outras telas. */}
              <Route path="saldo" element={<Navigate to=".." relative="path" replace />} />
              <Route path="auditoria" element={<Navigate to="../solicitacoes" relative="path" replace />} />
            </Route>

            <Route path="/gestor/:id" element={<GestorArea />}>
              <Route index element={tela(Equipe)} />
              <Route path="aprovacoes" element={tela(Aprovacoes)} />
              <Route path="feriados" element={tela(Feriados)} />
              <Route path="auditoria" element={tela(Auditoria)} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </NotificacoesProvider>
    </SessaoProvider>
  );
}
