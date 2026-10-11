
from decimal import Decimal

from procurement_assistant.models import (
    BudgetPreference,
    PurchaseRequest,
    Supplier,
    SupplierStatus,
    InventoryItem,
    PurchaseEvaluation,
    PurchaseEvaluationStatus,
)


def validate_purchase_request(
    request: PurchaseRequest,
    supplier: Supplier,
) -> tuple[bool, str]:
    """Check basic business rules for a purchase request."""

    if supplier.status != SupplierStatus.APPROVED:
        return False, "Supplier is not approved."

    total_price = supplier.unit_price * request.quantity

    if (
        request.budget_limit is not None
        and total_price > request.budget_limit
    ):
        return False, "Purchase exceeds the user's budget limit."

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
) -> PurchaseEvaluation:
    """Evaluate a purchase request using inventory, supplier and budget rules."""

    if request.sku != inventory.sku:
        raise ValueError("Request SKU does not match inventory SKU.")

    shortage = max(
        0,
        request.quantity - inventory.available_quantity,
    )

    # No purchase is necessary if inventory covers the request.
    if shortage == 0:
        return PurchaseEvaluation(
            status=PurchaseEvaluationStatus.NO_PURCHASE_NEEDED,
            purchase_quantity=0,
            estimated_cost=Decimal("0"),
            message="Sufficient inventory is available.",
        )

    # Only check supplier approval when a purchase is actually needed.
    if supplier.status != SupplierStatus.APPROVED:
        return PurchaseEvaluation(
            status=PurchaseEvaluationStatus.REJECTED_SUPPLIER,
            purchase_quantity=0,
            estimated_cost=Decimal("0"),
            message="Supplier is not approved.",
        )

    estimated_cost = supplier.unit_price * shortage

    if (
        request.budget_limit is not None
        and estimated_cost > request.budget_limit
    ):
        return PurchaseEvaluation(
            status=PurchaseEvaluationStatus.OVER_BUDGET,
            purchase_quantity=0,
            estimated_cost=estimated_cost,
            message="Purchase exceeds the user's budget limit.",
        )

    return PurchaseEvaluation(
        status=PurchaseEvaluationStatus.READY_FOR_PURCHASE,
        purchase_quantity=shortage,
        estimated_cost=estimated_cost,
        message="Purchase request passed evaluation.",
    )
