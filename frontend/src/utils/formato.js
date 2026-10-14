// Formatacao para a tela: datas em dd/mm/aaaa, horas como "6,5h", nomes
// amigaveis no lugar dos nomes tecnicos da API ("Retorno do almoço" em vez
// de retorno_almoco). Concentrado aqui para todas as telas falarem igual.

export const MESES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];
// "outubro" -> "Outubro" (so a primeira letra; o "de" continua minusculo)
export function nomeDoMes(mes) {
  const nome = MESES[mes - 1];
  return nome.charAt(0).toUpperCase() + nome.slice(1);
}

export const MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const DIAS_SEMANA = ["domingo", "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado"];
const DIAS_CURTOS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];

export const NOMES_CAMPOS = {
  entrada: "Entrada",
  saida_almoco: "Saída para o almoço",
  retorno_almoco: "Retorno do almoço",
  saida: "Saída",
};

// O texto do botao de bater ponto depende de qual marcacao vem a seguir.
export const ACAO_DO_PONTO = {
  entrada: "Registrar entrada",
  saida_almoco: "Sair para o almoço",
  retorno_almoco: "Voltar do almoço",
  saida: "Registrar saída",
};

export const NOMES_STATUS = { pendente: "Pendente", aprovado: "Aprovado", rejeitado: "Rejeitado" };

// "2026-10-13" vira um Date no fuso local. new Date("2026-10-13") sozinho
// interpreta como UTC e, no Brasil, cai no dia anterior.
export function paraData(iso) {
  if (iso instanceof Date) return iso;
  const [ano, mes, dia] = String(iso).slice(0, 10).split("-").map(Number);
  return new Date(ano, mes - 1, dia);
}

export function hojeIso() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function formatarData(iso) {
  if (!iso) return "—";
  const d = paraData(iso);
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
}

export function formatarDataCurta(iso) {
  if (!iso) return "—";
  const d = paraData(iso);
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function diaDaSemana(iso, curto = true) {
  const d = paraData(iso);
  return (curto ? DIAS_CURTOS : DIAS_SEMANA)[d.getDay()];
}

export function dataPorExtenso(data = new Date()) {
  return `${DIAS_SEMANA[data.getDay()]}, ${data.getDate()} de ${MESES[data.getMonth()]}`;
}

export function formatarDataHora(texto) {
  if (!texto) return "—";
  const d = new Date(texto);
  return `${formatarData(d)} às ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

// "09:00:00" -> "09:00"; vazio -> "—"
export function hora(texto) {
  return texto ? String(texto).slice(0, 5) : "—";
}

function decimal(valor, casas) {
  return Number(valor ?? 0).toFixed(casas).replace(".", ",");
}

// 6.5 -> "6,5h"
export function formatarHoras(valor, casas = 1) {
  return `${decimal(valor, casas)}h`;
}

// Saldo com sinal: +2,5h / −1,3h (o "−" e o sinal de menos tipografico).
export function formatarSaldo(valor, casas = 1) {
  const numero = Number(valor ?? 0);
  if (Math.abs(numero) < 0.05 && casas <= 1) return "0,0h";
  const sinal = numero > 0 ? "+" : numero < 0 ? "−" : "";
  return `${sinal}${decimal(Math.abs(numero), casas)}h`;
}

// 6.5 -> "6h30"
export function horasEMinutos(valor) {
  const total = Math.round(Math.abs(Number(valor ?? 0)) * 60);
  const h = Math.floor(total / 60);
  const m = total % 60;
  return m ? `${h}h${String(m).padStart(2, "0")}` : `${h}h`;
}

export function saudacao(data = new Date()) {
  const h = data.getHours();
  if (h < 12) return "Bom dia";
  if (h < 18) return "Boa tarde";
  return "Boa noite";
}

export function primeiroNome(nome = "") {
  return nome.trim().split(/\s+/)[0] || nome;
}

export function iniciais(nome = "") {
  const partes = nome.trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return "?";
  const primeira = partes[0][0];
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : "";
  return (primeira + ultima).toUpperCase();
}

// Cor fixa por pessoa (sempre a mesma para o mesmo nome).
const CORES_AVATAR = ["#0F766E", "#B45309", "#4F46E5", "#BE185D", "#0369A1", "#7C3AED", "#15803D", "#C2410C"];
export function corDoAvatar(nome = "") {
  let soma = 0;
  for (const letra of nome) soma = (soma * 31 + letra.charCodeAt(0)) % 997;
  return CORES_AVATAR[soma % CORES_AVATAR.length];
}

export function plural(n, singular, pluralTexto) {
  return `${n} ${n === 1 ? singular : pluralTexto}`;
}
