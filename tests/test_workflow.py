import pytest
from decimal import Decimal
from uuid import uuid4

from langgraph.types import Command

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import procurement_assistant.workflow as workflow_module
from procurement_assistant.database.connection import Base
from procurement_assistant.database.models import InventoryItemDB,PurchaseSuggestionDB

from procurement_assistant.models import (
    DepartmentBudget,
    InventoryItem,
    PurchaseEvaluationStatus,
    PurchasePolicy,
    PurchaseRequest,
    Supplier,
    SupplierStatus,
    SuggestionStatus,
)
from procurement_assistant.state import ProcurementState
from procurement_assistant.workflow import workflow

#

def run_workflow_with_test_database(state):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    inventory = state["inventory"]

    if inventory is not None:
        with TestSessionLocal() as session:
            session.add(
                InventoryItemDB(
                    sku=inventory.sku,
                    name=inventory.name,
                    available_quantity=inventory.available_quantity,
                    minimum_quantity=0,
                )
            )
            session.commit()

    original_session_local = workflow_module.SessionLocal
    workflow_module.SessionLocal = TestSessionLocal

    try:
        result = workflow_module.workflow.invoke( 
            state,
            config={"configurable": {"thread_id": str(uuid4())}},
        )

        with TestSessionLocal() as session:
            suggestion_count = session.scalar(
                select(func.count()).select_from(PurchaseSuggestionDB)
            )

        result["_test_suggestion_count"] = suggestion_count
        return result
    finally:
        workflow_module.SessionLocal = original_session_local
        engine.dispose()


# Tests for the workflow

def make_initial_state(
    max_auto_approval_amount: Decimal = Decimal("100"),
    available_quantity: int = 4,
    request_id: str | None = None,
) -> ProcurementState:
    """Make an initial state for the workflow."""
    if request_id is None:
        request_id = f"REQ-TEST-{uuid4().hex}"

    return {
        "request": PurchaseRequest(
            request_id=request_id,
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
        "purchase_suggestion": None,
        "suggestion_error": None,
        "suggestion_status": SuggestionStatus.PENDING,
    }

def test_purchase_requiring_manager_approval():
    """Test that the workflow requires manager approval when the purchase amount is greater than the max auto approval amount."""
    state = make_initial_state(
        max_auto_approval_amount=Decimal("100"),
        request_id="REQ-TEST-001",
    )

    result = run_workflow_with_test_database(state)

    assert (
        result["evaluation"].status
        == PurchaseEvaluationStatus.MANAGER_APPROVAL_REQUIRED
    )
    assert result["manager_review_status"] == "pending"
    assert result["manager_email_status"] == "simulated_sent"
    assert result["manager_email_subject"] == (
        "Manager Approval Required — REQ-TEST-001"
    )

def test_purchase_ready_for_purchase():
    """Test that the workflow is ready for purchase when the purchase amount is less than the max auto approval amount."""
    state = make_initial_state(
        max_auto_approval_amount=Decimal("1000"),
        request_id="REQ-TEST-002",
    )

    result = run_workflow_with_test_database(state)

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
        request_id="REQ-TEST-003",
    )

    result = run_workflow_with_test_database(state)

    assert (
        result["evaluation"].status
        == PurchaseEvaluationStatus.NO_PURCHASE_NEEDED
    )
    assert result["evaluation"].purchase_quantity == 0
    assert result["evaluation"].estimated_cost == Decimal("0")
    assert result["manager_review_status"] == "not_required"
    assert result["manager_email_status"] == "not_required"


def test_workflow_stops_when_inventory_is_missing():
    state = make_initial_state(
        request_id="REQ-TEST-004",
    )
    state["request"] = state["request"].model_copy(
    update={
        "sku": "UNKNOWN-999",
        "item_name": "Pressure Sensor",
        "description": "Industrial pressure sensor",
        "reason": "Required for machine maintenance",
        "requested_by": "employee-001",
    }
    )

    result = run_workflow_with_test_database(state)

    assert result["inventory"] is None
    assert result["inventory_error"] == (
        "Inventory item not found: UNKNOWN-999"
    )
    assert result["evaluation"] is None

    assert result["purchase_suggestion"] is not None
    assert result["purchase_suggestion"].item_name == "Pressure Sensor"
    assert result["purchase_suggestion"].status == SuggestionStatus.PENDING
    assert result["suggestion_status"] == SuggestionStatus.PENDING
    assert result["suggestion_error"] is None

