from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: Decimal
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price


@dataclass
class Invoice:
    invoice_number: str
    customer_name: str
    customer_email: str
    issue_date: str
    due_date: str
    tax_rate: Decimal
    items: list[LineItem]

    @property
    def subtotal(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0.00"))

    @property
    def tax_amount(self) -> Decimal:
        return (self.subtotal * self.tax_rate / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def total(self) -> Decimal:
        return (self.subtotal + self.tax_amount).quantize(Decimal("0.01"))
