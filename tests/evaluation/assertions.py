# tests/evaluation/assertions.py
from collections.abc import Iterable
from typing import Any


def extract_tool_calls(messages: Iterable[Any]) -> list[dict]:
    """
    Возвращает список tool_call'ов из AIMessage-ов.
    Каждый элемент: {"name": str, "args": dict, "id": str}
    """
    calls: list[dict] = []
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", None) or []
        for tc in tool_calls:
            calls.append({
                "name": tc["name"],
                "args": tc.get("args", {}),
                "id": tc.get("id"),
            })
    return calls


def called_tools(messages: Iterable[Any]) -> list[str]:
    return [c["name"] for c in extract_tool_calls(messages)]


def assert_tool_called(
    messages: Iterable[Any],
    name: str,
    times: int | None = None,
) -> list[dict]:
    calls = [c for c in extract_tool_calls(messages) if c["name"] == name]
    assert calls, f"Ожидался вызов тула {name!r}, но его нет"
    if times is not None:
        assert len(calls) == times, (
            f"Ожидалось {times} вызов(ов) {name!r}, "
            f"получено {len(calls)}"
        )
    return calls


def assert_tool_not_called(messages: Iterable[Any], name: str) -> None:
    names = called_tools(messages)
    assert name not in names, (
        f"Тул {name!r} не должен был вызываться, "
        f"но был вызван. Все вызовы: {names}"
    )


def assert_tool_order(
    messages: Iterable[Any],
    expected: list[str],
) -> None:
    """
    Проверяет, что среди вызовов есть подпоследовательность expected
    в указанном порядке.
    """
    names = called_tools(messages)

    i = 0
    for name in names:
        if i < len(expected) and name == expected[i]:
            i += 1

    assert i == len(expected), (
        f"Ожидался порядок {expected}, "
        f"но получилось {names}"
    )


def extract_ai_tool_calls(messages):
    """
    Возвращает список tool_call'ов ТОЛЬКО из AIMessage —
    то есть намерения LLM, без учёта того, был ли вызван ToolNode.
    """
    calls = []
    for msg in messages:
        if type(msg).__name__ != "AIMessage":
            continue
        for tc in getattr(msg, "tool_calls", None) or []:
            calls.append({
                "name": tc["name"],
                "args": tc.get("args", {}),
                "id": tc.get("id"),
            })
    return calls


def assert_tool_intent(messages, name, times=None):
    calls = [c for c in extract_ai_tool_calls(messages) if c["name"] == name]
    assert calls, f"LLM не собирался вызывать тул {name!r}"
    if times is not None:
        assert len(calls) == times, (
            f"Ожидалось {times} намерений вызвать {name!r}, "
            f"получено {len(calls)}"
        )
    return calls    