// Simbolo do InternHub: um relogio cujo ponteiro e um "check" - bater o
// ponto e ter as horas em dia. Desenhado a mao em SVG (sem imagem externa).
export function Logo({ tamanho = 32 }) {
  return (
    <span className="marca-simbolo" style={{ width: tamanho, height: tamanho }} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="8.5" />
        <path d="M8.2 12.4l2.6 2.5 5-5.6" />
      </svg>
    </span>
  );
}
