
from decimal import Decimal

from procurement_assistant.models import (
    BudgetPreference,
    PurchaseRequest,
    Supplier,
    SupplierStatus,
    InventoryItem,
    PurchaseEvaluation,
    PurchaseEvaluationStatus,
    DepartmentBudget,
    PurchasePolicy,
)


def validate_purchase_request(
    request: PurchaseRequest,
    supplier: Supplier,
) -> tuple[bool, str]:
    """Check basic business rules for a purchase request."""

    if supplier.status != SupplierStatus.APPROVED:
        return False, "Supplier is not approved."

    return True, "Purchase request passed basic validation."

def calculate_purchase_quantity(
    request: PurchaseRequest,
    inventory: InventoryItem,
) -> int:
    """Return the quantity needed after considering available stock."""

    if request.sku != inventory.sku:
        raise ValueError("Request SKU does not match inventory SKU.")

    shortage = request.quantity - inventory.available_quantity

    return max(0, shortage)


def evaluate_purchase_request(
    request: PurchaseRequest,
    inventory: InventoryItem,
    supplier: Supplier,
    department_budget: DepartmentBudget,
    policy: PurchasePolicy,
) -> PurchaseEvaluation:
    """Evaluate a purchase using inventory, budget and policy rules."""

    if request.sku != inventory.sku:
        raise ValueError("Request SKU does not match inventory SKU.")

    shortage = max(
        0,
        request.quantity - inventory.available_quantity,
    )

    if shortage == 0:
        return PurchaseEvaluation(
            status=PurchaseEvaluationStatus.NO_PURCHASE_NEEDED,
            purchase_quantity=0,
            estimated_cost=Decimal("0"),
            message="Sufficient inventory is available.",
        )

    if supplier.status != SupplierStatus.APPROVED:
        return PurchaseEvaluation(
            status=PurchaseEvaluationStatus.REJECTED_SUPPLIER,
            purchase_quantity=0,
            estimated_cost=Decimal("0"),
            message="Supplier is not approved.",
        )

    estimated_cost = supplier.unit_price * shortage

    # Check the company's actual remaining department budget.
    if estimated_cost > department_budget.remaining_budget:
        return PurchaseEvaluation(
            status=PurchaseEvaluationStatus.OVER_BUDGET,
            purchase_quantity=0,
            estimated_cost=estimated_cost,
            message="Department budget is insufficient. Manager review is required.",
        )

    # The agent cannot automatically approve purchases above its authority.
    if estimated_cost > policy.max_auto_approval_amount:
        return PurchaseEvaluation(
            status=PurchaseEvaluationStatus.MANAGER_APPROVAL_REQUIRED,
            purchase_quantity=0,
            estimated_cost=estimated_cost,
            message="Purchase exceeds the agent's auto-approval limit.",
        )

    return PurchaseEvaluation(
        status=PurchaseEvaluationStatus.READY_FOR_PURCHASE,
        purchase_quantity=shortage,
        estimated_cost=estimated_cost,
        message="Purchase request passed evaluation.",
    )