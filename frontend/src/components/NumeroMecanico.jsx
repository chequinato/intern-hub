// Numero que "rola" como um contador mecanico quando o valor muda, no
// lugar de so trocar de texto - e o gesto de movimento reservado para
// numeros no sistema visual do projeto (README de design, vero-webhook).
// Cada digito e uma janela de altura fixa (.od-col) com uma faixa vertical
// (.od-strip) que desliza ate mostrar o digito certo.

export function NumeroMecanico({ valor, casasDecimais = 0, prefixo = "", sufixo = "" }) {
  const texto = Number(valor ?? 0).toFixed(casasDecimais);

  return (
    <span className="od">
      {prefixo && <span className="od-fixed">{prefixo}</span>}
      {texto.split("").map((caractere, indice) => (
        <Digito key={indice} caractere={caractere} />
      ))}
      {sufixo && <span className="od-fixed">{sufixo}</span>}
    </span>
  );
}

function Digito({ caractere }) {
  // Sinal, ponto decimal etc nao rolam - so os algarismos 0-9 tem tira.
  if (!/[0-9]/.test(caractere)) {
    return <span className="od-fixed">{caractere}</span>;
  }

  const digito = Number(caractere);
  return (
    <span className="od-col">
      <span className="od-strip" style={{ transform: `translateY(-${digito * 1.06}em)` }}>
        {Array.from({ length: 10 }, (_, n) => (
          <span key={n}>{n}</span>
        ))}
      </span>
    </span>
  );
}
