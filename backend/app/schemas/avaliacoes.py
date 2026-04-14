from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AvaliacaoValores(BaseModel):
    saldo_bancario: float = 0
    contas_receber: float = 0
    cartoes: float = 0
    convenios: float = 0
    cheques: float = 0
    trade_marketing: float = 0
    outros_qt: float = 0
    estoque_custo: float = 0
    contas_pagar: float = 0
    fornecedores: float = 0
    investimentos_assumidos: float = 0
    outras_despesas_assumidas: float = 0
    dividas: float = 0
    financiamentos: float = 0
    tributos_atrasados: float = 0
    acoes_processos: float = 0
    faturamento_previsto_mes: float = 0
    compras_mes: float = 0
    entrada_mes: float = 0
    venda_cupom_mes: float = 0
    venda_custo_mes: float = 0
    lucro_liquido_mes: float = 0


class AvaliacaoCreateRequest(AvaliacaoValores):
    tenant_id: UUID
    semana_referencia: date
    status: str = "rascunho"
    observacoes: str | None = None


class AvaliacaoUpdateRequest(BaseModel):
    status: str | None = None
    observacoes: str | None = None
    valores: AvaliacaoValores | None = None


class IndicadorCalculado(BaseModel):
    codigo: str
    nome: str
    valor: float | None
    unidade: str


class AvaliacaoResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    semana_referencia: date
    status: str
    observacoes: str | None = None
    created_at: datetime
    updated_at: datetime
    valores: AvaliacaoValores
    indicadores: list[IndicadorCalculado] = Field(default_factory=list)
