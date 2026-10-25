
from sqlalchemy import CheckConstraint, Integer, String
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
