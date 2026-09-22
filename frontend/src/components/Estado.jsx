const ROTULOS = { pendente: "Pendente", aprovado: "Aprovado", rejeitado: "Rejeitado" };

// Selo de status de uma solicitacao de ajuste (pendente/aprovado/rejeitado).
export function Estado({ status }) {
  return (
    <span className={`state state--${status}`}>
      <i />
      {ROTULOS[status] || status}
    </span>
  );
}
