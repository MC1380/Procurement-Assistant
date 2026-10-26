from typing import TypedDict

from procurement_assistant.models import (
    DepartmentBudget,
    InventoryItem,
    PurchaseEvaluation,
    PurchasePolicy,
    PurchaseRequest,
    Supplier,
    SuggestionStatus,
    PurchaseSuggestion,
)


class ProcurementState(TypedDict):
    request: PurchaseRequest
    inventory: InventoryItem | None
    inventory_error: str | None
    supplier: Supplier
    department_budget: DepartmentBudget
    policy: PurchasePolicy
    evaluation: PurchaseEvaluation | None
    manager_review_status: str
    manager_email_subject: str | None
    manager_email_body: str | None
    manager_email_status: str
    purchase_suggestion: PurchaseSuggestion | None
    suggestion_error: str | None
    suggestion_status: SuggestionStatus | None