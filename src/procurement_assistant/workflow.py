
from decimal import Decimal
from uuid import uuid4


from procurement_assistant.database.connection import SessionLocal

from procurement_assistant.services.inventory_service import get_inventory_item
from procurement_assistant.services.purchase_suggestion_service import create_purchase_suggestion
from procurement_assistant.services.email_service import MockEmailSender

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver

from procurement_assistant.business_rules import evaluate_purchase_request, calculate_purchase_quantity

from procurement_assistant.models import (
    DepartmentBudget,
    InventoryItem,
    PurchaseEvaluationStatus,
    PurchasePolicy,
    PurchaseRequest,
    Supplier,
    SupplierStatus,
    PurchaseSuggestion,
    SuggestionStatus
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

def create_purchase_suggestion_node(
    state: ProcurementState,
) -> dict:
    """Register a purchase suggestion when an item is missing."""

    request = state["request"]

    # Validate the information required to register a suggestion.
    missing_fields = []

    if not request.item_name:
        missing_fields.append("item_name")

    if not request.reason:
        missing_fields.append("reason")

    if not request.requested_by:
        missing_fields.append("requested_by")

    if missing_fields:
        return {
            "purchase_suggestion": None,
            "suggestion_status": None,
            "suggestion_error": (
                "Missing required suggestion details: "
                + ", ".join(missing_fields)
            ),
        }

    suggestion = PurchaseSuggestion(
        suggestion_id=f"SUG-{uuid4().hex}",
        item_name=request.item_name,
        description=request.description,
        requested_quantity=request.quantity,
        reason=request.reason,
        requested_by=request.requested_by,
        status=SuggestionStatus.PENDING,
    )

    try:
        with SessionLocal() as session:
            saved_suggestion = create_purchase_suggestion(
                suggestion=suggestion,
                session=session,
            )
    except Exception as exc:
        return {
            "purchase_suggestion": None,
            "suggestion_status": None,
            "suggestion_error": (
                f"Failed to save purchase suggestion: {exc}"
            ),
        }

    return {
        "purchase_suggestion": saved_suggestion,
        "suggestion_status": saved_suggestion.status,
        "suggestion_error": None,
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



def send_manager_email(state: ProcurementState) -> dict:
    """Simulate sending the prepared approval email."""

    subject = state["manager_email_subject"]
    body = state["manager_email_body"]

    if not subject or not body:
        raise ValueError("Email subject and body must be prepared first.")

    sender = MockEmailSender()

    result = sender.send(
        recipient="manager@example.com",
        subject=subject,
        body=body,
    )

    return {
        "manager_email_status": (
            "simulated_sent" if result.success else "failed"
        ),
    }


def wait_for_manager_approval(state: ProcurementState) -> dict:
    """Pause the workflow until a manager reviews the request."""

    evaluation = state["evaluation"]
    if evaluation is None:
        raise ValueError("Purchase must be evaluated before manager review.")

    decision = interrupt(
        {
            "request_id": state["request"].request_id,
            "estimated_cost": str(evaluation.estimated_cost),
            "email_subject": state["manager_email_subject"],
            "email_body": state["manager_email_body"],
            "message": "Manager approval is required.",
        }
    )

    if not isinstance(decision, dict):
        raise ValueError("Manager decision must be a dictionary.")

    status = decision.get("decision")
    if status not in {"approved", "rejected"}:
        raise ValueError("Decision must be 'approved' or 'rejected'.")

    comment = decision.get("comment")
    if not isinstance(comment, str) or not comment.strip():
        raise ValueError("A manager comment is required.")

    return {
        "manager_review_status": status,
        "manager_review_comment": comment.strip(),
    }

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
builder.add_node("create_purchase_suggestion",create_purchase_suggestion_node)
builder.add_node("wait_for_manager_approval",wait_for_manager_approval)
builder.add_node("send_manager_email", send_manager_email)

builder.add_edge(START, "load_inventory")

builder.add_conditional_edges(
    "load_inventory",
    route_inventory,
    {
        "found": "evaluate_purchase",
        "missing": "create_purchase_suggestion",
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
builder.add_edge("prepare_manager_email", "send_manager_email")
builder.add_edge("send_manager_email", "wait_for_manager_approval")
builder.add_edge("wait_for_manager_approval", END)
builder.add_edge("create_purchase_suggestion", END)

checkpointer = InMemorySaver()
workflow = builder.compile(checkpointer=checkpointer)