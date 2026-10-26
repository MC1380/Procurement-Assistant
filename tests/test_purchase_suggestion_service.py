
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from procurement_assistant.database.connection import Base
from procurement_assistant.models import (
    PurchaseSuggestion,
    SuggestionStatus,
)
from procurement_assistant.services.purchase_suggestion_service import (
    create_purchase_suggestion,
    get_purchase_suggestion,
)


def test_create_and_retrieve_purchase_suggestion():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    try:
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            suggestion = PurchaseSuggestion(
                suggestion_id="SUG-TEST-001",
                item_name="Pressure Sensor",
                description="Industrial temperature monitoring",
                requested_quantity=2,
                reason="Required for maintenance",
                requested_by="employee-001",
            )

            saved = create_purchase_suggestion(suggestion, session)

            assert saved.suggestion_id == "SUG-TEST-001"
            assert saved.status == SuggestionStatus.PENDING

            retrieved = get_purchase_suggestion(
                "SUG-TEST-001",
                session,
            )

            assert retrieved is not None
            assert retrieved.item_name == "Pressure Sensor"
            assert retrieved.requested_quantity == 2
            assert retrieved.status == SuggestionStatus.PENDING

    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_get_unknown_purchase_suggestion_returns_none():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    try:
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            result = get_purchase_suggestion("SUG-UNKNOWN", session)
            assert result is None

    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
