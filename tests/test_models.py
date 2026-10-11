
from decimal import Decimal

import pytest
from pydantic import ValidationError

from procurement_assistant.models import (
    InventoryItem,
    OrderStatus,
    PurchaseOrder,
    Supplier,
    SupplierStatus,
    PurchaseRequest,
    BudgetPreference
)


def test_inventory_quantity_cannot_be_negative():
    with pytest.raises(ValidationError):
        InventoryItem(
            sku="BRG-6205",
            name="Industrial Bearing",
            available_quantity=-1,
        )


def test_supplier_status_is_validated():
    supplier = Supplier(
        supplier_id="SUP-001",
        name="Supplier A",
        status=SupplierStatus.APPROVED,
        unit_price=Decimal("90"),
    )

    assert supplier.status == SupplierStatus.APPROVED


def test_purchase_order_total_price():
    order = PurchaseOrder(
        order_id="PO-001",
        request_id="REQ-001",
        supplier_id="SUP-001",
        sku="BRG-6205",
        quantity=2,
        unit_price=Decimal("90"),
    )

    assert order.total_price == Decimal("180")
    assert order.status == OrderStatus.CREATED


def test_purchase_order_quantity_must_be_positive():
    with pytest.raises(ValidationError):
        PurchaseOrder(
            order_id="PO-002",
            request_id="REQ-002",
            supplier_id="SUP-001",
            sku="BRG-6205",
            quantity=0,
            unit_price=Decimal("90"),
        )


def test_purchase_request_accepts_valid_data():
    request = PurchaseRequest(
        request_id="REQ-001",
        sku="BRG-6205",
        quantity=4,
    )

    assert request.quantity == 4


def test_purchase_request_rejects_negative_quantity():
    with pytest.raises(ValidationError):
        PurchaseRequest(
            request_id="REQ-002",
            sku="BRG-6205",
            quantity=-2,
            budget=Decimal("500"),
        )



def test_purchase_request_does_not_require_budget():
    request = PurchaseRequest(
        request_id="REQ-003",
        sku="BRG-6205",
        quantity=4,
    )

    assert request.budget_limit is None
    assert request.budget_preference == BudgetPreference.UNKNOWN


def test_purchase_request_accepts_budget_limit():
    request = PurchaseRequest(
        request_id="REQ-004",
        sku="BRG-6205",
        quantity=4,
        budget_limit=Decimal("500"),
        budget_preference=BudgetPreference.BALANCED,
    )

    assert request.budget_limit == Decimal("500")
    assert request.budget_preference == BudgetPreference.BALANCED
