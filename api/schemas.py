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
    LIMITE_MAXIMO_DIARIO_PADRAO,
    LIMITE_MAXIMO_SEMANAL_PADRAO,
    META_HORAS_DIARIA_PADRAO,
    META_HORAS_SEMANAL_PADRAO,
    PRAZO_VENCIMENTO_MESES_PADRAO,
)
from modelos.solicitacao_ajuste import (
    CAMPOS_AJUSTAVEIS,
    STATUS_APROVADO,
    STATUS_REJEITADO,
)
from modelos.chamado import CATEGORIAS_CHAMADO, PRIORIDADES_CHAMADO, STATUS_CHAMADO
from modelos.compromisso import TIPOS_COMPROMISSO
from servicos.autenticacao import TAMANHO_MINIMO_SENHA, normalizar_email
from servicos.calculo import validar_ordem_dos_horarios


def _email_valido(valor: str) -> str:
    """Conferencia simples de e-mail (algo@dominio.algo), sem lib extra."""
    email = normalizar_email(valor)
    usuario, _, dominio = email.partition("@")
    if not usuario or "." not in dominio or dominio.startswith(".") or dominio.endswith("."):
        raise ValueError("informe um e-mail valido")
    return email


class _Credenciais(BaseModel):
    """E-mail e senha - entram no cadastro de estagiario e de gestor."""

    email: str = Field(max_length=120)
    senha: str = Field(min_length=TAMANHO_MINIMO_SENHA, max_length=128)

    @field_validator("email")
    @classmethod
    def _email(cls, valor: str) -> str:
        return _email_valido(valor)


class ConfiguracaoCreate(BaseModel):
    """Metas e limites enviados na criacao de um estagiario."""

    meta_horas_diaria: float = Field(default=META_HORAS_DIARIA_PADRAO, gt=0, le=24)
    meta_horas_semanal: float = Field(default=META_HORAS_SEMANAL_PADRAO, gt=0, le=168)
    limite_alerta_negativo: float = Field(default=LIMITE_ALERTA_NEGATIVO_PADRAO, le=0)
    prazo_vencimento_meses: int = Field(default=PRAZO_VENCIMENTO_MESES_PADRAO, ge=1)
    limite_maximo_diario: float = Field(default=LIMITE_MAXIMO_DIARIO_PADRAO, gt=0, le=24)
    limite_maximo_semanal: float = Field(
        default=LIMITE_MAXIMO_SEMANAL_PADRAO, gt=0, le=168
    )


class ConfiguracaoResponse(ConfiguracaoCreate):
    """Configuracao como ela sai da API, ja com os ids do banco."""

    # from_attributes: permite devolver o objeto do SQLAlchemy direto da rota,
    # sem converter campo por campo na mao.
    model_config = ConfigDict(from_attributes=True)

    id: int
    estagiario_id: int


class EstagiarioCreate(_Credenciais):
    """Payload de POST /estagiarios: nome + meta de horas.

    Entrega 3: tambem o e-mail e a senha da conta - o cadastro ja cria o
    login junto (api/rotas/estagiarios.py).
    """

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
    aviso_limite_legal: str | None = None


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
    dia_de_prova: bool = False

class RelatorioMensalResponse(BaseModel):
    mes: int
    ano: int
    total_horas_trabalhadas: float
    dias_uteis_trabalhados: int
    faltas: int
    datas_faltas: List[date] = []
    saldo_acumulado: float
    aviso_vencimento: Optional[str] = None
    evolucao_diaria: List[RelatorioDiario]
    datas_provas: List[date] = []
    datas_recesso: List[date] = []

# --- Gestor, solicitacoes de ajuste e auditoria -------------------------------
# Parte do Pedro Henrique (secao 3.4). Mesmo padrao da fundacao: um *Create
# para o payload de entrada e um *Response para a saida.


class GestorCreate(_Credenciais):
    """Payload de POST /gestores: o nome de quem vai aprovar os ajustes.

    Entrega 3: tambem o e-mail e a senha da conta de acesso.
    """

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


# --- Assistente de IA ----------------------------------------------------------
# Parte do Arthur Linhares (secao 3.5). Nao existe *Create porque a pergunta nao
# fica salva no banco - mesmo espirito de SimulacaoRequest/SimulacaoResponse
# (Pietro, secao 3.3): so entra, processa e sai, sem virar linha de tabela.


