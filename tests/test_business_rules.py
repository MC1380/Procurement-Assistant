
from decimal import Decimal
import pytest

from procurement_assistant.business_rules import validate_purchase_request , calculate_purchase_quantity,evaluate_purchase_request
from procurement_assistant.models import (
    BudgetPreference,
    PurchaseRequest,
    Supplier,
    SupplierStatus,
    InventoryItem,
    PurchaseEvaluationStatus,
)


def make_request(budget_limit=None):
    return PurchaseRequest(
        request_id="REQ-001",
        sku="BRG-6205",
        quantity=4,
        budget_limit=budget_limit,
        budget_preference=BudgetPreference.LOWEST_COST,
    )


def make_supplier(status=SupplierStatus.APPROVED, unit_price="90"):
    return Supplier(
        supplier_id="SUP-001",
        name="Supplier A",
        status=status,
        unit_price=Decimal(unit_price),
    )


def test_approved_supplier_within_budget_passes():
    request = make_request(Decimal("500"))
    supplier = make_supplier()

    is_valid, message = validate_purchase_request(request, supplier)

    assert is_valid is True
    assert message == "Purchase request passed basic validation."


def test_blocked_supplier_is_rejected():
    request = make_request(Decimal("500"))
    supplier = make_supplier(status=SupplierStatus.BLOCKED)

    is_valid, message = validate_purchase_request(request, supplier)

    assert is_valid is False
    assert message == "Supplier is not approved."


def test_purchase_over_budget_is_rejected():
    request = make_request(Decimal("300"))
    supplier = make_supplier(unit_price="90")

    is_valid, message = validate_purchase_request(request, supplier)

    assert is_valid is False
    assert message == "Purchase exceeds the user's budget limit."


def test_request_without_budget_can_pass_basic_validation():
    request = make_request()
    supplier = make_supplier(unit_price="90")

    is_valid, message = validate_purchase_request(request, supplier)

    assert is_valid is True
    assert message == "Purchase request passed basic validation."


def test_calculate_purchase_quantity_with_partial_stock():
    request = make_request()
    inventory = InventoryItem(
        sku="BRG-6205",
        name="Industrial Bearing",
        available_quantity=2,
    )

    assert calculate_purchase_quantity(request, inventory) == 2


def test_calculate_purchase_quantity_when_stock_is_sufficient():
    request = make_request()
    inventory = InventoryItem(
        sku="BRG-6205",
        name="Industrial Bearing",
        available_quantity=8,
    )

    assert calculate_purchase_quantity(request, inventory) == 0


def test_calculate_purchase_quantity_rejects_mismatched_sku():
    request = make_request()
    inventory = InventoryItem(
        sku="BRG-6206",
        name="Different Bearing",
        available_quantity=2,
    )

    with pytest.raises(ValueError, match="SKU does not match"):
        calculate_purchase_quantity(request, inventory)


def test_sufficient_inventory_requires_no_purchase():
    request = make_request()
    inventory = InventoryItem(
        sku="BRG-6205",
        name="Bearing",
        available_quantity=6,
    )

    result = evaluate_purchase_request(
        request, inventory, make_supplier()
    )

    assert result.status == PurchaseEvaluationStatus.NO_PURCHASE_NEEDED
    assert result.purchase_quantity == 0
    assert result.estimated_cost == Decimal("0")


def test_only_shortage_is_purchased():
    request = make_request()
    inventory = InventoryItem(
        sku="BRG-6205",
        name="Bearing",
        available_quantity=2,
    )

    result = evaluate_purchase_request(
        request, inventory, make_supplier(unit_price="90")
    )

    assert result.status == PurchaseEvaluationStatus.READY_FOR_PURCHASE
    assert result.purchase_quantity == 2
    assert result.estimated_cost == Decimal("180")


def test_blocked_supplier_is_rejected():
    request = make_request()
    inventory = InventoryItem(
        sku="BRG-6205",
        name="Bearing",
        available_quantity=0,
    )

    result = evaluate_purchase_request(
        request,
        inventory,
        make_supplier(status=SupplierStatus.BLOCKED),
    )

    assert result.status == PurchaseEvaluationStatus.REJECTED_SUPPLIER
    assert result.purchase_quantity == 0


def test_budget_is_checked_against_shortage_cost():
    request = make_request(budget_limit=Decimal("150"))
    inventory = InventoryItem(
        sku="BRG-6205",
        name="Bearing",
        available_quantity=2,
    )

    result = evaluate_purchase_request(
        request, inventory, make_supplier(unit_price="90")
    )

    assert result.status == PurchaseEvaluationStatus.OVER_BUDGET
    assert result.purchase_quantity == 0
    assert result.estimated_cost == Decimal("180")