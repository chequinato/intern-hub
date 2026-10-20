// Faz o navegador baixar um arquivo que veio da API (PDF, Excel, .ics).
export function baixarBlob(blob, nomeDoArquivo) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = nomeDoArquivo;
  link.click();
  URL.revokeObjectURL(url);
}
