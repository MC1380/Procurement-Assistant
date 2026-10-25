
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from procurement_assistant.database.connection import Base
from procurement_assistant.database.models import InventoryItemDB
from procurement_assistant.services.inventory_service import get_inventory_item


@pytest.fixture
def session():
    # Use a separate in-memory database for each test.
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)

    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with TestSessionLocal() as test_session:
        yield test_session

    test_engine.dispose()


def test_get_existing_inventory_item(session):
    session.add(
        InventoryItemDB(
            sku="MOTOR-001",
            name="Industrial Motor",
            available_quantity=4,
            minimum_quantity=5,
        )
    )
    session.commit()

    result = get_inventory_item("MOTOR-001", session)

    assert result is not None
    assert result.sku == "MOTOR-001"
    assert result.available_quantity == 4


def test_get_missing_inventory_item(session):
    result = get_inventory_item("UNKNOWN-999", session)

    assert result is None
