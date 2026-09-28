# tests/evaluation/conftest.py
import pytest

from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture
def agent_factory(make_scripted_llm, SessionLocal, monkeypatch):
    """
    Собирает агента так же, как modules/agent.py, но с мок-LLM
    и in-memory БД.
    """
    from langchain.agents import create_agent
    from modules import tools as tools_module
    from modules.system_prompt import system_prompt
    from modules.middleware import hitl

    def _build(script, *, thread_id="eval-thread"):
        llm = make_scripted_llm(script)
        checkpointer = MemorySaver()

        agent = create_agent(
            llm,
            tools=tools_module.AGENT_TOOLS,
            checkpointer=checkpointer,
            system_prompt=system_prompt,
            middleware=(hitl,),
        )

        config = {"configurable": {"thread_id": thread_id}}
        return agent, llm, checkpointer, config

    return _build


@pytest.fixture(autouse=True)
def _seed_products_for_eval(engine):
    from sqlalchemy.orm import Session
    from modules.database.models import ProductDB

    session = Session(bind=engine)
    try:
        session.add_all([
            ProductDB(name="Маргарита", price=339),
            ProductDB(name="Пепперони", price=350),
            ProductDB(name="Песта", price=800),
        ])
        session.commit()
    finally:
        session.close()
    yield