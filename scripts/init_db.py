from procurement_assistant.database.connection import Base, engine
from procurement_assistant.database.models import InventoryItemDB, PurchaseSuggestionDB, ProductCategoryDB, ProductAttributeDB 


def main() -> None:
    # Create database tables defined in the imported models.
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    main()