class AssistentePerguntaRequest(BaseModel):
    """Payload de POST /assistente/perguntar: quem pergunta, e o que."""

    estagiario_id: int
    pergunta: str = Field(min_length=3, max_length=500)

    @field_validator("pergunta")
    @classmethod
    def _pergunta_de_verdade(cls, valor: str) -> str:
        """Impede que espacos em branco passem pelo min_length."""
        texto = valor.strip()
        if len(texto) < 3:
            raise ValueError("escreva uma pergunta com pelo menos 3 caracteres")
        return texto


class AssistentePerguntaResponse(BaseModel):
    """Resposta do assistente, ja em linguagem natural."""

    resposta: str


# --- Entrega 3: ponto rapido, configuracao e paineis ---------------------------
# Parte do Miguel (Entrega 3). Mesmo padrao: *Request/*Update na entrada,
# *Response na saida.


class ConfiguracaoUpdate(BaseModel):
    """Payload de PATCH /estagiarios/{id}/configuracao.

    Todos os campos sao opcionais: so muda o que vier no payload. As mesmas
    faixas de ConfiguracaoCreate valem aqui (meta positiva, alerta <= 0...).
    """

    meta_horas_diaria: float | None = Field(default=None, gt=0, le=24)
    meta_horas_semanal: float | None = Field(default=None, gt=0, le=168)
    limite_alerta_negativo: float | None = Field(default=None, le=0)
    prazo_vencimento_meses: int | None = Field(default=None, ge=1)
    limite_maximo_diario: float | None = Field(default=None, gt=0, le=24)
    limite_maximo_semanal: float | None = Field(default=None, gt=0, le=168)


