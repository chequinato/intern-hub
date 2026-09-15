"""Paginas do dashboard (Streamlit).

Cada pagina e um CLIENTE HTTP PURO: fala com a API atraves de cliente_api.py
e nunca importa modelos/, servicos/ ou banco/ diretamente (decisao fechada,
README secao 7).

Contrato entre o menu (app.py) e as telas: toda pagina expoe uma funcao
`mostrar(estagiario_id)`. As excecoes sao aprovacoes.py, que recebe o
gestor_id, e auditoria.py, que aceita chamada sem parametro (visao do gestor).

Donos:
    Gustavo Legieri (3.2):  registro.py, saldo.py
    Pietro Paruci   (3.3):  relatorio.py, simulacao.py
    Pedro Henrique  (3.4):  solicitacoes.py, aprovacoes.py, auditoria.py,
                            cliente_api.py
"""
