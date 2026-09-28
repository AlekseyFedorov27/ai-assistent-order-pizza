# tests/test_order_confirmation.py
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from langchain_core.messages import ToolMessage
from langgraph.errors import GraphInterrupt

from modules.context import current_user_id
from modules.middleware.order_confirmation import HITLManager


# ---------- фикстуры ----------

@pytest.fixture
def user_id_1():
    token = current_user_id.set(1)
    try:
        yield 1
    finally:
        current_user_id.reset(token)


@pytest.fixture
def user_id_none():
    token = current_user_id.set(None)
    try:
        yield None
    finally:
        current_user_id.reset(token)


# ---------- вспомогательные классы ----------

def make_request(
    name="save_order",
    args=None,
    tool_call_id="call-1",
    thread_id="test-thread",
    user_id=1,
):
    args = args if args is not None else {
        "items": [{"name": "Маргарита", "quantity": 2}],
        "address": "Победа 22",
        "status": "новый",
    }
    request = SimpleNamespace()
    request.tool_call = {
        "name": name,
        "args": args,
        "id": tool_call_id,
    }
    request.runtime = SimpleNamespace(
        config={
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            }
        }
    )
    return request


def make_handler():
    calls = []

    def handler(request):
        calls.append(request)
        return ToolMessage(
            content="ok",
            tool_call_id=request.tool_call["id"],
            name=request.tool_call["name"],
        )

    handler.calls = calls
    return handler


def make_session_local_mock():
    """Контекстный менеджер: with SessionLocal() as session."""
    session = MagicMock(name="session")
    cm = MagicMock(name="SessionLocal()")
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False

    factory = MagicMock(name="SessionLocal", return_value=cm)
    return factory, session


def expected_preview(request):
    args = request.tool_call["args"]
    items = args["items"]
    return {
        "items": [
            {
                "name": item["name"],
                "quantity": item["quantity"],
                "price": "339",
                "subtotal": str(339 * item["quantity"]),
            }
            for item in items
        ],
        "address": args["address"],
        "status": args.get("status", "новый"),
        "total": str(sum(339 * item["quantity"] for item in items)),
    }


# ---------- тесты ----------

def test_non_save_order_passes_through():
    middleware = HITLManager()
    handler = make_handler()
    request = make_request(name="other_tool", args={})

    result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert result.content == "ok"
    assert handler.calls == [request]


def test_save_order_requires_address():
    middleware = HITLManager()
    handler = make_handler()
    request = make_request(args={"items": [], "address": "   "})

    with patch(
        "modules.middleware.order_confirmation.SessionLocal",
    ) as SessionLocal, patch(
        "modules.middleware.order_confirmation.OrderService",
    ) as Service, patch(
        "modules.middleware.order_confirmation.interrupt",
    ) as interrupt:
        result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert "Адрес доставки не указан" in result.content
    assert handler.calls == []
    SessionLocal.assert_not_called()
    Service.assert_not_called()
    interrupt.assert_not_called()


def test_save_order_requires_user_id(user_id_none):
    middleware = HITLManager()
    handler = make_handler()
    request = make_request()

    with patch(
        "modules.middleware.order_confirmation.SessionLocal",
    ) as SessionLocal, patch(
        "modules.middleware.order_confirmation.OrderService",
    ) as Service, patch(
        "modules.middleware.order_confirmation.interrupt",
    ) as interrupt:
        result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert "Не удалось определить пользователя" in result.content
    assert handler.calls == []
    SessionLocal.assert_not_called()
    Service.assert_not_called()
    interrupt.assert_not_called()


