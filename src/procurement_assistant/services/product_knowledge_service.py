from sqlalchemy import select
from sqlalchemy.orm import Session

from procurement_assistant.database.models import (
    ProductCategoryDB,
    ProductAttributeDB,
)
from procurement_assistant.models import ProductAttribute


def get_product_attributes(
    category_key: str,
    session: Session,
) -> list[ProductAttribute] | None:
    """
    Return technical attributes for a product category.

    Returns None if the category does not exist.
    Returns an empty list if the category has no attributes.
    """

    category = session.get(ProductCategoryDB, category_key)

    if category is None:
        return None

    statement = (
        select(ProductAttributeDB)
        .where(ProductAttributeDB.category_key == category_key)
        .order_by(ProductAttributeDB.id)
    )

    db_attributes = session.scalars(statement).all()

    return [
        ProductAttribute(
            category_key=attribute.category_key,
            attribute_key=attribute.attribute_key,
            display_name=attribute.display_name,
            description=attribute.description,
            is_required=attribute.is_required,
        )
        for attribute in db_attributes
    ]