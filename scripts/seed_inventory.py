
from sqlalchemy import select

from procurement_assistant.database.connection import SessionLocal
from procurement_assistant.database.models import InventoryItemDB


INITIAL_ITEMS = [
    {
        "sku": "MOTOR-001",
        "name": "Industrial Motor",
        "available_quantity": 4,
        "minimum_quantity": 5,
    },
    {
        "sku": "BEARING-002",
        "name": "Industrial Bearing",
        "available_quantity": 25,
        "minimum_quantity": 10,
    },
    {
        "sku": "SENSOR-003",
        "name": "Temperature Sensor",
        "available_quantity": 2,
        "minimum_quantity": 8,
    },
]


def main() -> None:
    with SessionLocal() as session:
        for item_data in INITIAL_ITEMS:
            statement = select(InventoryItemDB).where(
                InventoryItemDB.sku == item_data["sku"]
            )
            existing_item = session.scalar(statement)

            if existing_item is None:
                session.add(InventoryItemDB(**item_data))

        session.commit()

    print("Initial inventory data is ready.")


if __name__ == "__main__":
    main()
