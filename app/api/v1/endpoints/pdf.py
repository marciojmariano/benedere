"""
Endpoints: geração de PDF para Orçamento e Pedido
"""
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth0 import get_tenant_id
from app.infra.database.session import get_session
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.nutricionista_repository import NutricionistaRepository
from app.infra.repository.orcamento_repository import OrcamentoRepository
from app.infra.repository.pedido_repository import PedidoRepository
from app.services.pdf_generator import gerar_pdf_orcamento, gerar_pdf_pedido

router = APIRouter(prefix="/pdf", tags=["PDF"])

PDF_STORAGE_DIR = Path("/home/marciomariano/projetos/benedere/storage/pdfs")
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _montar_dados_orcamento(orcamento, cliente, nutricionista) -> dict:
    itens = []
    for item in orcamento.itens:
        itens.append({
            "nome_ingrediente": getattr(item, "nome_ingrediente_snapshot", str(item.ingrediente_id)),
            "quantidade": item.quantidade,
            "unidade_medida": item.unidade_medida,
            "custo_unitario_snapshot": item.custo_unitario_snapshot,
            "markup_fator_snapshot": item.markup_fator_snapshot,
            "preco_item_com_markup": item.preco_item_com_markup,
        })

    return {
        "numero": orcamento.numero,
        "status": orcamento.status,
        "validade_dias": orcamento.validade_dias,
        "created_at": orcamento.created_at,
        "observacoes": orcamento.observacoes,
        "cliente": {
            "nome": cliente.nome,
            "email": getattr(cliente, "email", None),
            "telefone": getattr(cliente, "telefone", None),
        },
        "nutricionista": {
            "nome": nutricionista.nome,
            "crn": nutricionista.crn,
        } if nutricionista else None,
        "markup_nome": None,
        "custo_ingredientes": orcamento.custo_ingredientes,
        "custo_embalagem": orcamento.custo_embalagem,
        "taxa_entrega": orcamento.taxa_entrega,
        "custo_total": orcamento.custo_total,
        "preco_final": orcamento.preco_final,
        "itens": itens,
    }


async def _montar_dados_pedido(pedido, orcamento, cliente, nutricionista) -> dict:
    itens = []
    for item in pedido.itens:
        itens.append({
            "nome_ingrediente_snapshot": item.nome_ingrediente_snapshot,
            "quantidade": item.quantidade,
            "unidade_medida": item.unidade_medida,
            "custo_unitario_snapshot": item.custo_unitario_snapshot,
            "custo_total_item": item.custo_total_item,
        })

    return {
        "numero": pedido.numero,
        "orcamento_numero": orcamento.numero if orcamento else "—",
        "status": pedido.status,
        "created_at": pedido.created_at,
        "data_entrega_prevista": pedido.data_entrega_prevista,
        "observacoes": pedido.observacoes,
        "cliente": {
            "nome": cliente.nome,
            "email": getattr(cliente, "email", None),
            "telefone": getattr(cliente, "telefone", None),
        },
        "nutricionista": {
            "nome": nutricionista.nome,
            "crn": nutricionista.crn,
        } if nutricionista else None,
        "valor_total": pedido.valor_total,
        "taxa_entrega": pedido.taxa_entrega,
        "custo_embalagem": pedido.custo_embalagem,
        "itens": itens,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/orcamentos/{orcamento_id}/download",
    summary="Download do PDF do orçamento",
    response_class=Response,
)
async def download_pdf_orcamento(
    orcamento_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id)
):
    _tenant_id = uuid.UUID(tenant_id)
    orcamento_repo = OrcamentoRepository(session, tenant_id=_tenant_id)
    cliente_repo = ClienteRepository(session, tenant_id=_tenant_id)
    nutri_repo = NutricionistaRepository(session, tenant_id=_tenant_id)

    orcamento = await orcamento_repo.get_by_id(orcamento_id)
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")

    cliente = await cliente_repo.get_by_id(orcamento.cliente_id)
    nutricionista = None
    if cliente and getattr(cliente, "nutricionista_id", None):
        nutricionista = await nutri_repo.get_by_id(cliente.nutricionista_id)

    dados = await _montar_dados_orcamento(orcamento, cliente, nutricionista)
    pdf_bytes = gerar_pdf_orcamento(dados)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{orcamento.numero}.pdf"'},
    )


