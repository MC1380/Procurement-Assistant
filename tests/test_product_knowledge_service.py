import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from procurement_assistant.database.connection import Base
from procurement_assistant.database.models import (
    ProductCategoryDB,
    ProductAttributeDB,
)
from procurement_assistant.services.product_knowledge_service import (
    get_product_attributes,
)


@pytest.fixture
def session():
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


def test_get_product_attributes(session):
    session.add(
        ProductCategoryDB(
            category_key="industrial_motor",
            display_name="Industrial Motor",
        )
    )

    session.add_all(
        [
            ProductAttributeDB(
                category_key="industrial_motor",
                attribute_key="power",
                display_name="Power",
                is_required=True,
            ),
            ProductAttributeDB(
                category_key="industrial_motor",
                attribute_key="voltage",
                display_name="Voltage",
                is_required=True,
            ),
        ]
    )

    session.commit()

    result = get_product_attributes(
        "industrial_motor",
        session,
    )

    assert result is not None
    assert len(result) == 2
    assert result[0].attribute_key == "power"
    assert result[1].attribute_key == "voltage"
    assert all(attribute.is_required for attribute in result)


def test_get_attributes_for_unknown_category(session):
    result = get_product_attributes(
        "unknown_category",
        session,
    )

    assert result is None


def test_category_without_attributes_returns_empty_list(session):
    session.add(
        ProductCategoryDB(
            category_key="industrial_motor",
            display_name="Industrial Motor",
        )
    )
    session.commit()

    result = get_product_attributes(
        "industrial_motor",
        session,
    )

    assert result == []