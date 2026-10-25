
from decimal import Decimal

from procurement_assistant.database.connection import SessionLocal
from procurement_assistant.services.inventory_service import get_inventory_item

from langgraph.graph import StateGraph, START, END

from procurement_assistant.business_rules import evaluate_purchase_request, calculate_purchase_quantity
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

# Nodes

def load_inventory(state: ProcurementState) -> dict:
    """Load the inventory item from the database."""
    sku = state["request"].sku

    with SessionLocal() as session:
        inventory = get_inventory_item(sku, session)

    if inventory is None:
        return {
            "inventory": None,
            "inventory_error": f"Inventory item not found: {sku}",
        }

    return {
        "inventory": inventory,
        "inventory_error": None,
    }


def evaluate_purchase(state: ProcurementState) -> dict:
    """ Evaluate the purchase request. """
    inventory = state["inventory"]

    if inventory is None:
        raise ValueError(
            "Cannot evaluate purchase without inventory data."
        )

    evaluation = evaluate_purchase_request(
        request=state["request"],
        inventory=state["inventory"],
        supplier=state["supplier"],
        department_budget=state["department_budget"],
        policy=state["policy"],
    )

    return {"evaluation": evaluation}


def mark_manager_review_pending(
    state: ProcurementState,
) -> dict:
    """ Mark the request as pending manager review. """
    evaluation = state["evaluation"]

    if evaluation is None:
        raise ValueError("Purchase must be evaluated before routing.")

    print(
        f"Request {state['request'].request_id} "
        "requires manager approval."
    )

    return {"manager_review_status": "pending"}

def prepare_manager_email(state: ProcurementState) -> dict:
    """ Prepare the manager email. """
    evaluation = state["evaluation"]

    if evaluation is None:
        raise ValueError("Purchase must be evaluated before preparing email.")

    purchase_quantity = calculate_purchase_quantity(
    request=state["request"],
    inventory=state["inventory"],
    )
    request = state["request"]

    subject = (
        f"Manager Approval Required — {request.request_id}"
    )

    body = (
        f"Hello,\n\n"
        f"Purchase request {request.request_id} requires your review.\n"
        f"Item SKU: {request.sku}\n"
        f"Quantity to purchase: {purchase_quantity}\n" # Show the actual shortage, even when approval is pending.
        f"Estimated cost: {evaluation.estimated_cost}\n"
        f"Reason: {evaluation.message}\n\n"
        f"The purchase must not proceed before valid approval.\n"
    )

    print("\n--- Manager Email Draft ---")
    print(f"Subject: {subject}")
    print(body)

    return {"manager_email_subject": subject, "manager_email_body": body, "manager_email_status": "draft_ready"}

#Routes

def route_request(state: ProcurementState) -> str:
    """ Route the request based on the evaluation status. """
    evaluation = state["evaluation"]

    if evaluation is None:
        raise ValueError("Purchase must be evaluated before routing.")

    if (
        evaluation.status
        == PurchaseEvaluationStatus.MANAGER_APPROVAL_REQUIRED
    ):
        return "manager_approval"

    return "continue"


def route_inventory(state: ProcurementState) -> str:
    """ Route the request based on the inventory status. """
    if state["inventory"] is None:
        return "missing"

    return "found"

# Workflow Builder Definition and Compilation 

builder = StateGraph(ProcurementState)

builder.add_node("load_inventory", load_inventory)
builder.add_node("evaluate_purchase", evaluate_purchase)
builder.add_node("mark_manager_review_pending",mark_manager_review_pending)
builder.add_node("prepare_manager_email", prepare_manager_email)

builder.add_edge(START, "load_inventory")

builder.add_conditional_edges(
    "load_inventory",
    route_inventory,
    {
        "found": "evaluate_purchase",
        "missing": END,
    },
)

builder.add_conditional_edges(
    "evaluate_purchase",
    route_request,
    {
        "manager_approval": "mark_manager_review_pending",
        "continue": END,
    },
)

builder.add_edge(
    "mark_manager_review_pending",
    "prepare_manager_email",
)
builder.add_edge("prepare_manager_email", END)

workflow = builder.compile()