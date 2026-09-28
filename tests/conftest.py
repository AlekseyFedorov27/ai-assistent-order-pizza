# tests/conftest.py
from typing import Any, Optional

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.checkpoint.memory import MemorySaver
from pydantic import PrivateAttr

from modules.database import Base

# ВАЖНО: импортируем модели, чтобы они зарегистрировались в Base.metadata.
# Иначе Base.metadata.create_all(engine) не создаст таблицы products/orders/etc.
import modules.database.models  # noqa: F401

# Если ProductDB лежит в отдельном модуле, который не реэкспортится через
# modules.database.models, раскомментируйте нужное:
# from modules.database.models.product import ProductDB  # noqa: F401

from modules.context import current_user_id


# ---------- in-memory DB ----------

@pytest.fixture
def engine():
    """Изолированный in-memory SQLite-движок на один тест."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(eng)
        eng.dispose()


@pytest.fixture
def SessionLocal(engine):
    """Фабрика сессий, привязанная к тестовому движку."""
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest.fixture
def session(SessionLocal):
    """Готовая сессия для unit-тестов, которые работают с ней напрямую."""
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture(autouse=True)
def _patch_session_local(monkeypatch, SessionLocal):
    """
    Подменяет SessionLocal во всех модулях, где он импортирован,
    чтобы сервисы и тулы ходили в тестовую БД.
    """
    targets = (
        "modules.database.SessionLocal",
        "modules.middleware.order_confirmation.SessionLocal",
        "modules.tools.order.SessionLocal",
        "modules.tools.user.SessionLocal",
        "modules.tools.retriever.SessionLocal",
    )
    for target in targets:
        try:
            monkeypatch.setattr(target, SessionLocal)
        except AttributeError:
            # модуль ещё не импортирован или SessionLocal там не объявлен
            pass


# ---------- user_id (ContextVar) ----------

@pytest.fixture
def user_id_1():
    """Устанавливает current_user_id = 1 на время теста."""
    token = current_user_id.set(1)
    try:
        yield 1
    finally:
        current_user_id.reset(token)


@pytest.fixture
def user_id_none():
    """Устанавливает current_user_id = None на время теста."""
    token = current_user_id.set(None)
    try:
        yield None
    finally:
        current_user_id.reset(token)


# ---------- мок LLM для Agent Evaluation ----------

class FakeToolCallingModel(BaseChatModel):
    """
    Мок-LLM, который отдаёт заранее заданную последовательность
    AIMessage'ей. Полноценный BaseChatModel: поддерживает bind,
    bind_tools, invoke, ainvoke.

    По исчерпании сценария возвращает AIMessage(content="Готово."),
    что корректно завершает цикл tool-calling в create_agent.
    """

    script: list[AIMessage]
    _index: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "fake-tool-calling"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self._index < len(self.script):
            msg = self.script[self._index]
            self._index += 1
        else:
            msg = AIMessage(content="Готово.")

        return ChatResult(
            generations=[ChatGeneration(message=msg)],
        )

    def bind_tools(self, tools, **kwargs):
        return self

    def bind(self, **kwargs):
        return self


@pytest.fixture
def make_scripted_llm():
    def _make(script):
        return FakeToolCallingModel(script=list(script))
    return _make