def test_save_order_approve_calls_handler(user_id_1):
    middleware = HITLManager()
    handler = make_handler()
    request = make_request()

    SessionLocal, session = make_session_local_mock()
    preview = expected_preview(request)

    with patch(
        "modules.middleware.order_confirmation.SessionLocal",
        SessionLocal,
    ), patch(
        "modules.middleware.order_confirmation.OrderService",
    ) as Service, patch(
        "modules.middleware.order_confirmation.interrupt",
        return_value={"approved": True},
    ) as interrupt:
        Service.return_value.save_pending_order.return_value = (42, preview)

        result = middleware.wrap_tool_call(request, handler)

    # handler вызван один раз с тем же request
    assert handler.calls == [request]
    assert isinstance(result, ToolMessage)
    assert result.content == "ok"

    # save_pending_order вызван с корректными параметрами
    Service.assert_called_once()
    kwargs = Service.return_value.save_pending_order.call_args.kwargs
    assert kwargs["user_id"] == 1
    assert kwargs["thread_id"] == "test-thread"
    assert kwargs["tool_call_id"] == "call-1"
    assert kwargs["address"] == "Победа 22"
    assert kwargs["status"] == "новый"
    assert kwargs["config"] == {
        "configurable": {
            "user_id": 1,
            "thread_id": "test-thread",
        }
    }

    # interrupt вызван с preview + pending_id
    interrupt.assert_called_once_with({"pending_id": 42, **preview})


def test_save_order_reject_returns_cancel_message(user_id_1):
    middleware = HITLManager()
    handler = make_handler()
    request = make_request()

    SessionLocal, session = make_session_local_mock()
    preview = expected_preview(request)

    with patch(
        "modules.middleware.order_confirmation.SessionLocal",
        SessionLocal,
    ), patch(
        "modules.middleware.order_confirmation.OrderService",
    ) as Service, patch(
        "modules.middleware.order_confirmation.interrupt",
        return_value={"approved": False},
    ) as interrupt:
        Service.return_value.save_pending_order.return_value = (42, preview)

        result = middleware.wrap_tool_call(request, handler)

    # handler НЕ вызван — save_order не должен выполниться
    assert handler.calls == []

    assert isinstance(result, ToolMessage)
    assert result.content == "Заказ отменён."

    # save_pending_order и interrupt всё равно были вызваны
    Service.return_value.save_pending_order.assert_called_once()
    interrupt.assert_called_once_with({"pending_id": 42, **preview})


def test_save_order_graph_interrupt_propagates(user_id_1):
    middleware = HITLManager()
    handler = make_handler()
    request = make_request()

    SessionLocal, session = make_session_local_mock()
    preview = expected_preview(request)

    with patch(
        "modules.middleware.order_confirmation.SessionLocal",
        SessionLocal,
    ), patch(
        "modules.middleware.order_confirmation.OrderService",
    ) as Service, patch(
        "modules.middleware.order_confirmation.interrupt",
        side_effect=GraphInterrupt(),
    ):
        Service.return_value.save_pending_order.return_value = (42, preview)

        with pytest.raises(GraphInterrupt):
            middleware.wrap_tool_call(request, handler)

    # handler не должен был выполниться — interrupt прервал выполнение
    assert handler.calls == []


def test_save_order_service_error_returns_tool_message(user_id_1):
    """Если OrderService.save_pending_order падает — middleware
    возвращает ToolMessage с текстом ошибки, а не пробрасывает исключение."""

    middleware = HITLManager()
    handler = make_handler()
    request = make_request()

    SessionLocal, session = make_session_local_mock()

    with patch(
        "modules.middleware.order_confirmation.SessionLocal",
        SessionLocal,
    ), patch(
        "modules.middleware.order_confirmation.OrderService",
    ) as Service, patch(
        "modules.middleware.order_confirmation.interrupt",
    ) as interrupt:
        Service.return_value.save_pending_order.side_effect = (
            RuntimeError("boom")
        )

        result = middleware.wrap_tool_call(request, handler)

    assert handler.calls == []
    assert isinstance(result, ToolMessage)
    assert "Не удалось подготовить заказ" in result.content
    assert "boom" in result.content

    interrupt.assert_not_called()