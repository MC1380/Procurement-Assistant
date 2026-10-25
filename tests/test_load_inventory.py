import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import procurement_assistant.workflow as workflow
from procurement_assistant.database.connection import Base
from procurement_assistant.database.models import InventoryItemDB
from procurement_assistant.models import PurchaseRequest


@pytest.fixture
def test_session_factory(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    monkeypatch.setattr(workflow, "SessionLocal", TestSessionLocal)

    yield TestSessionLocal

    engine.dispose()


def test_load_existing_inventory(test_session_factory):
    with test_session_factory() as session:
        session.add(
            InventoryItemDB(
                sku="MOTOR-001",
                name="Industrial Motor",
                available_quantity=4,
                minimum_quantity=5,
            )
        )
        session.commit()

    state = {
        "request": PurchaseRequest(
            request_id="REQ-TEST-001",
            sku="MOTOR-001",
            quantity=10,
        )
    }

    result = workflow.load_inventory(state)

    assert result["inventory"] is not None
    assert result["inventory"].sku == "MOTOR-001"
    assert result["inventory"].available_quantity == 4
    assert result["inventory_error"] is None


def test_load_missing_inventory(test_session_factory):
    state = {
        "request": PurchaseRequest(
            request_id="REQ-TEST-002",
            sku="UNKNOWN-999",
            quantity=2,
        )
    }

    result = workflow.load_inventory(state)

    assert result["inventory"] is None
    assert result["inventory_error"] == (
        "Inventory item not found: UNKNOWN-999"
    )