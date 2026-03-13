"""
Gerador de PDF — Orçamento e Pedido
Benedere Alimentação Saudável
"""
import io
import os
from datetime import datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Cores da marca Benedere ───────────────────────────────────────────────────
COR_PRIMARIA = colors.HexColor("#e75d23")
COR_SECUNDARIA = colors.HexColor("#87cc6e")
COR_TEXTO = colors.HexColor("#2c2c2c")
COR_TEXTO_CLARO = colors.HexColor("#666666")
COR_FUNDO_HEADER = colors.HexColor("#e75d23")
COR_FUNDO_TABELA = colors.HexColor("#fdf6f3")
COR_LINHA_TABELA = colors.HexColor("#f0e0d8")
COR_BRANCO = colors.white

LOGO_PATH = "/home/marciomariano/projetos/benedere/assets/logo_benedere.png"
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 15 * mm


# ── Estilos ───────────────────────────────────────────────────────────────────

def _estilos():
    styles = getSampleStyleSheet()
    return {
        "titulo_doc": ParagraphStyle(
            "titulo_doc",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=COR_BRANCO,
            spaceAfter=2,
        ),
        "subtitulo_doc": ParagraphStyle(
            "subtitulo_doc",
            fontName="Helvetica",
            fontSize=10,
            textColor=COR_BRANCO,
            spaceAfter=2,
        ),
        "numero_doc": ParagraphStyle(
            "numero_doc",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=COR_BRANCO,
        ),
        "secao": ParagraphStyle(
            "secao",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=COR_PRIMARIA,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "label",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=COR_TEXTO_CLARO,
        ),
        "valor": ParagraphStyle(
            "valor",
            fontName="Helvetica",
            fontSize=9,
            textColor=COR_TEXTO,
        ),
        "rodape": ParagraphStyle(
            "rodape",
            fontName="Helvetica",
            fontSize=8,
            textColor=COR_TEXTO_CLARO,
            alignment=1,
        ),
        "total_label": ParagraphStyle(
            "total_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=COR_TEXTO,
        ),
        "total_valor": ParagraphStyle(
            "total_valor",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=COR_PRIMARIA,
        ),
    }


# ── Header com logo ───────────────────────────────────────────────────────────

def _header(styles: dict, titulo: str, numero: str, data: str) -> Table:
    # Logo
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=40 * mm, height=14 * mm)
        logo.hAlign = "LEFT"
        col_logo = logo
    else:
        col_logo = Paragraph(
            "<b>BENEDERE</b>",
            ParagraphStyle("logo_text", fontName="Helvetica-Bold", fontSize=16, textColor=COR_BRANCO),
        )

    col_titulo = [
        Paragraph(titulo, styles["titulo_doc"]),
        Paragraph("Alimentação Saudável e Personalizada", styles["subtitulo_doc"]),
    ]

    col_numero = [
        Paragraph(numero, styles["numero_doc"]),
        Paragraph(data, styles["subtitulo_doc"]),
    ]

    tabela = Table(
        [[col_logo, col_titulo, col_numero]],
        colWidths=[45 * mm, 90 * mm, 45 * mm],
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_FUNDO_HEADER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "LEFT"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, 0), 6),
        ("RIGHTPADDING", (2, 0), (2, 0), 6),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return tabela


# ── Bloco de info (2 colunas) ─────────────────────────────────────────────────

def _bloco_info(dados: list[tuple[str, str]], styles: dict, colunas: int = 2) -> Table:
    """Renderiza lista de (label, valor) em grade de colunas."""
    rows = []
    for i in range(0, len(dados), colunas):
        grupo = dados[i:i + colunas]
        row_labels = []
        row_valores = []
        for label, valor in grupo:
            row_labels.append(Paragraph(label, styles["label"]))
            row_valores.append(Paragraph(valor or "—", styles["valor"]))
        # Preenche se grupo incompleto
        while len(row_labels) < colunas:
            row_labels.append(Paragraph("", styles["label"]))
            row_valores.append(Paragraph("", styles["valor"]))
        rows.append(row_labels)
        rows.append(row_valores)

    col_width = (PAGE_WIDTH - 2 * MARGIN) / colunas
    tabela = Table(rows, colWidths=[col_width] * colunas)
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabela


# ── Tabela de itens ───────────────────────────────────────────────────────────

def _tabela_itens_orcamento(itens: list[dict], styles: dict) -> Table:
    header = ["#", "Ingrediente", "Qtd", "Un.", "Custo Unit.", "Markup", "Preço Item"]
    dados = [header]

    for i, item in enumerate(itens, 1):
        markup = f"×{item['markup_fator_snapshot']:.4f}" if item.get("markup_fator_snapshot") else "—"
        dados.append([
            str(i),
            item["nome_ingrediente"],
            f"{item['quantidade']:.3f}",
            item["unidade_medida"],
            f"R$ {item['custo_unitario_snapshot']:.4f}",
            markup,
            f"R$ {item['preco_item_com_markup']:.2f}",
        ])

    col_widths = [8 * mm, 55 * mm, 18 * mm, 13 * mm, 28 * mm, 22 * mm, 26 * mm]
    tabela = Table(dados, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), COR_BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Dados
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TEXTCOLOR", (0, 1), (-1, -1), COR_TEXTO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COR_BRANCO, COR_FUNDO_TABELA]),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (3, -1), "CENTER"),
        ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.3, COR_LINHA_TABELA),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COR_PRIMARIA),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabela


