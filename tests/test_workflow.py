from decimal import Decimal

from procurement_assistant.models import (
    DepartmentBudget,
    InventoryItem,
    PurchaseEvaluationStatus,
    PurchasePolicy,
    PurchaseRequest,
    Supplier,
    SupplierStatus,
)
from procurement_assistant.state import ProcurementState
from procurement_assistant.workflow import workflow

# Tests for the workflow

def make_initial_state(
    max_auto_approval_amount: Decimal = Decimal("1000"),
    available_quantity: int = 4,
) -> ProcurementState:
    """Make an initial state for the workflow."""
    return {
        "request": PurchaseRequest(
            request_id="REQ-TEST-001",
            sku="MOTOR-001",
            quantity=10,
        ),
        "inventory": InventoryItem(
            sku="MOTOR-001",
            name="Industrial motor",
            available_quantity=available_quantity,
        ),
        "supplier": Supplier(
            supplier_id="SUP-001",
            name="Trusted Supplier",
            status=SupplierStatus.APPROVED,
            unit_price=Decimal("50"),
        ),
        "department_budget": DepartmentBudget(
            department_id="MAINTENANCE",
            allocated_budget=Decimal("5000"),
            spent_amount=Decimal("1000"),
        ),
        "policy": PurchasePolicy(
            max_auto_approval_amount=max_auto_approval_amount,
        ),
        "evaluation": None,
        "manager_review_status": "not_required",
        "manager_email_subject": None,
        "manager_email_body": None,
        "manager_email_status": "not_required",
    }

def test_purchase_requiring_manager_approval():
    """Test that the workflow requires manager approval when the purchase amount is greater than the max auto approval amount."""
    state = make_initial_state(
        max_auto_approval_amount=Decimal("100"),
    )

    result = workflow.invoke(state)

    assert (
        result["evaluation"].status
        == PurchaseEvaluationStatus.MANAGER_APPROVAL_REQUIRED
    )
    assert result["manager_review_status"] == "pending"
    assert result["manager_email_status"] == "draft_ready"
    assert result["manager_email_subject"] == (
        "Manager Approval Required — REQ-TEST-001"
    )

def test_purchase_ready_for_purchase():
    """Test that the workflow is ready for purchase when the purchase amount is less than the max auto approval amount."""
    state = make_initial_state(
        max_auto_approval_amount=Decimal("1000"),
    )

    result = workflow.invoke(state)

    assert (
        result["evaluation"].status
        == PurchaseEvaluationStatus.READY_FOR_PURCHASE
    )
    assert result["evaluation"].purchase_quantity == 6
    assert result["manager_review_status"] == "not_required"
    assert result["manager_email_status"] == "not_required"
    assert result["manager_email_subject"] is None
    assert result["manager_email_body"] is None

def test_no_purchase_needed_when_inventory_is_sufficient():
    state = make_initial_state(
        available_quantity=10,
    )

    result = workflow.invoke(state)

    assert (
        result["evaluation"].status
        == PurchaseEvaluationStatus.NO_PURCHASE_NEEDED
    )
    assert result["evaluation"].purchase_quantity == 0
    assert result["evaluation"].estimated_cost == Decimal("0")
    assert result["manager_review_status"] == "not_required"
    assert result["manager_email_status"] == "not_required"