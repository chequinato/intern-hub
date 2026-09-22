"""servicos/exportar_pdf.py

Comprovante em PDF de uma solicitacao de ajuste especifica (funcionalidade
18 do README). Modulo dono: Arthur Linhares (Desenvolvedor 5, secao 3.5).

Trabalha direto em cima do modelo SQLAlchemy (SolicitacaoAjuste), e nao do
schema Pydantic da API: um servico nao deveria depender de api/schemas.py -
a dependencia e o contrario, schemas.py que descreve o que sai do banco.
Os dados vem das relationships ja existentes no modelo (registro,
estagiario, gestor), sem precisar de nenhuma query nova.

Nao confundir com servicos/exportar_relatorio.py: aquele exporta o resumo
do MES inteiro (funcionalidade 9); este aqui e o comprovante de UMA
solicitacao so (funcionalidade 18).
"""

from datetime import datetime

from fpdf import FPDF

from modelos import SolicitacaoAjuste

_NOMES_CAMPO = {
    "entrada": "Entrada",
    "saida": "Saída",
    "saida_almoco": "Saída para almoço",
    "retorno_almoco": "Retorno do almoço",
}

_NOMES_STATUS = {
    "pendente": "Pendente",
    "aprovado": "Aprovado",
    "rejeitado": "Rejeitado",
}


def gerar_pdf_solicitacao(solicitacao: SolicitacaoAjuste) -> bytes:
    """Gera o comprovante em PDF de uma solicitação de ajuste.

    Não recalcula nada: só formata em PDF os dados que já estão na
    solicitação e nas relações dela (registro, estagiário, gestor).
    Devolve os bytes do PDF, prontos pra rota devolver como arquivo
    (Response(content=..., media_type="application/pdf")).
    """
    registro = solicitacao.registro
    horario_atual = getattr(registro, solicitacao.campo_alterado)
    nome_campo = _NOMES_CAMPO.get(solicitacao.campo_alterado, solicitacao.campo_alterado)
    nome_status = _NOMES_STATUS.get(solicitacao.status, solicitacao.status)

    pdf = FPDF(format="A4")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    _linha(pdf, "InternHub - Comprovante de Solicitação de Ajuste", altura=10)

    pdf.set_font("Helvetica", "", 9)
    texto_cabecalho = (
        f"Solicitação #{solicitacao.id}  |  gerado em "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    _linha(pdf, texto_cabecalho)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    _linha(pdf, "Dados do estagiário", altura=8)
    pdf.set_font("Helvetica", "", 11)
    _linha(pdf, f"Nome: {solicitacao.estagiario.nome}")
    _linha(pdf, f"Data do registro: {registro.data.strftime('%d/%m/%Y')}")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    _linha(pdf, "Ajuste solicitado", altura=8)
    pdf.set_font("Helvetica", "", 11)
    _linha(pdf, f"Campo: {nome_campo}")
    _linha(pdf, "Horário atual: " + (
        horario_atual.strftime("%H:%M") if horario_atual is not None else "(não preenchido)"
    ))
    _linha(pdf, f"Horário sugerido: {solicitacao.horario_sugerido.strftime('%H:%M')}")
    pdf.multi_cell(0, 7, f"Justificativa: {solicitacao.justificativa}")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    _linha(pdf, "Status", altura=8)
    pdf.set_font("Helvetica", "", 11)
    _linha(pdf, f"Situação: {nome_status}")
    _linha(pdf, f"Pedido em: {solicitacao.data_solicitacao.strftime('%d/%m/%Y %H:%M')}")
    if solicitacao.data_resposta is not None:
        _linha(pdf, f"Respondido em: {solicitacao.data_resposta.strftime('%d/%m/%Y %H:%M')}")
    if solicitacao.gestor is not None:
        _linha(pdf, f"Gestor responsável: {solicitacao.gestor.nome}")

    return bytes(pdf.output())


def _linha(pdf: FPDF, texto: str, altura: int = 7) -> None:
    """Escreve uma linha e já pula pra próxima.

    Evita repetir cell()+ln() toda hora, e evita o parâmetro ln= do
    cell(), que está deprecated nas versões recentes do fpdf2.
    """
    pdf.cell(0, altura, texto)
    pdf.ln(altura)
