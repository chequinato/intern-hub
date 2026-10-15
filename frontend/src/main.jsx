import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Fontes empacotadas no projeto (npm), sem depender de internet na hora
// da apresentacao. Em Mac/iPhone o tema usa a SF Pro do sistema; a Inter
// (a mais parecida com ela) entra no Windows e no Linux.
import "@fontsource-variable/inter";
import "@fontsource-variable/geist-mono";
import "./estilos/tema.css";
import "./estilos/base.css";
import "./estilos/componentes.css";
import "./estilos/estrutura.css";
import "./estilos/telas.css";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
