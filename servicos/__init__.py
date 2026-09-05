"""Servicos - a logica de negocio do InternHub.

Cada servico e uma funcao pura de regra de negocio (ou uma consulta ao banco).
As rotas da API (api/rotas/) chamam estes servicos; o Streamlit nunca importa
daqui - ele fala com a API por HTTP.

Parte do Gustavo Legieri (secao 3.2): calculo.py e saldo.py.
"""
