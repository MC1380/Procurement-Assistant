
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class SupplierStatus(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"


class OrderStatus(str, Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class InventoryItem(BaseModel):
    sku: str
    name: str
    available_quantity: int = Field(ge=0)


class Supplier(BaseModel):
    supplier_id: str
    name: str
    status: SupplierStatus
    unit_price: Decimal = Field(gt=0)


class PurchaseOrder(BaseModel):
    order_id: str
    request_id: str
    supplier_id: str
    sku: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    status: OrderStatus = OrderStatus.CREATED

    @property
    def total_price(self) -> Decimal:
        return self.unit_price * self.quantity

class BudgetPreference(str, Enum):
    LOWEST_COST = "lowest_cost"
    BALANCED = "balanced"
    QUALITY_FIRST = "quality_first"
    UNKNOWN = "unknown"

class PurchasePolicy(BaseModel):
    max_auto_approval_amount: Decimal = Field(gt=0)
    require_approved_supplier: bool = True
    sensitive_categories: set[str] = Field(default_factory=set)

class PurchaseRequest(BaseModel):
    request_id: str
    sku: str
    quantity: int = Field(gt=0)
    budget_limit: Decimal | None = Field(default=None, gt=0)
    budget_preference: BudgetPreference = BudgetPreference.UNKNOWN
    item_name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    reason: str | None = Field(default=None, min_length=1)
    requested_by: str | None = Field(default=None, min_length=1)



class PurchaseEvaluationStatus(str, Enum):
    NO_PURCHASE_NEEDED = "no_purchase_needed"
    READY_FOR_PURCHASE = "ready_for_purchase"
    REJECTED_SUPPLIER = "rejected_supplier"
    OVER_BUDGET = "over_budget"
    MANAGER_APPROVAL_REQUIRED = "manager_approval_required"


class PurchaseEvaluation(BaseModel):
    status: PurchaseEvaluationStatus
    purchase_quantity: int = Field(ge=0)
    estimated_cost: Decimal = Field(ge=0)
    message: str

class DepartmentBudget(BaseModel):
    department_id: str
    allocated_budget: Decimal = Field(gt=0)
    spent_amount: Decimal = Field(default=Decimal("0"), ge=0)

    @property
    def remaining_budget(self) -> Decimal:
        return self.allocated_budget - self.spent_amount


class SuggestionStatus(str, Enum):
    """Possible review states for a purchase suggestion."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PurchaseSuggestion(BaseModel):
    """A request to consider purchasing an item not found in the catalog."""

    suggestion_id: str
    item_name: str = Field(min_length=1)
    description: str | None = None
    requested_quantity: int = Field(gt=0)
    reason: str = Field(min_length=1)
    requested_by: str
    status: SuggestionStatus = SuggestionStatus.PENDING
    manager_comment: str | None = None
