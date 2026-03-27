"""
Service: Producao — Explosão de Insumos (BOM)
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from app.infra.database.models.base import StatusPedido
from app.infra.repository.pedido_repository import PedidoRepository
from app.api.v1.schemas.producao import (
    ExplosaoIngredienteItem,
    ExplosaoPedidoDetalhe,
    ExplosaoProducaoResponse,
    MapaClienteGrupo,
    MapaComposicaoItem,
    MapaItemDetalhe,
    MapaMontagemResponse,
    MapaPedidoDetalhe,
)


class ProducaoService:

    def __init__(self, pedido_repo: PedidoRepository) -> None:
        self._pedido_repo = pedido_repo

    async def gerar_explosao(
        self,
        data_inicio: date,
        data_fim: date,
        status_list: list[StatusPedido] | None = None,
        filtro_data: Literal["entrega", "criacao"] = "entrega",
    ) -> ExplosaoProducaoResponse:
        rows_ingredientes = await self._pedido_repo.explosao_ingredientes(
            data_inicio=data_inicio,
            data_fim=data_fim,
            status_list=status_list,
            filtro_data=filtro_data,
        )
        rows_pedidos = await self._pedido_repo.listar_pedidos_periodo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            status_list=status_list,
            filtro_data=filtro_data,
        )

        ingredientes: list[ExplosaoIngredienteItem] = []
        custo_total_geral = Decimal("0")

        for row in rows_ingredientes:
            qtd_total = Decimal(str(row.quantidade_total_g)) if row.quantidade_total_g is not None else Decimal("0")
            custo_kg = Decimal(str(row.custo_kg_medio)) if row.custo_kg_medio is not None else None
            custo_total = (qtd_total / 1000 * custo_kg).quantize(Decimal("0.0001")) if custo_kg else None
            saldo = Decimal(str(row.saldo_atual)) if row.saldo_atual is not None else None

            deficit = None
            if saldo is not None:
                saldo_g = saldo * 1000
                diff = qtd_total - saldo_g
                deficit = diff if diff > 0 else Decimal("0")

            if custo_total:
                custo_total_geral += custo_total

            ingredientes.append(
                ExplosaoIngredienteItem(
                    ingrediente_id=row.ingrediente_id,
                    ingrediente_nome=row.ingrediente_nome_snap,
                    tipo=row.tipo,
                    unidade_medida=row.unidade_medida,
                    quantidade_total_g=qtd_total.quantize(Decimal("0.01")),
                    custo_kg_medio=custo_kg.quantize(Decimal("0.0001")) if custo_kg else None,
                    custo_total_estimado=custo_total,
                    saldo_atual=saldo,
                    deficit_g=deficit.quantize(Decimal("0.01")) if deficit is not None else None,
                )
            )

        pedidos: list[ExplosaoPedidoDetalhe] = [
            ExplosaoPedidoDetalhe(
                pedido_id=row.id,
                pedido_numero=row.numero,
                cliente_nome=row.cliente_nome,
                data_entrega_prevista=row.data_entrega_prevista,
                total_itens=row.total_itens,
            )
            for row in rows_pedidos
        ]

        return ExplosaoProducaoResponse(
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            total_pedidos=len(pedidos),
            total_ingredientes=len(ingredientes),
            custo_total_estimado=custo_total_geral.quantize(Decimal("0.01")),
            ingredientes=ingredientes,
            pedidos=pedidos,
        )

    async def gerar_mapa_montagem(
        self,
        data_inicio: date,
        data_fim: date,
        status_list: list | None = None,
        filtro_data: str = "entrega",
    ) -> MapaMontagemResponse:
        pedidos = await self._pedido_repo.mapa_montagem(
            data_inicio=data_inicio,
            data_fim=data_fim,
            status_list=status_list,
            filtro_data=filtro_data,
        )

        # Agrupa por cliente preservando a ordem de entrega
        clientes_dict: dict = {}
        total_itens = 0

        for pedido in pedidos:
            cliente = pedido.cliente
            cid = str(cliente.id)

            if cid not in clientes_dict:
                clientes_dict[cid] = MapaClienteGrupo(
                    cliente_id=cliente.id,
                    cliente_nome=cliente.nome,
                    cliente_endereco=cliente.endereco if hasattr(cliente, "endereco") else None,
                    cliente_observacoes=cliente.observacoes if hasattr(cliente, "observacoes") else None,
                    pedidos=[],
                )

            _TIPO_ORDER = {
                'CAFE_MANHA': 0, 'LANCHE_MANHA': 1, 'ALMOCO': 2,
                'LANCHE_TARDE': 3, 'JANTAR': 4,
            }
            itens_sorted = sorted(pedido.itens, key=lambda i: i.nome_snapshot or '', reverse=True)
            itens_sorted = sorted(
                itens_sorted,
                key=lambda i: _TIPO_ORDER.get(i.tipo_refeicao.value if i.tipo_refeicao else '', 99),
            )

            itens_detalhe: list[MapaItemDetalhe] = []
            for item in itens_sorted:
                composicao = [
                    MapaComposicaoItem(
                        ingrediente_nome=c.ingrediente_nome_snap,
                        quantidade_g=Decimal(str(c.quantidade_g)),
                    )
                    for c in sorted(item.composicao, key=lambda c: c.ingrediente_nome_snap)
                ]
                itens_detalhe.append(
                    MapaItemDetalhe(
                        nome_snapshot=item.nome_snapshot,
                        tipo_refeicao=item.tipo_refeicao,
                        tipo=item.tipo,
                        quantidade=item.quantidade,
                        embalagem_nome=item.embalagem_nome_snapshot,
                        composicao=composicao,
                    )
                )
                total_itens += item.quantidade

            clientes_dict[cid].pedidos.append(
                MapaPedidoDetalhe(
                    pedido_id=pedido.id,
                    pedido_numero=pedido.numero,
                    data_entrega_prevista=pedido.data_entrega_prevista,
                    observacoes=pedido.observacoes,
                    itens=itens_detalhe,
                )
            )

        clientes = list(clientes_dict.values())

        return MapaMontagemResponse(
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            total_clientes=len(clientes),
            total_pedidos=len(pedidos),
            total_itens=total_itens,
            clientes=clientes,
        )
