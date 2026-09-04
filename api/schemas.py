"""Schemas Pydantic - validacao do que entra e do que sai da API.

Modulo dono (base): Pedro Ribeiro (Desenvolvedor 1 - fundacao).
Os proximos devs ADICIONAM schemas aqui, seguindo o mesmo padrao:
um *Create para o payload de entrada e um *Response para a saida.

Por que existe: a rota nunca confia no que o cliente mandou. O Pydantic
rejeita nome vazio ou meta negativa antes de qualquer coisa chegar no banco,
e o FastAPI devolve 422 sozinho com a explicacao do erro.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
