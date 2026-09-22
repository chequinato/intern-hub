import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { SessaoProvider } from "./context/SessaoContext";
import { Layout } from "./components/Layout";
import { Portal } from "./paginas/Portal";
import { EstagiarioArea } from "./paginas/EstagiarioArea";
import { Registro } from "./paginas/Registro";
import { Saldo } from "./paginas/Saldo";
import { Relatorio } from "./paginas/Relatorio";
import { Simulacao } from "./paginas/Simulacao";
import { Solicitacoes } from "./paginas/Solicitacoes";
import { Auditoria } from "./paginas/Auditoria";
import { Assistente } from "./paginas/Assistente";
import { GestorArea } from "./paginas/GestorArea";
import { Aprovacoes } from "./paginas/Aprovacoes";

// Mapa de rotas do InternHub. A tela inicial (Portal) fica fora do Layout
// com trilho - so depois de escolher "quem e voce" (estagiario ou gestor)
// e que a navegacao lateral e as abas aparecem.
export default function App() {
  return (
    <SessaoProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Portal />} />

          <Route element={<Layout />}>
            <Route path="/estagiario/:id" element={<EstagiarioArea />}>
              <Route index element={<Registro />} />
              <Route path="saldo" element={<Saldo />} />
              <Route path="relatorio" element={<Relatorio />} />
              <Route path="simulacao" element={<Simulacao />} />
              <Route path="solicitacoes" element={<Solicitacoes />} />
              <Route path="auditoria" element={<Auditoria />} />
              <Route path="assistente" element={<Assistente />} />
            </Route>

            <Route path="/gestor/:id" element={<GestorArea />}>
              <Route index element={<Aprovacoes />} />
              <Route path="auditoria" element={<Auditoria />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </SessaoProvider>
  );
}
