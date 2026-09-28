# modules/tools/retriever.py
from langchain.tools import tool
from typing import Tuple, List
from langchain_core.documents import Document
from ..database.vector_store.vector_store import vector_store  


@tool(response_format="content_and_artifact")
def retriever(query: str) -> Tuple[str, List[Document]]:
    """
    Выполнение векторного поиска.
    Параметр:
        query - искомая строка.
    Результат: кортеж из строки с результатами поиска и
               списка найденных документов.
    """
    docs_list = vector_store.similarity_search(query, k=2)
    docs_string = "\n\n".join(
        f"Источник: {doc.metadata}\nСодержимое: {doc.page_content}"
        for doc in docs_list
    ) + "\n"
    return docs_string, docs_list