def test_missing_suggestion_details_prevent_registration():
    state = make_initial_state(
        request_id="REQ-TEST-005",
    )

    state["request"] = state["request"].model_copy(
        update={
            "sku": "UNKNOWN-999",
            "item_name": None,
            "reason": None,
            "requested_by": None,
        }
    )

    result = run_workflow_with_test_database(state)

    assert result["inventory"] is None
    assert result["purchase_suggestion"] is None
    assert result["suggestion_status"] is None
    assert "item_name" in result["suggestion_error"]
    assert "reason" in result["suggestion_error"]
    assert "requested_by" in result["suggestion_error"]
    assert result["_test_suggestion_count"] == 0


def test_workflow_pauses_and_resumes_after_manager_approval():
    state = make_initial_state(
        request_id="REQ-TEST-006",
    )
    config = {
        "configurable": {
            "thread_id": state["request"].request_id,
        }
    }

    # First invocation: the workflow should pause for approval.
    paused_state = workflow.invoke(state, config=config)

    assert paused_state["manager_email_status"] == "simulated_sent"
    assert paused_state["manager_review_status"] == "pending"
    assert "__interrupt__" in paused_state

    # Resume the same workflow with the manager's decision.
    resumed_state = workflow.invoke(
        Command(
            resume={
                "decision": "approved",
                "comment": "Approved for testing.",
            }
        ),
        config=config,
    )

    assert resumed_state["manager_review_status"] == "approved"
    assert resumed_state["manager_review_comment"] == "Approved for testing."


def test_workflow_pauses_and_resumes_after_manager_rejection():
    state = make_initial_state(
        request_id="REQ-TEST-007",
    )
    config = {
        "configurable": {
            "thread_id": state["request"].request_id,
        }
    }

    # First invocation: the workflow should pause for manager review.
    paused_state = workflow.invoke(state, config=config)
    assert paused_state["manager_email_status"] == "simulated_sent"
    assert paused_state["manager_review_status"] == "pending"
    assert "__interrupt__" in paused_state

    # Resume the same workflow with the manager's decision.
    resumed_state = workflow.invoke(
        Command(
            resume={
                "decision": "rejected",
                "comment": "The requested purchase is not justified.",
            }
        ),
        config=config,
    )

    assert resumed_state["manager_review_status"] == "rejected"
    assert resumed_state["manager_review_comment"] == "The requested purchase is not justified."

def test_workflow_pauses_after_manager_approval_with_invalid_decision():
    state = make_initial_state(
        request_id="REQ-TEST-008",
    )
    config = {
        "configurable": {
            "thread_id": state["request"].request_id,
        }
    }

    # First invocation: the workflow should pause for approval.
    paused_state = workflow.invoke(state, config=config)
    assert paused_state["manager_email_status"] == "simulated_sent"
    assert paused_state["manager_review_status"] == "pending"
    assert "__interrupt__" in paused_state

    # Resume the same workflow with the manager's decision.
    
    with pytest.raises(ValueError, match="Decision must be 'approved' or 'rejected'."):
        workflow.invoke(
        Command(
            resume={
                "decision": "invalid",
                "comment": "Invalid decision.",
            }
        ),
        config=config,
    )
    


def test_workflow_pauses_after_manager_leaving_comment_blank():
    state = make_initial_state(
        request_id="REQ-TEST-009",
    )
    config = {
        "configurable": {
            "thread_id": state["request"].request_id,
        }
    }

    # First invocation: the workflow should pause for approval.
    paused_state = workflow.invoke(state, config=config)
    assert paused_state["manager_email_status"] == "simulated_sent"
    assert paused_state["manager_review_status"] == "pending"
    assert "__interrupt__" in paused_state

    # Resume the same workflow with the manager's decision.
    with pytest.raises(ValueError, match="A manager comment is required."):
        workflow.invoke(
        Command(
            resume={
                "decision": "approved",
                "comment": "",
            }
        ),
        config=config,
    )
    
def test_different_request_ids_are_independent():
    state1 = make_initial_state()
    state2 = make_initial_state()
    assert state1["request"].request_id != state2["request"].request_id
