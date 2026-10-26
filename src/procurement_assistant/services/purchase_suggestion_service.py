
"""Services for creating and retrieving purchase suggestions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from procurement_assistant.database.models import PurchaseSuggestionDB
from procurement_assistant.models import (
    PurchaseSuggestion,
    SuggestionStatus,
)


def create_purchase_suggestion(
    suggestion: PurchaseSuggestion,
    session: Session,
) -> PurchaseSuggestion:
    """Save a purchase suggestion and return the saved data."""

    db_suggestion = PurchaseSuggestionDB(
        suggestion_id=suggestion.suggestion_id,
        item_name=suggestion.item_name,
        description=suggestion.description,
        requested_quantity=suggestion.requested_quantity,
        reason=suggestion.reason,
        requested_by=suggestion.requested_by,
        status=suggestion.status.value,
        manager_comment=suggestion.manager_comment,
    )

    try:
        session.add(db_suggestion)
        session.commit()
        session.refresh(db_suggestion)
    except Exception:
        session.rollback()
        raise

    return PurchaseSuggestion(
        suggestion_id=db_suggestion.suggestion_id,
        item_name=db_suggestion.item_name,
        description=db_suggestion.description,
        requested_quantity=db_suggestion.requested_quantity,
        reason=db_suggestion.reason,
        requested_by=db_suggestion.requested_by,
        status=SuggestionStatus(db_suggestion.status),
        manager_comment=db_suggestion.manager_comment,
    )


def get_purchase_suggestion(
    suggestion_id: str,
    session: Session,
) -> PurchaseSuggestion | None:
    """Retrieve a purchase suggestion by its unique ID."""

    statement = select(PurchaseSuggestionDB).where(
        PurchaseSuggestionDB.suggestion_id == suggestion_id
    )
    db_suggestion = session.scalar(statement)

    if db_suggestion is None:
        return None

    return PurchaseSuggestion(
        suggestion_id=db_suggestion.suggestion_id,
        item_name=db_suggestion.item_name,
        description=db_suggestion.description,
        requested_quantity=db_suggestion.requested_quantity,
        reason=db_suggestion.reason,
        requested_by=db_suggestion.requested_by,
        status=SuggestionStatus(db_suggestion.status),
        manager_comment=db_suggestion.manager_comment,
    )


def review_purchase_suggestion(
    suggestion_id: str,
    decision: SuggestionStatus,
    manager_comment: str,
    session: Session,
) -> PurchaseSuggestion:
    """Approve or reject a pending purchase suggestion."""

    if decision not in {
        SuggestionStatus.APPROVED,
        SuggestionStatus.REJECTED,
    }:
        raise ValueError("Decision must be APPROVED or REJECTED.")

    if not manager_comment.strip():
        raise ValueError("Manager comment cannot be empty.")

    statement = select(PurchaseSuggestionDB).where(
        PurchaseSuggestionDB.suggestion_id == suggestion_id
    )
    db_suggestion = session.scalar(statement)

    if db_suggestion is None:
        raise ValueError(
            f"Purchase suggestion not found: {suggestion_id}"
        )

    if db_suggestion.status != SuggestionStatus.PENDING.value:
        raise ValueError(
            "Only pending suggestions can be reviewed."
        )

    db_suggestion.status = decision.value
    db_suggestion.manager_comment = manager_comment.strip()

    try:
        session.commit()
        session.refresh(db_suggestion)
    except Exception:
        session.rollback()
        raise

    return PurchaseSuggestion(
        suggestion_id=db_suggestion.suggestion_id,
        item_name=db_suggestion.item_name,
        description=db_suggestion.description,
        requested_quantity=db_suggestion.requested_quantity,
        reason=db_suggestion.reason,
        requested_by=db_suggestion.requested_by,
        status=SuggestionStatus(db_suggestion.status),
        manager_comment=db_suggestion.manager_comment,
    )
