from __future__ import annotations

import csv
from collections import OrderedDict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Invoice, LineItem


REQUIRED_COLUMNS = {
    "invoice_number",
    "customer_name",
    "customer_email",
    "issue_date",
    "due_date",
    "description",
    "quantity",
    "unit_price",
    "tax_rate",
}


def _money(value: Decimal) -> str:
    return f"${value:,.2f}"


def _parse_decimal(value: str, field: str, row_number: int) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid {field!r} on CSV row {row_number}: {value!r}") from exc


def load_invoices(csv_path: Path) -> list[Invoice]:
    grouped: OrderedDict[str, Invoice] = OrderedDict()

    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("The CSV file has no header row.")

        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        for row_number, row in enumerate(reader, start=2):
            invoice_number = row["invoice_number"].strip()
            if not invoice_number:
                raise ValueError(f"invoice_number is required on CSV row {row_number}")

            quantity = _parse_decimal(row["quantity"], "quantity", row_number)
            unit_price = _parse_decimal(row["unit_price"], "unit_price", row_number)
            tax_rate = _parse_decimal(row["tax_rate"], "tax_rate", row_number)

            if quantity <= 0:
                raise ValueError(f"quantity must be greater than 0 on CSV row {row_number}")
            if unit_price < 0:
                raise ValueError(f"unit_price cannot be negative on CSV row {row_number}")
            if tax_rate < 0:
                raise ValueError(f"tax_rate cannot be negative on CSV row {row_number}")

            item = LineItem(
                description=row["description"].strip(),
                quantity=quantity,
                unit_price=unit_price,
            )

            if invoice_number not in grouped:
                grouped[invoice_number] = Invoice(
                    invoice_number=invoice_number,
                    customer_name=row["customer_name"].strip(),
                    customer_email=row["customer_email"].strip(),
                    issue_date=row["issue_date"].strip(),
                    due_date=row["due_date"].strip(),
                    tax_rate=tax_rate,
                    items=[item],
                )
            else:
                invoice = grouped[invoice_number]
                identity_fields = {
                    "customer_name": row["customer_name"].strip(),
                    "customer_email": row["customer_email"].strip(),
                    "issue_date": row["issue_date"].strip(),
                    "due_date": row["due_date"].strip(),
                }
                for field, value in identity_fields.items():
                    if getattr(invoice, field) != value:
                        raise ValueError(
                            f"Invoice {invoice_number} has inconsistent {field} values (row {row_number})."
                        )
                if invoice.tax_rate != tax_rate:
                    raise ValueError(
                        f"Invoice {invoice_number} has inconsistent tax_rate values (row {row_number})."
                    )
                invoice.items.append(item)

    return list(grouped.values())


def create_invoice_pdf(
    invoice: Invoice,
    destination: Path,
    company_name: str,
    company_email: str,
) -> None:
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    normal.fontSize = 9
    normal.leading = 12

    muted = ParagraphStyle(
        "Muted",
        parent=normal,
        textColor=colors.HexColor("#5C6670"),
    )
    right = ParagraphStyle(
        "Right",
        parent=normal,
        alignment=TA_RIGHT,
    )
    heading = ParagraphStyle(
        "InvoiceHeading",
        parent=styles["Heading1"],
        fontSize=24,
        leading=28,
        spaceAfter=0,
        textColor=colors.HexColor("#1F2937"),
    )

    doc = SimpleDocTemplate(
        str(destination),
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f"Invoice {invoice.invoice_number}",
        author=company_name,
    )

    story = []

    header_data = [
        [
            Paragraph(f"<b>{company_name}</b><br/><font color='#5C6670'>{company_email}</font>", normal),
            Paragraph("INVOICE", heading),
        ]
    ]
    header = Table(header_data, colWidths=[4.4 * inch, 2.2 * inch])
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 0.12 * inch))

    meta_data = [
        [
            Paragraph(
                f"<b>Bill To</b><br/>{invoice.customer_name}<br/>"
                f"<font color='#5C6670'>{invoice.customer_email}</font>",
                normal,
            ),
            Paragraph(
                f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
                f"<b>Issue date:</b> {invoice.issue_date}<br/>"
                f"<b>Due date:</b> {invoice.due_date}",
                right,
            ),
        ]
    ]
    meta = Table(meta_data, colWidths=[4.1 * inch, 2.5 * inch])
    meta.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 0.10 * inch))

    item_rows = [["Description", "Qty", "Unit Price", "Amount"]]
    for item in invoice.items:
        item_rows.append(
            [
                item.description,
                f"{item.quantity.normalize()}",
                _money(item.unit_price),
                _money(item.line_total),
            ]
        )

    items_table = Table(item_rows, colWidths=[3.7 * inch, 0.7 * inch, 1.1 * inch, 1.1 * inch], repeatRows=1)
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (1, 0), (-1, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 0.16 * inch))

    totals = [
        ["Subtotal", _money(invoice.subtotal)],
        [f"Tax ({invoice.tax_rate.normalize()}%)", _money(invoice.tax_amount)],
        ["Total", _money(invoice.total)],
    ]
    totals_table = Table(totals, colWidths=[1.25 * inch, 1.25 * inch], hAlign="RIGHT")
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 1), "Helvetica"),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEABOVE", (0, 2), (-1, 2), 0.8, colors.HexColor("#111827")),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph("Thank you for your business.", muted))

    doc.build(story)


def write_summary(invoices: list[Invoice], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "invoice_number",
                "customer_name",
                "customer_email",
                "issue_date",
                "due_date",
                "subtotal",
                "tax_amount",
                "total",
            ]
        )
        for invoice in invoices:
            writer.writerow(
                [
                    invoice.invoice_number,
                    invoice.customer_name,
                    invoice.customer_email,
                    invoice.issue_date,
                    invoice.due_date,
                    f"{invoice.subtotal:.2f}",
                    f"{invoice.tax_amount:.2f}",
                    f"{invoice.total:.2f}",
                ]
            )


def generate_invoices(
    input_csv: str | Path,
    output_dir: str | Path,
    company_name: str = "Northstar Automation Studio",
    company_email: str = "billing@example.com",
) -> list[Invoice]:
    csv_path = Path(input_csv)
    output_path = Path(output_dir)

    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    output_path.mkdir(parents=True, exist_ok=True)
    invoices = load_invoices(csv_path)

    for invoice in invoices:
        pdf_path = output_path / f"invoice_{invoice.invoice_number}.pdf"
        create_invoice_pdf(invoice, pdf_path, company_name, company_email)

    write_summary(invoices, output_path / "invoice_summary.csv")
    return invoices
