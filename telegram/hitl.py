# telegram/hitl.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from modules.database import SessionLocal
from modules.repositories.pending_order import PendingOrderRepository


@dataclass
class PendingOrder:
    """DTO поверх PendingOrderDB: только то, что нужно resume_agent."""
    id: int
    config: dict[str, Any]
    preview: dict[str, Any]
    expires_at: datetime


def get_pending_order(user_id: int) -> PendingOrder | None:
    """
    Возвращает активное pending-подтверждение пользователя или None.
    Просроченные помечает как expired и не возвращает.
    """
    with SessionLocal() as session:
        repo = PendingOrderRepository(session)
        repo.delete_expired(user_id)
        session.commit()                         # фиксируем expired

        row = repo.get_pending_by_user(user_id)
        if row is None:
            return None

        return PendingOrder(
            id=row.id,
            config=row.config,
            preview=row.preview,
            expires_at=row.expires_at,
        )


def clear_pending_order(user_id: int, state: str = "approved") -> None:
    """
    Помечает активное pending-подтверждение пользователя
    как обработанное (approved / rejected / expired).
    После этого get_pending_order его уже не вернёт.
    """
    with SessionLocal() as session:
        repo = PendingOrderRepository(session)
        row = repo.get_pending_by_user(user_id)
        if row is not None:
            repo.mark(row.id, state)
        session.commit()


# совместимость со старым импортом, если он где-то остался
delete_pending_order = clear_pending_order