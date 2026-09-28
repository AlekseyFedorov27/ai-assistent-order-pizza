# tests/evaluation/test_agent_evaluation.py
from collections.abc import Iterable
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command


# ---------- хелперы ----------

def extract_tool_calls(messages: Iterable[Any]) -> list[dict]:
    """tool_call'ы из AIMessage (намерения LLM)."""
    calls: list[dict] = []
    for msg in messages:
        for tc in getattr(msg, "tool_calls", None) or []:
            calls.append({
                "name": tc["name"],
                "args": tc.get("args", {}),
                "id": tc.get("id"),
            })
    return calls


def called_tools(messages: Iterable[Any]) -> list[str]:
    return [c["name"] for c in extract_tool_calls(messages)]


def assert_tool_intent(messages, name, times=None):
    calls = [c for c in extract_tool_calls(messages) if c["name"] == name]
    assert calls, f"LLM не собирался вызывать тул {name!r}"
    if times is not None:
        assert len(calls) == times
    return calls


def assert_tool_not_intent(messages, name):
    names = called_tools(messages)
    assert name not in names, (
        f"LLM не должен был планировать вызов {name!r}. Все: {names}"
    )


def assert_tool_order(messages, expected):
    names = called_tools(messages)
    i = 0
    for name in names:
        if i < len(expected) and name == expected[i]:
            i += 1
    assert i == len(expected), (
        f"Ожидался порядок {expected}, получилось {names}"
    )


# ---------- Сценарий 1: intent, а не выполнение ----------

def test_eval_order_two_pepperoni(agent_factory, monkeypatch):
    script = [
        AIMessage(
            content="",
            tool_calls=[{
                "name": "get_pizza_price",
                "args": {"name": "Пепперони"},
                "id": "call-1",
            }],
        ),
        AIMessage(
            content="",
            tool_calls=[{
                "name": "save_order",
                "args": {
                    "items": [{"name": "Пепперони", "quantity": 2}],
                    "address": "Москва, Ленина 10",
                    "status": "новый",
                },
                "id": "call-2",
            }],
        ),
        AIMessage(content="Заказ оформлен."),
    ]

    agent, _, _, config = agent_factory(script)

    # HITL сам вызовет interrupt, но мы не resume — проверяем intent
    monkeypatch.setattr("builtins.input", lambda _: "нет")

    result = agent.invoke(
        {"messages": [HumanMessage(content="Хочу две Пепперони")]},
        config,
    )
    messages = result["messages"]

    # get_pizza_price — реально выполнен
    from langchain_core.messages import ToolMessage
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert any(
        getattr(m, "name", "") == "get_pizza_price"
        for m in tool_messages
    ), "get_pizza_price должен был выполниться"

    # save_order — только намерение LLM (граф остановлен на HITL)
    intents = assert_tool_intent(messages, "save_order")
    items = intents[0]["args"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Пепперони"
    assert items[0]["quantity"] == 2


# ---------- Сценарий 2 ----------

def test_eval_price_question(agent_factory):
    script = [
        AIMessage(
            content="",
            tool_calls=[{
                "name": "get_pizza_price",
                "args": {"name": "Песта"},
                "id": "call-1",
            }],
        ),
        AIMessage(content="Песта стоит 800 ₽."),
    ]

    agent, _, _, config = agent_factory(script)
    result = agent.invoke(
        {"messages": [HumanMessage(content="Сколько стоит Песта?")]},
        config,
    )
    messages = result["messages"]

    assert_tool_intent(messages, "get_pizza_price", times=1)
    assert_tool_not_intent(messages, "save_order")


# ---------- Сценарий 3 ----------

def test_eval_ingredients_question(agent_factory):
    script = [
        AIMessage(
            content="",
            tool_calls=[{
                "name": "retriever",
                "args": {"query": "состав пиццы Песта"},
                "id": "call-1",
            }],
        ),
        AIMessage(content="Песта состоит из ..."),
    ]

    agent, _, _, config = agent_factory(script)
    result = agent.invoke(
        {"messages": [HumanMessage(content="Из чего состоит Песта?")]},
        config,
    )
    messages = result["messages"]

    assert_tool_intent(messages, "retriever", times=1)
    assert_tool_not_intent(messages, "save_order")


# ---------- Сценарий 4 ----------

def test_eval_user_last_orders(agent_factory):
    script = [
        AIMessage(
            content="",
            tool_calls=[{
                "name": "get_user_last_orders",
                "args": {},
                "id": "call-1",
            }],
        ),
        AIMessage(content="Ваши последние заказы: ..."),
    ]

    agent, _, _, config = agent_factory(script)
    result = agent.invoke(
        {"messages": [HumanMessage(content="Какие у меня были заказы?")]},
        config,
    )
    messages = result["messages"]

    assert_tool_intent(messages, "get_user_last_orders", times=1)
    assert_tool_not_intent(messages, "save_order")


# ---------- Сценарий 5: HITL approve ----------

def test_eval_hitl_approve_creates_order(agent_factory, user_id_1):
    from langchain_core.messages import AIMessage, HumanMessage
    from langgraph.types import Command

    script = [
        AIMessage(
            content="",
            tool_calls=[{
                "name": "save_order",
                "args": {
                    "items": [{"name": "Маргарита", "quantity": 2}],
                    "address": "Победа 22",
                    "status": "новый",
                },
                "id": "call-1",
            }],
        ),
        AIMessage(content="Заказ сохранён."),
    ]

    agent, _, _, config = agent_factory(script)

    first = agent.invoke(
        {"messages": [HumanMessage(content="Закажи две Маргариты")]},
        config,
    )
    assert "__interrupt__" in first, (
        f"Ожидался interrupt от HITL, но получили: {list(first.keys())}"
    )

    agent.invoke(
        Command(resume={"approved": True}),
        config,
    )

    from modules.database import SessionLocal
    from modules.database.models import OrderDB

    with SessionLocal() as session:
        orders = session.query(OrderDB).all()
        assert len(orders) == 1
        assert orders[0].address == "Победа 22"


# ---------- Сценарий 6: HITL reject ----------

def test_eval_hitl_reject_does_not_create_order(agent_factory, user_id_1):
    script = [
        AIMessage(
            content="",
            tool_calls=[{
                "name": "save_order",
                "args": {
                    "items": [{"name": "Маргарита", "quantity": 2}],
                    "address": "Победа 22",
                    "status": "новый",
                },
                "id": "call-1",
            }],
        ),
        AIMessage(content="Заказ отменён."),
    ]

    agent, _, _, config = agent_factory(script)

    first = agent.invoke(
        {"messages": [HumanMessage(content="Закажи две Маргариты")]},
        config,
    )
    assert "__interrupt__" in first

    agent.invoke(
        Command(resume={"approved": False}),
        config,
    )

    from modules.database import SessionLocal
    from modules.database.models import OrderDB

    with SessionLocal() as session:
        assert session.query(OrderDB).count() == 0