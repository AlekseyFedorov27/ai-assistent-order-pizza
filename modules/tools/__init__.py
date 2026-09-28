from .user import (
    get_user_address, 
    get_user_last_orders, 
    get_status_last_order,
    save_user_address
)
from .order import (
    get_pizza_names, 
    verify_address_before_order, 
    get_pizza_price,
    save_order
)
from .retriever import retriever

AGENT_TOOLS = [
    get_pizza_names,
    get_pizza_price,
    verify_address_before_order,
    get_user_address,
    get_user_last_orders,
    get_status_last_order,
    save_user_address,
    save_order,
    retriever
]