class PontoRequest(BaseModel):
    """Payload (opcional) de POST /ponto/{estagiario_id}.

    Sem marcacao, vale a proxima da ordem (entrada, saida para o almoco,
    retorno, saida). Com marcacao="saida", da para fechar o dia sem almoco.
    """

    marcacao: str | None = None

    @field_validator("marcacao")
    @classmethod
    def _marcacao_conhecida(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in CAMPOS_AJUSTAVEIS:
            raise ValueError(
                f"marcacao precisa ser uma entre: {', '.join(CAMPOS_AJUSTAVEIS)}"
            )
        return valor


class PontoResponse(BaseModel):
    """O registro do dia depois da marcacao, e qual horario foi marcado."""

    campo_marcado: str
    proxima_marcacao: str | None = None
    registro: RegistroResponse


class RegistroHoje(BaseModel):
    """Os horarios do dia de hoje, para o painel saber o que ja foi marcado."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    entrada: time
    saida: time | None = None
    saida_almoco: time | None = None
    retorno_almoco: time | None = None


class Pendencia(BaseModel):
    """Um dia fechado com o almoco incompleto."""

    registro_id: int
    data: date
    campos_faltando: List[str]
    pedido_aberto: bool


class DiaResumo(BaseModel):
    data: date
    horas_trabalhadas: float
    completo: bool


class TendenciaMes(BaseModel):
    """Uma linha da tendencia: o mes, as horas e o saldo acumulado ate ele."""

    ano: int
    mes: int
    horas_trabalhadas: float
    dias_completos: int
    saldo_mes: float
    saldo_acumulado: float


class CompromissoResponse(BaseModel):
    """Um item da agenda como ele sai da API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    estagiario_id: int
    titulo: str
    tipo: str
    data: date
    inicio: time | None = None
    fim: time | None = None
    local: str | None = None
    observacao: str | None = None


class PainelEstagiarioResponse(BaseModel):
    """Tudo o que o painel inicial do estagiario mostra."""

    estagiario_id: int
    nome: str
    hoje: date
    meta_horas_diaria: float
    meta_horas_semanal: float
    limite_alerta: float
    limite_maximo_diario: float
    limite_maximo_semanal: float
    saldo_acumulado: float
    em_alerta: bool
    horas_semana: float
    horas_hoje: float
    registro_hoje: RegistroHoje | None = None
    proxima_marcacao: str | None = None
    pendencias: List[Pendencia]
    pedidos_pendentes: int
    aviso_vencimento: str | None = None
    ultimos_dias: List[DiaResumo]
    tendencia: List[TendenciaMes]
    dia_de_prova_hoje: bool = False
    meta_hoje: float
    compromissos_hoje: List[CompromissoResponse] = []
    proximos_compromissos: List[CompromissoResponse] = []
    chamados_em_aberto: int = 0
    contrato: dict = {}
    recesso: dict = {}


class LinhaEquipe(BaseModel):
    estagiario_id: int
    nome: str
    saldo_acumulado: float
    em_alerta: bool
    limite_alerta: float
    horas_semana: float
    limite_maximo_semanal: float
    meta_horas_semanal: float
    acima_limite_semanal: bool
    dias_acima_limite_diario: int
    pendencias: int
    pedidos_pendentes: int
    ultimo_ponto: date | None = None
    dias_para_fim_contrato: int | None = None
    recessos_pendentes: int = 0


class PainelGestorResponse(BaseModel):
    """Visao da equipe de um gestor."""

    gestor_id: int
    hoje: date
    total_estagiarios: int
    em_alerta: int
    acima_limite_semanal: int
    acima_limite_legal: int
    pedidos_na_fila: int
    saldo_medio: float
    chamados_sem_resposta: int = 0
    chamados_em_andamento: int = 0
    contratos_vencendo: int = 0
    recessos_pendentes: int = 0
    equipe: List[LinhaEquipe]


# --- Entrega 3 (segunda parte): login, chamados, agenda e cracha ---------------
# Parte do Miguel. Mesmo padrao: *Request/*Create na entrada, *Response na saida.


class LoginRequest(BaseModel):
    """Payload de POST /auth/entrar."""

    email: str = Field(max_length=120)
    senha: str = Field(min_length=1, max_length=128)


class UsuarioResponse(BaseModel):
    """Quem esta logado: o perfil e o id do estagiario ou do gestor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    perfil: str
    nome: str
    estagiario_id: int | None = None
    gestor_id: int | None = None


class LoginResponse(BaseModel):
    """O token vai no header Authorization: Bearer <token> das proximas chamadas."""

    token: str
    expira_em: datetime
    usuario: UsuarioResponse


class TrocarSenhaRequest(BaseModel):
    senha_atual: str = Field(min_length=1, max_length=128)
    senha_nova: str = Field(min_length=TAMANHO_MINIMO_SENHA, max_length=128)


class ChamadoCreate(BaseModel):
    """Payload de POST /chamados. O estagiario vem do login, nao do payload."""

    titulo: str = Field(min_length=3, max_length=120)
    categoria: str
    prioridade: str = "media"
    descricao: str = Field(min_length=5, max_length=1000)

    @field_validator("categoria")
    @classmethod
    def _categoria(cls, valor: str) -> str:
        if valor not in CATEGORIAS_CHAMADO:
            raise ValueError(f"categoria precisa ser uma entre: {', '.join(CATEGORIAS_CHAMADO)}")
        return valor

    @field_validator("prioridade")
    @classmethod
    def _prioridade(cls, valor: str) -> str:
        if valor not in PRIORIDADES_CHAMADO:
            raise ValueError(f"prioridade precisa ser uma entre: {', '.join(PRIORIDADES_CHAMADO)}")
        return valor

    @field_validator("titulo", "descricao")
    @classmethod
    def _texto_de_verdade(cls, valor: str) -> str:
        texto = valor.strip()
        if len(texto) < 3:
            raise ValueError("escreva um texto com pelo menos 3 caracteres")
        return texto


class MensagemCreate(BaseModel):
    texto: str = Field(min_length=1, max_length=1000)

    @field_validator("texto")
    @classmethod
    def _texto(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("a mensagem esta vazia")
        return valor.strip()


class ChamadoStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _status(cls, valor: str) -> str:
        if valor not in STATUS_CHAMADO:
            raise ValueError(f"status precisa ser um entre: {', '.join(STATUS_CHAMADO)}")
        return valor


class MensagemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    autor: str
    texto: str
    enviada_em: datetime


class ChamadoResponse(BaseModel):
    """Chamado na lista: sem a conversa, com o resumo dela."""

    id: int
    estagiario_id: int
    estagiario_nome: str
    gestor_id: int
    gestor_nome: str
    titulo: str
    categoria: str
    prioridade: str
    status: str
    aberto_em: datetime
    atualizado_em: datetime
    resolvido_em: datetime | None = None
    total_mensagens: int
    ultima_mensagem_de: str


class ChamadoDetalheResponse(ChamadoResponse):
    """Chamado aberto na tela: com a conversa inteira."""

    mensagens: List[MensagemResponse]


class CompromissoCreate(BaseModel):
    """Payload de POST /agenda. O estagiario vem do login."""

    titulo: str = Field(min_length=2, max_length=120)
    tipo: str
    data: date
    inicio: time | None = None
    fim: time | None = None
    local: str | None = Field(default=None, max_length=120)
    observacao: str | None = Field(default=None, max_length=300)

    @field_validator("tipo")
    @classmethod
    def _tipo(cls, valor: str) -> str:
        if valor not in TIPOS_COMPROMISSO:
            raise ValueError(f"tipo precisa ser um entre: {', '.join(TIPOS_COMPROMISSO)}")
        return valor

    @model_validator(mode="after")
    def _horario(self) -> "CompromissoCreate":
        if self.fim is not None and self.inicio is None:
            raise ValueError("informe o horario de inicio antes do fim")
        if self.inicio is not None and self.fim is not None and self.fim <= self.inicio:
            raise ValueError("o fim precisa ser depois do inicio")
        return self


class CrachaResponse(BaseModel):
    """O cracha como o proprio estagiario (ou o gestor dele) ve."""

    estagiario_id: int
    nome: str
    gestor_nome: str | None = None
    codigo: str
    ativo: bool
    emitido_em: datetime
    inicio_estagio: date | None = None
    url_verificacao: str


class CrachaVerificacaoResponse(BaseModel):
    """O que a pagina publica de verificacao mostra - o minimo necessario."""

    nome: str
    gestor_nome: str | None = None
    ativo: bool
    emitido_em: datetime
    inicio_estagio: date | None = None


class CrachaStatusUpdate(BaseModel):
    ativo: bool


# --- Entrega 3 (terceira parte): contrato de estagio --------------------------------
# Parte do Miguel. Lei 11.788/2008: termo (art. 11), recesso (art. 13) e
# relatorio de atividades (art. 9o, VII). Regras em servicos/estagio.py.


class TermoUpdate(BaseModel):
    """Payload de PUT /estagio/{id}/termo (so o gestor responsavel)."""

    data_inicio: date
    data_fim: date
    instituicao_ensino: str | None = Field(default=None, max_length=120)
    curso: str | None = Field(default=None, max_length=120)
    pessoa_com_deficiencia: bool = False


class ContratoResponse(BaseModel):
    cadastrado: bool
    data_inicio: date | None = None
    data_fim: date | None = None
    instituicao_ensino: str | None = None
    curso: str | None = None
    pessoa_com_deficiencia: bool = False
    dias_restantes: int | None = None
    vencendo: bool = False
    encerrado: bool = False


class SaldoRecessoResponse(BaseModel):
    inicio_estagio: date | None = None
    meses_completos: int
    direito: int
    aprovados: int
    pendentes: int
    disponiveis: int


class RecessoCreate(BaseModel):
    """Payload de POST /estagio/recessos. O estagiario vem do login."""

    data_inicio: date
    data_fim: date
    observacao: str | None = Field(default=None, max_length=300)


class RecessoResponse(BaseModel):
    id: int
    estagiario_id: int
    estagiario_nome: str
    data_inicio: date
    data_fim: date
    dias: int
    observacao: str | None = None
    status: str
    pedido_em: datetime
    respondido_em: datetime | None = None
    gestor_nome: str | None = None


class RecessoDecisao(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _decisao(cls, valor: str) -> str:
        if valor not in ("aprovado", "rejeitado"):
            raise ValueError("status precisa ser aprovado ou rejeitado")
        return valor


class EstagioResponse(BaseModel):
    """GET /estagio/{id}: contrato, saldo de recesso e os pedidos."""

    contrato: ContratoResponse
    recesso: SaldoRecessoResponse
    pedidos: List[RecessoResponse]


class AtividadeCreate(BaseModel):
    data: date
    descricao: str = Field(min_length=5, max_length=1000)

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str) -> str:
        texto = valor.strip()
        if len(texto) < 5:
            raise ValueError("descreva a atividade com pelo menos 5 caracteres")
        return texto


class AtividadeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data: date
    descricao: str
    criada_em: datetime


class SemestreResponse(BaseModel):
    """O relatorio de atividades de um semestre (tela e PDF)."""

    model_config = ConfigDict(from_attributes=True)

    estagiario_id: int
    estagiario_nome: str
    ano: int
    semestre: int
    inicio: date
    fim: date
    horas_trabalhadas: float
    dias_trabalhados: int
    atividades: List[AtividadeResponse]
    status: str
    avaliacao_gestor: str | None = None
    validado_em: datetime | None = None
    gestor_nome: str | None = None
    ciente_em: datetime | None = None
    instituicao_ensino: str | None = None
    curso: str | None = None


class AvaliacaoSemestre(BaseModel):
    """Payload de PUT /estagio/{id}/semestre/{ano}/{semestre} (gestor)."""

    avaliacao: str = Field(default="", max_length=1500)
    validar: bool = False