@router.get(
    "/orcamentos/{orcamento_id}/salvar",
    summary="Salva PDF do orçamento em disco e retorna caminho",
)
async def salvar_pdf_orcamento(
    orcamento_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id)
):
    _tenant_id = uuid.UUID(tenant_id)
    orcamento_repo = OrcamentoRepository(session, tenant_id=_tenant_id)
    cliente_repo = ClienteRepository(session, tenant_id=_tenant_id)
    nutri_repo = NutricionistaRepository(session, tenant_id=_tenant_id)

    orcamento = await orcamento_repo.get_by_id(orcamento_id)
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")

    cliente = await cliente_repo.get_by_id(orcamento.cliente_id)
    nutricionista = None
    if cliente and getattr(cliente, "nutricionista_id", None):
        nutricionista = await nutri_repo.get_by_id(cliente.nutricionista_id)

    dados = await _montar_dados_orcamento(orcamento, cliente, nutricionista)
    pdf_bytes = gerar_pdf_orcamento(dados)

    filename = f"{orcamento.numero}.pdf"
    filepath = PDF_STORAGE_DIR / str(_tenant_id) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(pdf_bytes)

    return {"numero": orcamento.numero, "arquivo": str(filepath), "tamanho_bytes": len(pdf_bytes)}


@router.get(
    "/pedidos/{pedido_id}/download",
    summary="Download do PDF do pedido",
    response_class=Response,
)
async def download_pdf_pedido(
    pedido_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id)
):
    _tenant_id = uuid.UUID(tenant_id)
    pedido_repo = PedidoRepository(session, tenant_id=_tenant_id)
    orcamento_repo = OrcamentoRepository(session, tenant_id=_tenant_id)
    cliente_repo = ClienteRepository(session, tenant_id=_tenant_id)
    nutri_repo = NutricionistaRepository(session, tenant_id=_tenant_id)

    pedido = await pedido_repo.get_by_id(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    orcamento = await orcamento_repo.get_by_id(pedido.orcamento_id)
    cliente = await cliente_repo.get_by_id(pedido.cliente_id)
    nutricionista = None
    if cliente and getattr(cliente, "nutricionista_id", None):
        nutricionista = await nutri_repo.get_by_id(cliente.nutricionista_id)

    dados = await _montar_dados_pedido(pedido, orcamento, cliente, nutricionista)
    pdf_bytes = gerar_pdf_pedido(dados)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pedido.numero}.pdf"'},
    )


@router.get(
    "/pedidos/{pedido_id}/salvar",
    summary="Salva PDF do pedido em disco e retorna caminho",
)
async def salvar_pdf_pedido(
    pedido_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id)
):
    _tenant_id = uuid.UUID(tenant_id)
    pedido_repo = PedidoRepository(session, tenant_id=_tenant_id)
    orcamento_repo = OrcamentoRepository(session, tenant_id=_tenant_id)
    cliente_repo = ClienteRepository(session, tenant_id=_tenant_id)
    nutri_repo = NutricionistaRepository(session, tenant_id=_tenant_id)

    pedido = await pedido_repo.get_by_id(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    orcamento = await orcamento_repo.get_by_id(pedido.orcamento_id)
    cliente = await cliente_repo.get_by_id(pedido.cliente_id)
    nutricionista = None
    if cliente and getattr(cliente, "nutricionista_id", None):
        nutricionista = await nutri_repo.get_by_id(cliente.nutricionista_id)

    dados = await _montar_dados_pedido(pedido, orcamento, cliente, nutricionista)
    pdf_bytes = gerar_pdf_pedido(dados)

    filename = f"{pedido.numero}.pdf"
    filepath = PDF_STORAGE_DIR / str(_tenant_id) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(pdf_bytes)

    return {"numero": pedido.numero, "arquivo": str(filepath), "tamanho_bytes": len(pdf_bytes)}
