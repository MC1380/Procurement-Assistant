from sqlalchemy import select

from procurement_assistant.database.connection import SessionLocal
from procurement_assistant.database.models import (
    ProductCategoryDB,
    ProductAttributeDB,
)


PRODUCT_KNOWLEDGE = {
    "industrial_motor": {
        "display_name": "Industrial Motor",
        "attributes": [
            {
                "key": "power",
                "name": "Power",
                "description": "Motor rated power in kilowatts.",
                "required": True,
            },
            {
                "key": "voltage",
                "name": "Voltage",
                "description": "Motor operating voltage.",
                "required": True,
            },
            {
                "key": "rpm",
                "name": "Rotational Speed",
                "description": "Motor speed in revolutions per minute.",
                "required": True,
            },
        ],
    },
    "industrial_bearing": {
        "display_name": "Industrial Bearing",
        "attributes": [
            {
                "key": "inner_diameter",
                "name": "Inner Diameter",
                "description": "Bearing inner diameter in millimeters.",
                "required": True,
            },
            {
                "key": "outer_diameter",
                "name": "Outer Diameter",
                "description": "Bearing outer diameter in millimeters.",
                "required": True,
            },
            {
                "key": "width",
                "name": "Width",
                "description": "Bearing width in millimeters.",
                "required": True,
            },
            {
                "key": "bearing_type",
                "name": "Bearing Type",
                "description": "Bearing design or type.",
                "required": True,
            },
        ],
    },
    "industrial_pump": {
        "display_name": "Industrial Pump",
        "attributes": [
            {
                "key": "flow_rate",
                "name": "Flow Rate",
                "description": "Required fluid flow rate.",
                "required": True,
            },
            {
                "key": "head",
                "name": "Head",
                "description": "Required pump head.",
                "required": True,
            },
            {
                "key": "fluid_type",
                "name": "Fluid Type",
                "description": "Type of fluid handled by the pump.",
                "required": True,
            },
            {
                "key": "operating_temperature",
                "name": "Operating Temperature",
                "description": "Fluid operating temperature.",
                "required": True,
            },
        ],
    },
}


def seed_product_knowledge() -> None:
    with SessionLocal() as session:
        for category_key, category_data in PRODUCT_KNOWLEDGE.items():

            category = session.get(
                ProductCategoryDB,
                category_key,
            )

            if category is None:
                category = ProductCategoryDB(
                    category_key=category_key,
                    display_name=category_data["display_name"],
                )
                session.add(category)

            for attribute_data in category_data["attributes"]:
                statement = select(ProductAttributeDB).where(
                    ProductAttributeDB.category_key == category_key,
                    ProductAttributeDB.attribute_key == attribute_data["key"],
                )

                existing_attribute = session.scalar(statement)

                if existing_attribute is None:
                    session.add(
                        ProductAttributeDB(
                            category_key=category_key,
                            attribute_key=attribute_data["key"],
                            display_name=attribute_data["name"],
                            description=attribute_data["description"],
                            is_required=attribute_data["required"],
                        )
                    )

        session.commit()

    print("Product knowledge seeded successfully.")


if __name__ == "__main__":
    seed_product_knowledge()