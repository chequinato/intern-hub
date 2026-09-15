"""Schemas Pydantic - validacao do que entra e do que sai da API.

Modulo dono (base): Pedro Ribeiro (Desenvolvedor 1 - fundacao).
Os proximos devs ADICIONAM schemas aqui, seguindo o mesmo padrao:
um *Create para o payload de entrada e um *Response para a saida.

Por que existe: a rota nunca confia no que o cliente mandou. O Pydantic
rejeita nome vazio ou meta negativa antes de qualquer coisa chegar no banco,
e o FastAPI devolve 422 sozinho com a explicacao do erro.
"""

from datetime import date, datetime, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from modelos.configuracao import (
    LIMITE_ALERTA_NEGATIVO_PADRAO,
    META_HORAS_DIARIA_PADRAO,
    META_HORAS_SEMANAL_PADRAO,
    PRAZO_VENCIMENTO_MESES_PADRAO,
)
from modelos.solicitacao_ajuste import (
    CAMPOS_AJUSTAVEIS,
    STATUS_APROVADO,
    STATUS_REJEITADO,
)
from servicos.calculo import validar_ordem_dos_horarios


class ConfiguracaoCreate(BaseModel):
    """Metas e limites enviados na criacao de um estagiario."""

    meta_horas_diaria: float = Field(default=META_HORAS_DIARIA_PADRAO, gt=0, le=24)
    meta_horas_semanal: float = Field(default=META_HORAS_SEMANAL_PADRAO, gt=0, le=168)
    limite_alerta_negativo: float = Field(default=LIMITE_ALERTA_NEGATIVO_PADRAO, le=0)
    prazo_vencimento_meses: int = Field(default=PRAZO_VENCIMENTO_MESES_PADRAO, ge=1)


class ConfiguracaoResponse(ConfiguracaoCreate):
    """Configuracao como ela sai da API, ja com os ids do banco."""

    # from_attributes: permite devolver o objeto do SQLAlchemy direto da rota,
    # sem converter campo por campo na mao.
    model_config = ConfigDict(from_attributes=True)

    id: int
    estagiario_id: int


class EstagiarioCreate(BaseModel):
    """Payload de POST /estagiarios: nome + meta de horas."""

    nome: str = Field(min_length=2, max_length=120)
    meta_horas_diaria: float = Field(default=META_HORAS_DIARIA_PADRAO, gt=0, le=24)
    meta_horas_semanal: float = Field(default=META_HORAS_SEMANAL_PADRAO, gt=0, le=168)
    gestor_id: int | None = None

    @field_validator("nome")
    @classmethod
    def _sem_espacos_nas_pontas(cls, valor: str) -> str:
        """Impede que '   ' passe pelo min_length e vire um nome em branco."""
        nome = valor.strip()
        if len(nome) < 2:
            raise ValueError("nome precisa ter pelo menos 2 caracteres")
        return nome


class EstagiarioResponse(BaseModel):
    """Estagiario como ele sai da API, com a configuracao junto."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    gestor_id: int | None = None
    configuracao: ConfiguracaoResponse | None = None


# --- Registro de ponto e saldo -----------------------------------------------
# Parte do Gustavo Legieri (secao 3.2). Segue o padrao da fundacao: um *Create
# para o payload de entrada e um *Response para a saida.


class RegistroCreate(BaseModel):
    """Payload de POST /registros: o ponto de um dia.

    entrada e obrigatoria; os demais horarios nascem opcionais. Um dia que
    chega sem saida_almoco/retorno_almoco (mas com saida) e aceito e salvo -
    ele apenas volta marcado como pendencia (README secao 7).
    """

    estagiario_id: int
    data: date
    entrada: time
    saida: time | None = None
    saida_almoco: time | None = None
    retorno_almoco: time | None = None

    @model_validator(mode="after")
    def _horarios_em_ordem(self) -> "RegistroCreate":
        """Barra horarios logicamente impossiveis antes de chegarem no banco.

        A regra em si mora em servicos/calculo.py, e nao aqui, porque a
        aprovacao de uma solicitacao de ajuste (Pedro Henrique, secao 3.4)
        precisa aplicar exatamente a mesma checagem. Duas copias da regra
        acabariam divergindo na primeira correcao.
        """
        problema = validar_ordem_dos_horarios(
            self.entrada, self.saida, self.saida_almoco, self.retorno_almoco
        )
        if problema is not None:
            raise ValueError(problema)
        return self


class RegistroResponse(BaseModel):
    """Registro como ele sai da API, ja com o calculo do dia junto.

    horas_trabalhadas e pendencia nao ficam no banco: sao calculados na hora
    (servicos/calculo.py) e anexados aqui para a tela nao precisar recalcular.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    estagiario_id: int
    data: date
    entrada: time
    saida: time | None = None
    saida_almoco: time | None = None
    retorno_almoco: time | None = None
    horas_trabalhadas: float
    pendencia: bool
    aviso: str | None = None


class SaldoResponse(BaseModel):
    """Saldo acumulado de um estagiario, com o estado do alerta."""

    estagiario_id: int
    saldo_acumulado: float
    em_alerta: bool
    limite_alerta: float
    dias_registrados: int


# --- Feriados, simulacao e relatorio ------------------------------------------
# Parte do Pietro Paruci (secao 3.3).


