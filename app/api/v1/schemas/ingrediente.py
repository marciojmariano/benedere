"""
Schemas Pydantic — Ingrediente
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator, model_validator

from app.infra.database.models.base import EstrategiaCusto, TipoIngrediente, UnidadeMedida


# ── Requests ──────────────────────────────────────────────────────────────────

class IngredienteCreateRequest(BaseModel):
    nome: str
    tipo: TipoIngrediente = TipoIngrediente.INSUMO
    unidade_medida: UnidadeMedida
    custo_unitario: Decimal
    descricao: str | None = None
    markup_id: uuid.UUID | None = None
    estrategia_custo: EstrategiaCusto | None = None
    periodo_dias_custo_medio: int | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        if len(v) > 255:
            raise ValueError("Nome deve ter no máximo 255 caracteres")
        return v

    @field_validator("custo_unitario")
    @classmethod
    def validate_custo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Custo unitário deve ser maior que zero")
        return round(v, 4)

    @field_validator("periodo_dias_custo_medio")
    @classmethod
    def validate_periodo(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("Período deve ser de pelo menos 1 dia")
        return v

    @model_validator(mode="after")
    def validate_periodo_requer_estrategia_periodo(self):
        if self.periodo_dias_custo_medio is not None and self.estrategia_custo != EstrategiaCusto.MEDIA_PONDERADA_PERIODO:
            raise ValueError("periodo_dias_custo_medio só é aplicável com estrategia_custo=MEDIA_PONDERADA_PERIODO")
        return self


class IngredienteUpdateRequest(BaseModel):
    nome: str | None = None
    tipo: TipoIngrediente | None = None
    unidade_medida: UnidadeMedida | None = None
    custo_unitario: Decimal | None = None
    descricao: str | None = None
    markup_id: uuid.UUID | None = None
    estrategia_custo: EstrategiaCusto | None = None
    periodo_dias_custo_medio: int | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        return v

    @field_validator("custo_unitario")
    @classmethod
    def validate_custo(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("Custo unitário deve ser maior que zero")
        return round(v, 4)


# ── Response ──────────────────────────────────────────────────────────────────

class IngredienteResponse(BaseModel):
    id: uuid.UUID
    nome: str
    tipo: TipoIngrediente
    unidade_medida: UnidadeMedida
    custo_unitario: Decimal
    saldo_atual: Decimal
    descricao: str | None
    markup_id: uuid.UUID | None
    ativo: bool
    estrategia_custo: EstrategiaCusto | None
    periodo_dias_custo_medio: int | None
    custo_calculado: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Histórico de custo ─────────────────────────────────────────────────────────

class HistoricoCustoItem(BaseModel):
    data_movimentacao: str
    preco_unitario_custo: Decimal
    quantidade: Decimal
    custo_medio_acumulado: Decimal


class RecalculoCustosResponse(BaseModel):
    recalculados: int