def _tabela_itens_pedido(itens: list[dict], styles: dict) -> Table:
    header = ["#", "Ingrediente", "Qtd", "Un.", "Custo Unit.", "Total Item"]
    dados = [header]

    for i, item in enumerate(itens, 1):
        dados.append([
            str(i),
            item["nome_ingrediente_snapshot"],
            f"{item['quantidade']:.3f}",
            item["unidade_medida"],
            f"R$ {item['custo_unitario_snapshot']:.4f}",
            f"R$ {item['custo_total_item']:.2f}",
        ])

    col_widths = [8 * mm, 65 * mm, 20 * mm, 15 * mm, 30 * mm, 32 * mm]
    tabela = Table(dados, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), COR_BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TEXTCOLOR", (0, 1), (-1, -1), COR_TEXTO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COR_BRANCO, COR_FUNDO_TABELA]),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (3, -1), "CENTER"),
        ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, COR_LINHA_TABELA),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COR_PRIMARIA),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabela


# ── Bloco de totais ───────────────────────────────────────────────────────────

def _bloco_totais_orcamento(dados: dict, styles: dict) -> Table:
    linhas = [
        ("Custo dos Ingredientes", f"R$ {dados['custo_ingredientes']:.2f}"),
        ("Embalagem", f"R$ {dados['custo_embalagem']:.2f}"),
        ("Taxa de Entrega", f"R$ {dados['taxa_entrega']:.2f}"),
        ("Custo Total", f"R$ {dados['custo_total']:.2f}"),
    ]
    rows = [[Paragraph(l, styles["label"]), Paragraph(v, styles["valor"])] for l, v in linhas]
    # Linha do preço final destacada
    rows.append([
        Paragraph("PREÇO FINAL", styles["total_label"]),
        Paragraph(f"R$ {dados['preco_final']:.2f}", styles["total_valor"]),
    ])

    tabela = Table(rows, colWidths=[50 * mm, 35 * mm], hAlign="RIGHT")
    tabela.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, COR_PRIMARIA),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabela


def _bloco_totais_pedido(dados: dict, styles: dict) -> Table:
    linhas = [
        ("Embalagem", f"R$ {dados['custo_embalagem']:.2f}"),
        ("Taxa de Entrega", f"R$ {dados['taxa_entrega']:.2f}"),
    ]
    rows = [[Paragraph(l, styles["label"]), Paragraph(v, styles["valor"])] for l, v in linhas]
    rows.append([
        Paragraph("VALOR TOTAL", styles["total_label"]),
        Paragraph(f"R$ {dados['valor_total']:.2f}", styles["total_valor"]),
    ])

    tabela = Table(rows, colWidths=[50 * mm, 35 * mm], hAlign="RIGHT")
    tabela.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, COR_PRIMARIA),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabela


# ── Rodapé ────────────────────────────────────────────────────────────────────

def _rodape(styles: dict, numero: str) -> list:
    return [
        HRFlowable(width="100%", thickness=0.5, color=COR_LINHA_TABELA),
        Spacer(1, 3 * mm),
        Paragraph(
            f"Benedere Alimentação Saudável • {numero} • "
            f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            styles["rodape"],
        ),
    ]


# ── Gerador principal: Orçamento ──────────────────────────────────────────────

