// Simbolo do InternHub: uma ampulheta geometrica - o banco de horas. A
// metade de cima, so o contorno, e o tempo passando; a de baixo, cheia, e o
// que ficou acumulado. Desenhado a mao em SVG (sem imagem externa).
//
// Ao aparecer, a metade de baixo "enche" uma vez (scaleY a partir da base).
export function Logo({ tamanho = 32 }) {
  return (
    <span className="marca-simbolo" style={{ width: tamanho, height: tamanho }} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="currentColor" stroke="none">
        {/* tampas de cima e de baixo */}
        <rect x="4.5" y="3" width="15" height="2.4" rx=".6" />
        <rect x="4.5" y="18.6" width="15" height="2.4" rx=".6" />
        {/* metade de cima: contorno (o tempo passando) */}
        <path d="M7 6.6 H17 L12 11.6 Z" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinejoin="round" />
        {/* metade de baixo: cheia (as horas acumuladas) */}
        <path className="logo-areia" d="M12 12.4 L17.2 17.6 H6.8 Z" />
      </svg>
    </span>
  );
}
