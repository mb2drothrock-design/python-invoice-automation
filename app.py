from __future__ import annotations

import argparse

from invoice_tool import generate_invoices


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate PDF invoices and a summary CSV from order data."
    )
    parser.add_argument("--input", default="data/sample_orders.csv", help="Path to the source CSV")
    parser.add_argument("--output", default="output", help="Folder for generated files")
    parser.add_argument(
        "--company-name",
        default="Northstar Automation Studio",
        help="Company name shown on invoices",
    )
    parser.add_argument(
        "--company-email",
        default="billing@example.com",
        help="Company email shown on invoices",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    invoices = generate_invoices(
        input_csv=args.input,
        output_dir=args.output,
        company_name=args.company_name,
        company_email=args.company_email,
    )

    print(f"Generated {len(invoices)} invoice(s) in: {args.output}")
    for invoice in invoices:
        print(f"  - {invoice.invoice_number}: ${invoice.total:,.2f}")


if __name__ == "__main__":
    main()
