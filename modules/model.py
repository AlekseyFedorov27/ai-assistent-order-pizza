import os
from dotenv import load_dotenv
from langchain_gigachat import GigaChat

load_dotenv()

AUTH_KEY = os.environ.get("AUTH_KEY")

model = GigaChat(
    credentials=AUTH_KEY,
    verify_ssl_certs=False,
    model='GigaChat-2',
    timeout=60,
)