def gerar_pdf_orcamento(dados: dict) -> bytes:
    """
    dados = {
        "numero": "ORC-2026-0001",
        "status": "rascunho",
        "validade_dias": 7,
        "created_at": datetime,
        "observacoes": str | None,
        "cliente": {"nome": str, "email": str, "telefone": str},
        "nutricionista": {"nome": str, "crn": str} | None,
        "markup_nome": str | None,
        "custo_ingredientes": Decimal,
        "custo_embalagem": Decimal,
        "taxa_entrega": Decimal,
        "custo_total": Decimal,
        "preco_final": Decimal,
        "itens": [
            {
                "nome_ingrediente": str,
                "quantidade": Decimal,
                "unidade_medida": str,
                "custo_unitario_snapshot": Decimal,
                "markup_fator_snapshot": Decimal | None,
                "preco_item_com_markup": Decimal,
            }
        ],
    }
    """
    buffer = io.BytesIO()
    styles = _estilos()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Orçamento {dados['numero']}",
        author="Benedere Alimentação Saudável",
    )

    story = []
    data_fmt = dados["created_at"].strftime("%d/%m/%Y") if isinstance(dados["created_at"], datetime) else str(dados["created_at"])

    # Header
    story.append(_header(styles, "ORÇAMENTO", dados["numero"], f"Data: {data_fmt}"))
    story.append(Spacer(1, 5 * mm))

    # Dados do cliente
    story.append(Paragraph("DADOS DO CLIENTE", styles["secao"]))
    info_cliente = [
        ("Nome", dados["cliente"]["nome"]),
        ("E-mail", dados["cliente"].get("email", "—")),
        ("Telefone", dados["cliente"].get("telefone", "—")),
        ("Validade do Orçamento", f"{dados['validade_dias']} dias"),
    ]
    if dados.get("nutricionista"):
        info_cliente.append(("Nutricionista", dados["nutricionista"]["nome"]))
        info_cliente.append(("CRN", dados["nutricionista"]["crn"]))

    story.append(_bloco_info(info_cliente, styles))
    story.append(Spacer(1, 4 * mm))

    # Itens
    story.append(Paragraph("ITENS DO ORÇAMENTO", styles["secao"]))
    story.append(_tabela_itens_orcamento(dados["itens"], styles))
    story.append(Spacer(1, 4 * mm))

    # Markup total
    if dados.get("markup_nome"):
        story.append(
            Paragraph(
                f"Markup aplicado no total: <b>{dados['markup_nome']}</b>",
                ParagraphStyle("obs", fontName="Helvetica", fontSize=8, textColor=COR_TEXTO_CLARO),
            )
        )
        story.append(Spacer(1, 2 * mm))

    # Totais
    story.append(_bloco_totais_orcamento(dados, styles))
    story.append(Spacer(1, 4 * mm))

    # Observações
    if dados.get("observacoes"):
        story.append(Paragraph("OBSERVAÇÕES", styles["secao"]))
        story.append(
            Paragraph(
                dados["observacoes"],
                ParagraphStyle("obs_body", fontName="Helvetica", fontSize=9, textColor=COR_TEXTO),
            )
        )
        story.append(Spacer(1, 4 * mm))

    # Rodapé
    story.extend(_rodape(styles, dados["numero"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ── Gerador principal: Pedido ─────────────────────────────────────────────────

def gerar_pdf_pedido(dados: dict) -> bytes:
    """
    dados = {
        "numero": "PED-2026-0001",
        "orcamento_numero": str,
        "status": str,
        "created_at": datetime,
        "data_entrega_prevista": datetime | None,
        "observacoes": str | None,
        "cliente": {"nome": str, "email": str, "telefone": str},
        "nutricionista": {"nome": str, "crn": str} | None,
        "valor_total": Decimal,
        "taxa_entrega": Decimal,
        "custo_embalagem": Decimal,
        "itens": [
            {
                "nome_ingrediente_snapshot": str,
                "quantidade": Decimal,
                "unidade_medida": str,
                "custo_unitario_snapshot": Decimal,
                "custo_total_item": Decimal,
            }
        ],
    }
    """
    buffer = io.BytesIO()
    styles = _estilos()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Pedido {dados['numero']}",
        author="Benedere Alimentação Saudável",
    )

    story = []
    data_fmt = dados["created_at"].strftime("%d/%m/%Y") if isinstance(dados["created_at"], datetime) else str(dados["created_at"])

    # Header
    story.append(_header(styles, "PEDIDO", dados["numero"], f"Data: {data_fmt}"))
    story.append(Spacer(1, 5 * mm))

    # Dados do pedido
    story.append(Paragraph("DADOS DO PEDIDO", styles["secao"]))
    entrega_prevista = (
        dados["data_entrega_prevista"].strftime("%d/%m/%Y %H:%M")
        if dados.get("data_entrega_prevista") else "A definir"
    )
    info_pedido = [
        ("Cliente", dados["cliente"]["nome"]),
        ("Orçamento de origem", dados.get("orcamento_numero", "—")),
        ("Telefone", dados["cliente"].get("telefone", "—")),
        ("Entrega prevista", entrega_prevista),
        ("Status", dados["status"].upper()),
        ("E-mail", dados["cliente"].get("email", "—")),
    ]
    if dados.get("nutricionista"):
        info_pedido.append(("Nutricionista", dados["nutricionista"]["nome"]))
        info_pedido.append(("CRN", dados["nutricionista"]["crn"]))

    story.append(_bloco_info(info_pedido, styles))
    story.append(Spacer(1, 4 * mm))

    # Itens
    story.append(Paragraph("ITENS DO PEDIDO", styles["secao"]))
    story.append(_tabela_itens_pedido(dados["itens"], styles))
    story.append(Spacer(1, 4 * mm))

    # Totais
    story.append(_bloco_totais_pedido(dados, styles))
    story.append(Spacer(1, 4 * mm))

    # Observações
    if dados.get("observacoes"):
        story.append(Paragraph("OBSERVAÇÕES", styles["secao"]))
        story.append(
            Paragraph(
                dados["observacoes"],
                ParagraphStyle("obs_body", fontName="Helvetica", fontSize=9, textColor=COR_TEXTO),
            )
        )
        story.append(Spacer(1, 4 * mm))

    # Rodapé
    story.extend(_rodape(styles, dados["numero"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
