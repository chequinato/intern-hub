"""Schemas Pydantic - validacao do que entra e do que sai da API.

Modulo dono (base): Pedro Ribeiro (Desenvolvedor 1 - fundacao).
Os proximos devs ADICIONAM schemas aqui, seguindo o mesmo padrao:
um *Create para o payload de entrada e um *Response para a saida.

Por que existe: a rota nunca confia no que o cliente mandou. O Pydantic
rejeita nome vazio ou meta negativa antes de qualquer coisa chegar no banco,
e o FastAPI devolve 422 sozinho com a explicacao do erro.
"""

from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from modelos.configuracao import (
    LIMITE_ALERTA_NEGATIVO_PADRAO,
    META_HORAS_DIARIA_PADRAO,
    META_HORAS_SEMANAL_PADRAO,
    PRAZO_VENCIMENTO_MESES_PADRAO,
)


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

        So validamos a ordem entre os horarios que vieram preenchidos - assim
        um registro com pendencia (almoco faltando) continua passando.
        """
        if self.saida is not None and self.saida <= self.entrada:
            raise ValueError("a saida precisa ser depois da entrada")

        if self.saida_almoco is not None and self.saida_almoco <= self.entrada:
            raise ValueError("a saida para o almoco precisa ser depois da entrada")

        if (
            self.saida_almoco is not None
            and self.retorno_almoco is not None
            and self.retorno_almoco <= self.saida_almoco
        ):
            raise ValueError("o retorno do almoco precisa ser depois da saida")

        if self.saida is not None and self.retorno_almoco is not None and (
            self.retorno_almoco >= self.saida
        ):
            raise ValueError("o retorno do almoco precisa ser antes da saida")

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
