# modules/agent.py
from typing import Any

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.types import Command

from telegram.hitl import get_pending_order, clear_pending_order
from . import tools
from .model import model
from .system_prompt import system_prompt
from .middleware import hitl
from .database import (
    AgentPersistence,
    SessionLocal,
)
from .services import UserService
from .context import current_user_id


persistence = AgentPersistence()


agent: Any = create_agent(
    model,
    tools=tools.AGENT_TOOLS,
    checkpointer=persistence.checkpointer,
    store=persistence.store,
    system_prompt=system_prompt,
    middleware=(hitl,),
)


def get_agent_response(message: str, user_id: int):
    token = current_user_id.set(user_id)
    try:
        thread_id = f"user:{user_id}"
        runtime_config = {
            "configurable": {
                "user_id": user_id,
                "thread_id": thread_id,
            }
        }

        pending = get_pending_order(user_id)
        if pending is not None:
            approved = message.strip().lower() in {
                "да", "yes", "подтверждаю", "ок", "ok",
            }
            return resume_agent(user_id, {"approved": approved})

        with SessionLocal() as session:
            service = UserService(session=session, store=persistence.store)
            service.load_user_to_store(user_id)

        return agent.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=runtime_config,
        )
    finally:
        current_user_id.reset(token)


def resume_agent(user_id: int, decision: dict):
    token = current_user_id.set(user_id)
    try:
        pending = get_pending_order(user_id)
        if pending is None:
            raise ValueError("Ожидающее подтверждение заказа не найдено.")

        response = agent.invoke(
            Command(resume=decision),
            config=pending.config,
        )

        clear_pending_order(
            user_id,
            state="approved" if decision.get("approved") else "rejected",
        )
        return response
    finally:
        current_user_id.reset(token)