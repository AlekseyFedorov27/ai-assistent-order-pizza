from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from ..database.models import PendingOrderDB


class PendingOrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        user_id: int,
        thread_id: str,
        tool_call_id: str | None,
        items: list[dict],
        address: str,
        status: str,
        preview: dict,
        total: Decimal,                 
        config: dict,
        ttl_minutes: int = 30,
    ) -> PendingOrderDB:
        row = PendingOrderDB(
            user_id=user_id,
            thread_id=thread_id,
            tool_call_id=tool_call_id,
            items=items,
            address=address,
            status=status,
            preview=preview,
            total=total,               
            config=config,
            state="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get_pending_by_user(self, user_id: int) -> Optional[PendingOrderDB]:
        return (
            self.session.query(PendingOrderDB)
            .filter(
                PendingOrderDB.user_id == user_id,
                PendingOrderDB.state == "pending",
            )
            .order_by(PendingOrderDB.created_at.desc())
            .first()
        )

    def mark(self, pending_id: str, state: str) -> None:
        row = self.session.get(PendingOrderDB, pending_id)
        if row is not None:
            row.state = state
            self.session.flush()

    def delete_expired(self, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        (
            self.session.query(PendingOrderDB)
            .filter(
                PendingOrderDB.user_id == user_id,
                PendingOrderDB.state == "pending",
                PendingOrderDB.expires_at < now,
            )
            .update({"state": "expired"})
        )
        self.session.flush()