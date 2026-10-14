// Caixinha que aparece ao passar o mouse num grafico (recharts). O recharts
// entrega `payload` com os valores do ponto; `linhas` diz como mostrar cada um.

export function DicaGrafico({ active, payload, label, titulo, linhas }) {
  if (!active || !payload || payload.length === 0) return null;
  const ponto = payload[0].payload;
  return (
    <div className="dica-grafico">
      <div className="titulo">{titulo ? titulo(ponto, label) : label}</div>
      {linhas.map(({ rotulo, valor }) => (
        <div key={rotulo} className="linha">
          <span>{rotulo}</span>
          <b>{valor(ponto)}</b>
        </div>
      ))}
    </div>
  );
}
