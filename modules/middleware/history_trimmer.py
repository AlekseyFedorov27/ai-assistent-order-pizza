from langchain.agents.middleware import before_model
from langchain.agents import AgentState
from langgraph.runtime import Runtime
from typing import Any
from langchain.messages import trim_messages
from ..model import model

@before_model 
def history_trimmer(state: AgentState, runtime: Runtime) -> dict[str, Any]:
    """Обрезает историю сообщений до 500 токенов"""
    try:
        # Обрезаем сообщения до 500 токенов
        new_messages = trim_messages(
            messages=state['messages'],
            max_tokens=500,
            token_counter=model,
            include_system=True
        )
        
        # Возвращаем обрезанные сообщения
        return {'messages': new_messages}
    except Exception as e:
        # В случае ошибки возвращаем исходные сообщения
        print(f"⚠️ Ошибка обрезки истории: {e}")
        return {'messages': state['messages']}