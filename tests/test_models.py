
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
    BudgetPreference,
    PurchasePolicy,
    DepartmentBudget,
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

def test_purchase_policy_accepts_valid_data():
    policy = PurchasePolicy(
        max_auto_approval_amount=Decimal("50000000"),
        sensitive_categories={"critical_components"},
    )

    assert policy.max_auto_approval_amount == Decimal("50000000")
    assert policy.require_approved_supplier is True
    assert "critical_components" in policy.sensitive_categories


def test_purchase_policy_rejects_zero_limit():
    with pytest.raises(ValidationError):
        PurchasePolicy(
            max_auto_approval_amount=Decimal("0"),
        )


def test_purchase_policy_has_independent_default_categories():
    policy_a = PurchasePolicy(
        max_auto_approval_amount=Decimal("50000000"),
    )
    policy_b = PurchasePolicy(
        max_auto_approval_amount=Decimal("30000000"),
    )

    policy_a.sensitive_categories.add("critical_components")

    assert policy_b.sensitive_categories == set()

def test_department_budget_calculates_remaining_budget():
    budget = DepartmentBudget(
        department_id="maintenance",
        allocated_budget=Decimal("200000000"),
        spent_amount=Decimal("70000000"),
    )

    assert budget.remaining_budget == Decimal("130000000")


def test_department_budget_defaults_spent_amount_to_zero():
    budget = DepartmentBudget(
        department_id="maintenance",
        allocated_budget=Decimal("200000000"),
    )

    assert budget.spent_amount == Decimal("0")
    assert budget.remaining_budget == Decimal("200000000")


def test_department_budget_allows_over_budget_status():
    budget = DepartmentBudget(
        department_id="maintenance",
        allocated_budget=Decimal("100000000"),
        spent_amount=Decimal("110000000"),
    )

    assert budget.remaining_budget == Decimal("-10000000")


def test_department_budget_rejects_negative_spent_amount():
    with pytest.raises(ValidationError):
        DepartmentBudget(
            department_id="maintenance",
            allocated_budget=Decimal("100000000"),
            spent_amount=Decimal("-1"),
        )    