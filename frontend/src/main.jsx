import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Fontes empacotadas no projeto (npm), sem depender de internet na hora
// da apresentacao.
import "@fontsource-variable/geist";
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
