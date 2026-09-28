# modules/middleware/order_confirmation.py
from langchain.agents.middleware import AgentMiddleware
from langchain.messages import ToolMessage
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
import traceback

from ..database import SessionLocal
from ..services import OrderService
from ..context import current_user_id


class HITLManager(AgentMiddleware):
    """
    Перехватывает вызов save_order:
      1. считает цену и сохраняет pending в БД (через OrderService),
      2. прерывает граф через interrupt(preview),
      3. после resume — либо отклоняет, либо пропускает вызов дальше.
    """

    def wrap_tool_call(self, request, handler):
        tool_call = request.tool_call

        if tool_call["name"] != "save_order":
            return handler(request)

        tool_call_id = tool_call.get("id")
        tool_name = tool_call["name"]
        args = tool_call["args"]

        try:
            address = (args.get("address") or "").strip()

            if not address:
                return ToolMessage(
                    content=(
                        "Адрес доставки не указан. "
                        "Спроси у пользователя адрес и вызови save_order снова."
                    ),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )

            user_id = current_user_id.get()
            if user_id is None:
                return ToolMessage(
                    content="Не удалось определить пользователя. Попробуйте ещё раз.",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )

            config = request.runtime.config
            configurable = config.get("configurable", {})
            thread_id = configurable.get("thread_id")

            safe_config = {
                "configurable": {
                    "user_id": configurable.get("user_id"),
                    "thread_id": thread_id,
                }
            }

            with SessionLocal() as session:
                service = OrderService(session)
                pending_id, preview = service.save_pending_order(
                    user_id=user_id,
                    thread_id=thread_id,
                    tool_call_id=tool_call_id,
                    items=args["items"],
                    address=address,
                    status=args.get("status", "новый"),
                    config=safe_config,
                )

            decision = interrupt({"pending_id": pending_id, **preview})

            if not decision.get("approved"):
                return ToolMessage(
                    content="Заказ отменён.",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )

            return handler(request)

        except GraphInterrupt:
            # пробрасываем — это не ошибка, а механизм прерывания
            raise
        except Exception as e:
            # закрываем tool_call, чтобы чекпоинт остался валидным
            traceback.print_exc()
            return ToolMessage(
                content=f"Не удалось подготовить заказ: {e}",
                tool_call_id=tool_call_id,
                name=tool_name,
            )


# экземпляр, который уходит в create_agent(middleware=(hitl,))
hitl = HITLManager()