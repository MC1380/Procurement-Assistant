
from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from procurement_assistant.database.connection import Base


class InventoryItemDB(Base):
    __tablename__ = "inventory_items"

    __table_args__ = (
        CheckConstraint(
            "available_quantity >= 0",
            name="check_available_quantity_non_negative",
        ),
        CheckConstraint(
            "minimum_quantity >= 0",
            name="check_minimum_quantity_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    available_quantity: Mapped[int] = mapped_column(Integer)
    minimum_quantity: Mapped[int] = mapped_column(Integer)



class PurchaseSuggestionDB(Base):
    """Database model for new-item purchase suggestions."""

    __tablename__ = "purchase_suggestions"

    __table_args__ = (
        CheckConstraint(
            "requested_quantity > 0",
            name="check_suggestion_quantity_positive",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    suggestion_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )

    item_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    requested_by: Mapped[str] = mapped_column(String(100))

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )

    manager_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )