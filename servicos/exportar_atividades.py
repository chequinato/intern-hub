"""PDF do relatorio de atividades do semestre (Lei 11.788/2008, art. 9o, VII).

Modulo dono: Miguel (Entrega 3).

E o documento que a empresa envia a faculdade: dados do estagio, horas do
semestre, as atividades registradas, a avaliacao do gestor e as duas
confirmacoes - validado pelo gestor e ciente o estagiario ("com vista
obrigatoria ao estagiario", diz a lei).

Mesmo jeito de servicos/exportar_pdf.py (Arthur): fpdf2, gerado na hora,
sem recalcular nada - so formata o dicionario de resumo_do_semestre().
"""

from datetime import datetime

from fpdf import FPDF


def _data(valor) -> str:
    return valor.strftime("%d/%m/%Y") if valor else "-"


def gerar_pdf_atividades(resumo: dict) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 15)
    _linha(pdf, "Relatório de atividades de estágio", 9)
    pdf.set_font("Helvetica", "", 9)
    _linha(pdf, (
        f"{resumo['semestre']}º semestre de {resumo['ano']}  |  "
        f"{_data(resumo['inicio'])} a {_data(resumo['fim'])}  |  "
        f"gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  Lei 11.788/2008, art. 9º, VII"
    ))
    pdf.ln(4)

    _titulo(pdf, "Estagiário")
    _linha(pdf, f"Nome: {resumo['estagiario_nome']}")
    if resumo.get("instituicao_ensino"):
        _linha(pdf, f"Instituição de ensino: {resumo['instituicao_ensino']}")
    if resumo.get("curso"):
        _linha(pdf, f"Curso: {resumo['curso']}")
    _linha(pdf, f"Horas trabalhadas no semestre: {resumo['horas_trabalhadas']:.2f}h em {resumo['dias_trabalhados']} dia(s)")
    pdf.ln(3)

    _titulo(pdf, f"Atividades registradas ({len(resumo['atividades'])})")
    if not resumo["atividades"]:
        _linha(pdf, "Nenhuma atividade registrada neste semestre.")
    for atividade in resumo["atividades"]:
        pdf.set_font("Helvetica", "B", 10)
        _linha(pdf, _data(atividade.data), 6)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5.5, atividade.descricao)
        pdf.ln(1.5)
    pdf.ln(2)

    _titulo(pdf, "Avaliação do supervisor")
    pdf.multi_cell(0, 6, resumo.get("avaliacao_gestor") or "Ainda não avaliado.")
    pdf.ln(3)

    _titulo(pdf, "Confirmações")
    validado = resumo.get("validado_em")
    _linha(pdf, (
        f"Validado por {resumo.get('gestor_nome') or '-'} em {validado.strftime('%d/%m/%Y %H:%M')}"
        if validado else "Validação do supervisor: pendente"
    ))
    ciente = resumo.get("ciente_em")
    _linha(pdf, (
        f"Ciência do estagiário em {ciente.strftime('%d/%m/%Y %H:%M')}"
        if ciente else "Ciência do estagiário: pendente"
    ))
    return bytes(pdf.output())


def _titulo(pdf: FPDF, texto: str) -> None:
    pdf.set_font("Helvetica", "B", 12)
    _linha(pdf, texto, 8)
    pdf.set_font("Helvetica", "", 11)


def _linha(pdf: FPDF, texto: str, altura: float = 7) -> None:
    """Uma linha e pula para a proxima (igual a servicos/exportar_pdf.py)."""
    pdf.cell(0, altura, texto)
    pdf.ln(altura)