class FeriadoCreate(BaseModel):
    """Payload de POST /feriados: um dia nao util."""

    data: date
    descricao: str = Field(min_length=2, max_length=120)


class FeriadoResponse(FeriadoCreate):
    """Feriado como ele sai da API."""

    # from_attributes e o nome atual do antigo orm_mode (que era Pydantic 1 e
    # nao tem mais efeito no Pydantic 2, usado por este projeto).
    model_config = ConfigDict(from_attributes=True)

    id: int

# Schemas para Simulação
class SimulacaoRequest(BaseModel):
    estagiario_id: int
    dias_falta: int
    horas_atraso: float = 0.0

class SimulacaoResponse(BaseModel):
    saldo_atual: float
    saldo_projetado: float
    impacto_horas: float

# Schemas para Relatório
class RelatorioDiario(BaseModel):
    data: date
    horas_trabalhadas: float
    saldo_do_dia: float

class RelatorioMensalResponse(BaseModel):
    mes: int
    ano: int
    total_horas_trabalhadas: float
    dias_uteis_trabalhados: int
    faltas: int
    saldo_acumulado: float
    aviso_vencimento: Optional[str] = None
    evolucao_diaria: List[RelatorioDiario]

# --- Gestor, solicitacoes de ajuste e auditoria -------------------------------
# Parte do Pedro Henrique (secao 3.4). Mesmo padrao da fundacao: um *Create
# para o payload de entrada e um *Response para a saida.


class GestorCreate(BaseModel):
    """Payload de POST /gestores: so o nome de quem vai aprovar os ajustes."""

    nome: str = Field(min_length=2, max_length=120)

    @field_validator("nome")
    @classmethod
    def _sem_espacos_nas_pontas(cls, valor: str) -> str:
        nome = valor.strip()
        if len(nome) < 2:
            raise ValueError("nome precisa ter pelo menos 2 caracteres")
        return nome


class GestorResponse(BaseModel):
    """Gestor como ele sai da API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class EstagiarioGestorUpdate(BaseModel):
    """Payload de PATCH /estagiarios/{id}: troca o gestor responsavel.

    Aceita null de proposito - e assim que se desvincula um estagiario de um
    gestor sem precisar de uma rota separada so para isso.
    """

    gestor_id: int | None = None


class SolicitacaoCreate(BaseModel):
    """Payload de POST /solicitacoes: qual horario corrigir, e por que.

    Nao existe estagiario_id aqui: a API descobre de quem e o pedido olhando
    o registro (servicos/solicitacao.py). Um campo a menos no payload e um
    jeito a menos de pedir ajuste no ponto dos outros.
    """

    registro_id: int
    campo_alterado: str
    horario_sugerido: time
    justificativa: str = Field(min_length=5, max_length=300)

    @field_validator("campo_alterado")
    @classmethod
    def _campo_permitido(cls, valor: str) -> str:
        """So os quatro horarios do RegistroPonto podem ser ajustados."""
        if valor not in CAMPOS_AJUSTAVEIS:
            raise ValueError(
                f"campo_alterado precisa ser um entre: {', '.join(CAMPOS_AJUSTAVEIS)}"
            )
        return valor

    @field_validator("justificativa")
    @classmethod
    def _justificativa_de_verdade(cls, valor: str) -> str:
        """Impede que cinco espacos em branco passem pelo min_length."""
        texto = valor.strip()
        if len(texto) < 5:
            raise ValueError("escreva uma justificativa com pelo menos 5 caracteres")
        return texto


class SolicitacaoResponse(BaseModel):
    """Solicitacao como ela sai da API.

    Alem dos campos da tabela, carrega tres dados montados na hora pela rota:
    o nome do estagiario, a data do registro e o horario que esta la HOJE.
    Sem eles, a tela do gestor teria que fazer uma requisicao a mais por
    solicitacao so para conseguir escrever "de 13:00 para 14:00".
    """

    id: int
    registro_id: int
    estagiario_id: int
    estagiario_nome: str
    data_registro: date
    campo_alterado: str
    horario_atual: time | None = None
    horario_sugerido: time
    justificativa: str
    status: str
    data_solicitacao: datetime
    data_resposta: datetime | None = None
    gestor_id: int | None = None
    gestor_nome: str | None = None


class SolicitacaoDecisao(BaseModel):
    """Payload de PATCH /solicitacoes/{id}: a decisao do gestor."""

    status: str
    gestor_id: int

    @field_validator("status")
    @classmethod
    def _decisao_valida(cls, valor: str) -> str:
        """Um PATCH so pode aprovar ou rejeitar - nao da para 'despendenciar'."""
        decisoes = (STATUS_APROVADO, STATUS_REJEITADO)
        if valor not in decisoes:
            raise ValueError(f"status precisa ser {STATUS_APROVADO} ou {STATUS_REJEITADO}")
        return valor


class SolicitacaoDecisaoResponse(BaseModel):
    """Resposta do PATCH: o pedido ja respondido e o efeito da decisao.

    saldo_acumulado so vem preenchido na aprovacao - rejeitar nao mexe no
    registro, entao o saldo continua o mesmo e nao ha o que recalcular.
    """

    solicitacao: SolicitacaoResponse
    saldo_acumulado: float | None = None
    mensagem: str
