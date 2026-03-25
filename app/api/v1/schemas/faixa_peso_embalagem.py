"""
Schemas Pydantic — FaixaPesoEmbalagem
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────

class FaixaPesoEmbalagemCreateRequest(BaseModel):
    peso_min_g: Decimal
    peso_max_g: Decimal
    ingrediente_embalagem_id: uuid.UUID

    @field_validator("peso_min_g")
    @classmethod
    def validate_peso_min(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Peso mínimo não pode ser negativo")
        return round(v, 2)

    @field_validator("peso_max_g")
    @classmethod
    def validate_peso_max(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Peso máximo deve ser maior que zero")
        return round(v, 2)


class FaixaPesoEmbalagemUpdateRequest(BaseModel):
    peso_min_g: Decimal | None = None
    peso_max_g: Decimal | None = None
    ingrediente_embalagem_id: uuid.UUID | None = None

    @field_validator("peso_min_g")
    @classmethod
    def validate_peso_min(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("Peso mínimo não pode ser negativo")
        return round(v, 2) if v is not None else v

    @field_validator("peso_max_g")
    @classmethod
    def validate_peso_max(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Peso máximo deve ser maior que zero")
        return round(v, 2) if v is not None else v


# ── Response ──────────────────────────────────────────────────────────────────

class FaixaPesoEmbalagemResponse(BaseModel):
    id: uuid.UUID
    peso_min_g: Decimal
    peso_max_g: Decimal
    ingrediente_embalagem_id: uuid.UUID
    ingrediente_embalagem_nome: str
    ingrediente_embalagem_custo: Decimal
    ativo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
