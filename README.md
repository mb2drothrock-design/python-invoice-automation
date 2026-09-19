# Python Invoice Automation Tool

A Python automation project that converts structured CSV order data into professional PDF invoices and a consolidated billing summary.

## Features

- Reads invoice and order data from CSV
- Supports multiple line items per invoice
- Validates required columns and numeric fields
- Calculates subtotal, tax, and final total using `Decimal`
- Generates one formatted PDF invoice per customer invoice
- Creates a consolidated invoice summary CSV
- Supports command-line options for company name, billing email, input file, and output folder
- Includes automated tests

## Tech stack

- Python 3.10+
- ReportLab
- Python standard library: `csv`, `decimal`, `argparse`, `pathlib`
- `unittest`

## Project structure

```text
python-invoice-automation/
├── app.py
├── invoice_tool/
│   ├── __init__.py
│   ├── generator.py
│   └── models.py
├── data/
│   └── sample_orders.csv
├── examples/
│   └── invoice_summary.csv
├── tests/
│   └── test_invoice_tool.py
├── requirements.txt
└── README.md
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

Generated invoices and the summary CSV will be written to the `output/` folder.

### Custom company details

```bash
python3 app.py \
  --input data/sample_orders.csv \
  --output output \
  --company-name "Your Automation Studio" \
  --company-email "billing@yourdomain.com"
```

## CSV format

Required columns:

```text
invoice_number
customer_name
customer_email
issue_date
due_date
description
quantity
unit_price
tax_rate
```

Rows that share the same `invoice_number` are combined into one invoice with multiple line items.

## Testing

```bash
python3 -m unittest discover -s tests
```

## What this demonstrates

This project demonstrates practical Python automation, object-oriented design, CSV processing, validation, accurate monetary calculations, PDF generation, file handling, command-line tooling, and automated testing.

## Portfolio note

This is a self-directed portfolio project created to demonstrate software-development capability. All sample companies, contacts, and email addresses are fictional.
